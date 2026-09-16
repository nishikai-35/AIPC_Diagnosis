import ctypes
import json
import logging
import struct
from typing import Any

import msgpack


LOGGER_NAME = "AI_PC_Diagnosis.monitoring"
logger = logging.getLogger(LOGGER_NAME)


# ============================================================
# Windows API
# ============================================================

kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)

FILE_MAP_READ = 0x0004

WAIT_OBJECT_0 = 0x00000000
WAIT_TIMEOUT = 0x00000102
INFINITE = 0xFFFFFFFF

OpenFileMappingW = kernel32.OpenFileMappingW
OpenFileMappingW.argtypes = [
    ctypes.c_uint32,
    ctypes.c_int,
    ctypes.c_wchar_p,
]
OpenFileMappingW.restype = ctypes.c_void_p

MapViewOfFile = kernel32.MapViewOfFile
MapViewOfFile.argtypes = [
    ctypes.c_void_p,
    ctypes.c_uint32,
    ctypes.c_uint32,
    ctypes.c_uint32,
    ctypes.c_size_t,
]
MapViewOfFile.restype = ctypes.c_void_p

UnmapViewOfFile = kernel32.UnmapViewOfFile
UnmapViewOfFile.argtypes = [
    ctypes.c_void_p,
]
UnmapViewOfFile.restype = ctypes.c_int

CloseHandle = kernel32.CloseHandle
CloseHandle.argtypes = [
    ctypes.c_void_p,
]
CloseHandle.restype = ctypes.c_int

OpenMutexW = kernel32.OpenMutexW
OpenMutexW.argtypes = [
    ctypes.c_uint32,
    ctypes.c_int,
    ctypes.c_wchar_p,
]
OpenMutexW.restype = ctypes.c_void_p

WaitForSingleObject = kernel32.WaitForSingleObject
WaitForSingleObject.argtypes = [
    ctypes.c_void_p,
    ctypes.c_uint32,
]
WaitForSingleObject.restype = ctypes.c_uint32

ReleaseMutex = kernel32.ReleaseMutex
ReleaseMutex.argtypes = [
    ctypes.c_void_p,
]
ReleaseMutex.restype = ctypes.c_int


# MUTEX access rights
SYNCHRONIZE = 0x00100000
MUTEX_MODIFY_STATE = 0x0001

MUTEX_ACCESS = SYNCHRONIZE | MUTEX_MODIFY_STATE


# ============================================================
# LibreHardwareService constants
# ============================================================

SENSORS_MEMORY_MAP = (
    "Global\\LibreHardwareService/json/sensors/data"
)

SENSORS_MUTEX = (
    "Global\\LibreHardwareService/json/sensors/data/MUTEX"
)


# Memory map header
#
# Offset 0:
#   metadata length       int32
#
# Offset 4:
#   update interval       int32
#
# Offset 8:
#   last update           int64
#
# Offset 16:
#   metadata
#
# Header starts at:
#   4 + metadata_length
#
# Header:
#   index length          int32
#   index offset          int32
#   index format          int32
#   data length           int32
#   data offset           int32
#   reserved              16 bytes
#


# ============================================================
# Utility
# ============================================================

def _read_int32(buffer: bytes, offset: int) -> int:
    return struct.unpack_from("<i", buffer, offset)[0]


def _read_int64(buffer: bytes, offset: int) -> int:
    return struct.unpack_from("<q", buffer, offset)[0]


def _read_bytes(
    buffer: bytes,
    offset: int,
    size: int,
) -> bytes:
    return buffer[offset:offset + size]


# ============================================================
# Memory map
# ============================================================

class LHSClient:
    """
    LibreHardwareService shared-memory client.

    LibreHardwareServiceが提供する
    Global\\LibreHardwareService/json/sensors/data
    を読み取り、センサー値を取得する。
    """

    def __init__(
        self,
        memory_map_name: str = SENSORS_MEMORY_MAP,
        mutex_name: str = SENSORS_MUTEX,
    ):
        self.memory_map_name = memory_map_name
        self.mutex_name = mutex_name

        self._mapping_handle = None
        self._view = None
        self._mutex_handle = None

        self.update_interval_ms = None
        self.index_format = None

    # --------------------------------------------------------
    # Open / Close
    # --------------------------------------------------------

    def open(self) -> None:
        """
        LHSの共有メモリとmutexを開く。
        """

        logger.debug(
            "LHS共有メモリを開きます: %s",
            self.memory_map_name,
        )

        mapping_handle = OpenFileMappingW(
            FILE_MAP_READ,
            False,
            self.memory_map_name,
        )

        if not mapping_handle:
            error = ctypes.get_last_error()

            raise RuntimeError(
                "LibreHardwareServiceの共有メモリを開けませんでした。 "
                f"name={self.memory_map_name}, "
                f"WinError={error}"
            )

        self._mapping_handle = mapping_handle

        logger.debug(
            "LHS共有メモリを開きました。"
        )

        view = MapViewOfFile(
            self._mapping_handle,
            FILE_MAP_READ,
            0,
            0,
            0,
        )

        if not view:
            error = ctypes.get_last_error()

            self.close()

            raise RuntimeError(
                "LibreHardwareServiceの共有メモリを"
                "MapViewOfFileできませんでした。 "
                f"WinError={error}"
            )

        self._view = view

        logger.debug(
            "LHS共有メモリをMapViewOfFileしました。"
        )

        mutex_handle = OpenMutexW(
            MUTEX_ACCESS,
            False,
            self.mutex_name,
        )

        if not mutex_handle:
            error = ctypes.get_last_error()

            self.close()

            raise RuntimeError(
                "LibreHardwareServiceのmutexを"
                "開けませんでした。 "
                f"name={self.mutex_name}, "
                f"WinError={error}"
            )

        self._mutex_handle = mutex_handle

        logger.debug(
            "LHS mutexを開きました。"
        )

    def close(self) -> None:
        """
        共有メモリとmutexを閉じる。
        """

        if self._view:
            UnmapViewOfFile(self._view)
            self._view = None

        if self._mapping_handle:
            CloseHandle(self._mapping_handle)
            self._mapping_handle = None

        if self._mutex_handle:
            CloseHandle(self._mutex_handle)
            self._mutex_handle = None

    def __enter__(self):
        self.open()
        return self

    def __exit__(
        self,
        exc_type,
        exc_value,
        traceback,
    ):
        self.close()

    # --------------------------------------------------------
    # Memory map read
    # --------------------------------------------------------

    def _copy_memory_map(
        self,
        size: int = 1024 * 1024,
    ) -> bytes:
        """
        LHS共有メモリから指定サイズをコピーする。

        LHSのデフォルトmemoryMapLimitKbは1024KBなので、
        デフォルトでは1MBを読み取る。
        """

        if not self._view:
            raise RuntimeError(
                "LHS共有メモリが開かれていません。"
            )

        return ctypes.string_at(
            self._view,
            size,
        )

    # --------------------------------------------------------
    # Mutex
    # --------------------------------------------------------

    def _lock(self, timeout_ms: int = 1000) -> bool:
        if not self._mutex_handle:
            raise RuntimeError(
                "LHS mutexが開かれていません。"
            )

        result = WaitForSingleObject(
            self._mutex_handle,
            timeout_ms,
        )

        if result == WAIT_OBJECT_0:
            return True

        if result == WAIT_TIMEOUT:
            logger.warning(
                "LHS mutexの取得がタイムアウトしました。"
            )
            return False

        error = ctypes.get_last_error()

        raise RuntimeError(
            "LHS mutex取得に失敗しました。 "
            f"result={result}, WinError={error}"
        )

    def _unlock(self) -> None:
        if self._mutex_handle:
            ReleaseMutex(self._mutex_handle)

    # --------------------------------------------------------
    # Index
    # --------------------------------------------------------

    def _read_index(
        self,
        buffer: bytes,
    ) -> list[dict[str, Any]]:
        """
        LHSのindexを読み取る。

        indexFormat=2:
            MessagePack

        indexFormat=1:
            JSON
        """

        metadata_length = _read_int32(
            buffer,
            0,
        )

        header_offset = 4 + metadata_length

        index_length = _read_int32(
            buffer,
            header_offset,
        )

        index_offset = _read_int32(
            buffer,
            header_offset + 4,
        )

        index_format = _read_int32(
            buffer,
            header_offset + 8,
        )

        self.update_interval_ms = _read_int32(
            buffer,
            4,
        )

        self.index_format = index_format

        index_data = _read_bytes(
            buffer,
            index_offset,
            index_length,
        )

        if index_format == 2:
            index = msgpack.unpackb(
                index_data,
                raw=False,
            )

        elif index_format == 1:
            index = json.loads(
                index_data.decode("utf-8")
            )

        else:
            raise RuntimeError(
                "未対応のLHS index formatです: "
                f"{index_format}"
            )

        if not isinstance(index, list):
            raise RuntimeError(
                "LHS indexの形式が不正です。"
            )

        return index

    # --------------------------------------------------------
    # Sensor data
    # --------------------------------------------------------

    def _read_sensor_data(
        self,
        buffer: bytes,
        data_offset: int,
        entry: dict[str, Any] | list[Any],
    ) -> dict[str, Any]:
        """
        index entryからセンサーJSONを取得する。
    
        LHSのMessagePack indexは、
        環境によってDataIndexがリスト形式で
        デコードされる場合がある。
    
        DataIndex:
            0: identifier
            1: offset
            2: size
            3: sensorName
            4: sensorType
            5: hardwareName
        """
    
        if isinstance(entry, dict):
            offset = int(entry["offset"])
            size = int(entry["size"])
    
        elif isinstance(entry, (list, tuple)):
            if len(entry) < 3:
                raise RuntimeError(
                    "LHS index entryの要素数が不足しています。 "
                    f"entry={entry}"
                )
    
            offset = int(entry[1])
            size = int(entry[2])
    
        else:
            raise RuntimeError(
                "LHS index entryの形式が不正です。 "
                f"type={type(entry).__name__}, "
                f"entry={entry}"
            )
    
        start = data_offset + offset
        end = start + size
    
        raw_data = buffer[start:end]
    
        if len(raw_data) != size:
            raise RuntimeError(
                "LHSセンサーデータのサイズが不正です。 "
                f"expected={size}, actual={len(raw_data)}"
            )
    
        return json.loads(
            raw_data.decode("utf-8")
        )

    # --------------------------------------------------------
    # All sensors
    # --------------------------------------------------------

    def get_sensors(self) -> list[dict[str, Any]]:
        """
        LHSから全センサー情報を取得する。
        """

        locked = self._lock()

        if not locked:
            raise RuntimeError(
                "LHS mutexを取得できませんでした。"
            )

        try:
            buffer = self._copy_memory_map()

            metadata_length = _read_int32(
                buffer,
                0,
            )

            header_offset = 4 + metadata_length

            index_length = _read_int32(
                buffer,
                header_offset,
            )

            index_offset = _read_int32(
                buffer,
                header_offset + 4,
            )

            data_length = _read_int32(
                buffer,
                header_offset + 12,
            )

            data_offset = _read_int32(
                buffer,
                header_offset + 16,
            )

            # 必要なデータ量が1MBを超える場合に対応
            required_size = data_offset + data_length

            if required_size > len(buffer):
                buffer = self._copy_memory_map(
                    size=required_size
                )

            index = self._read_index(buffer)

            sensors = []

            for entry in index:
                sensor = self._read_sensor_data(
                    buffer,
                    data_offset,
                    entry,
                )

                sensors.append(sensor)

            return sensors

        finally:
            self._unlock()

    # --------------------------------------------------------
    # Specific sensor
    # --------------------------------------------------------

    def get_sensor_by_identifier(
        self,
        identifier: str,
    ) -> dict[str, Any] | None:
        """
        identifierでセンサーを取得する。
        """

        sensors = self.get_sensors()

        for sensor in sensors:
            if sensor.get("identifier") == identifier:
                return sensor

        return None

    def get_sensor_value(
        self,
        identifier: str,
    ) -> float | int | None:
        """
        identifierでセンサー値だけを取得する。
        """

        sensor = self.get_sensor_by_identifier(
            identifier
        )

        if sensor is None:
            return None

        return sensor.get("value")


# ============================================================
# Convenience functions
# ============================================================

def get_lhs_sensor(
    identifier: str,
) -> dict[str, Any] | None:
    """
    LHSから指定identifierのセンサー情報を取得する。
    """

    with LHSClient() as client:
        return client.get_sensor_by_identifier(
            identifier
        )


def get_lhs_sensor_value(
    identifier: str,
) -> float | int | None:
    """
    LHSから指定identifierのセンサー値を取得する。
    """

    with LHSClient() as client:
        return client.get_sensor_value(
            identifier
        )


def get_lhs_monitoring_values() -> dict[str, Any]:
    """
    AI PC Diagnosisで使用する5つのLHSセンサー値を取得する。

    Returns:
        {
            "cpu_usage": ...,
            "cpu_temperature": ...,
            "gpu_usage": ...,
            "gpu_temperature": ...,
            "memory_usage": ...,
        }
    """

    identifiers = {
        "cpu_usage": "/intelcpu/0/load/0",
        "cpu_temperature": "/intelcpu/0/temperature/0",
        "gpu_usage": "/gpu-nvidia/0/load/0",
        "gpu_temperature": "/gpu-nvidia/0/temperature/0",
        "memory_usage": "/ram/load/0",
    }

    with LHSClient() as client:
        values = {}

        for key, identifier in identifiers.items():
            values[key] = client.get_sensor_value(
                identifier
            )

        return values