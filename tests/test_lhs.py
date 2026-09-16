import ctypes
import json
import struct
from ctypes import wintypes

import msgpack


# ============================================================
# LibreHardwareService
# ============================================================

SENSORS_MAP_NAME = r"Global\LibreHardwareService/json/sensors/data"
SENSORS_MUTEX_NAME = r"Global\LibreHardwareService/json/sensors/data/MUTEX"

MAP_SIZE = 1024 * 1024

TARGET_SENSORS = {
    "cpu_usage": "/intelcpu/0/load/0",
    "cpu_temperature": "/intelcpu/0/temperature/0",
    "gpu_usage": "/gpu-nvidia/0/load/0",
    "gpu_temperature": "/gpu-nvidia/0/temperature/0",
    "memory_usage": "/ram/load/0",
}


# ============================================================
# Windows API
# ============================================================

kernel32 = ctypes.WinDLL(
    "kernel32",
    use_last_error=True,
)

# ------------------------------------------------------------
# OpenFileMappingW
# ------------------------------------------------------------

FILE_MAP_READ = 0x0004

kernel32.OpenFileMappingW.argtypes = [
    wintypes.DWORD,
    wintypes.BOOL,
    wintypes.LPCWSTR,
]

kernel32.OpenFileMappingW.restype = wintypes.HANDLE

# ------------------------------------------------------------
# MapViewOfFile
# ------------------------------------------------------------

kernel32.MapViewOfFile.argtypes = [
    wintypes.HANDLE,
    wintypes.DWORD,
    wintypes.DWORD,
    wintypes.DWORD,
    ctypes.c_size_t,
]

kernel32.MapViewOfFile.restype = ctypes.c_void_p

# ------------------------------------------------------------
# UnmapViewOfFile
# ------------------------------------------------------------

kernel32.UnmapViewOfFile.argtypes = [
    ctypes.c_void_p,
]

kernel32.UnmapViewOfFile.restype = wintypes.BOOL

# ------------------------------------------------------------
# CloseHandle
# ------------------------------------------------------------

kernel32.CloseHandle.argtypes = [
    wintypes.HANDLE,
]

kernel32.CloseHandle.restype = wintypes.BOOL

# ------------------------------------------------------------
# Mutex
# ------------------------------------------------------------

SYNCHRONIZE = 0x00100000
WAIT_OBJECT_0 = 0x00000000
WAIT_ABANDONED = 0x00000080
WAIT_TIMEOUT = 0x00000102

kernel32.OpenMutexW.argtypes = [
    wintypes.DWORD,
    wintypes.BOOL,
    wintypes.LPCWSTR,
]

kernel32.OpenMutexW.restype = wintypes.HANDLE

kernel32.WaitForSingleObject.argtypes = [
    wintypes.HANDLE,
    wintypes.DWORD,
]

kernel32.WaitForSingleObject.restype = wintypes.DWORD

kernel32.ReleaseMutex.argtypes = [
    wintypes.HANDLE,
]

kernel32.ReleaseMutex.restype = wintypes.BOOL


# ============================================================
# Mutex helper
# ============================================================

class LhsMutex:
    def __init__(self, name):
        self.name = name
        self.handle = None

    def __enter__(self):
        self.handle = kernel32.OpenMutexW(
            SYNCHRONIZE,
            False,
            self.name,
        )

        if not self.handle:
            error = ctypes.get_last_error()

            raise OSError(
                error,
                f"LHS Mutexを開けませんでした: {self.name}",
            )

        result = kernel32.WaitForSingleObject(
            self.handle,
            1000,
        )

        if result == WAIT_TIMEOUT:
            kernel32.CloseHandle(self.handle)
            self.handle = None

            raise TimeoutError(
                "LHS Mutexの取得がタイムアウトしました。"
            )

        if result not in (
            WAIT_OBJECT_0,
            WAIT_ABANDONED,
        ):
            kernel32.CloseHandle(self.handle)
            self.handle = None

            raise RuntimeError(
                f"LHS Mutex取得失敗: 0x{result:08X}"
            )

        return self

    def __exit__(
        self,
        exc_type,
        exc_value,
        traceback,
    ):
        if self.handle:
            kernel32.ReleaseMutex(
                self.handle
            )

            kernel32.CloseHandle(
                self.handle
            )

            self.handle = None


# ============================================================
# LibreHardwareService Memory Map
# ============================================================

class LibreHardwareServiceReader:

    def __init__(self):
        self.mapping_handle = None
        self.mapping_address = None

    # --------------------------------------------------------
    # Open
    # --------------------------------------------------------

    def open(self):
        if self.mapping_address:
            return

        print()
        print("[1] Opening LHS memory map...")
        print(f"    {SENSORS_MAP_NAME}")

        self.mapping_handle = kernel32.OpenFileMappingW(
            FILE_MAP_READ,
            False,
            SENSORS_MAP_NAME,
        )

        if not self.mapping_handle:
            error = ctypes.get_last_error()

            raise OSError(
                error,
                "LHS Sensors memory mapを開けませんでした。",
            )

        print("    OpenFileMappingW: OK")

        self.mapping_address = kernel32.MapViewOfFile(
            self.mapping_handle,
            FILE_MAP_READ,
            0,
            0,
            MAP_SIZE,
        )

        if not self.mapping_address:
            error = ctypes.get_last_error()

            kernel32.CloseHandle(
                self.mapping_handle
            )

            self.mapping_handle = None

            raise OSError(
                error,
                "LHS Sensors memory mapをMapViewOfFileできませんでした。",
            )

        print("    MapViewOfFile: OK")

    # --------------------------------------------------------
    # Close
    # --------------------------------------------------------

    def close(self):
        if self.mapping_address:
            kernel32.UnmapViewOfFile(
                self.mapping_address
            )

            self.mapping_address = None

        if self.mapping_handle:
            kernel32.CloseHandle(
                self.mapping_handle
            )

            self.mapping_handle = None

    # --------------------------------------------------------
    # Context manager
    # --------------------------------------------------------

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
    # Read bytes
    # --------------------------------------------------------

    def read_bytes(self, offset, size):
        if not self.mapping_address:
            raise RuntimeError(
                "Memory mapが開かれていません。"
            )

        return ctypes.string_at(
            self.mapping_address + offset,
            size,
        )

    # --------------------------------------------------------
    # Read int32
    # --------------------------------------------------------

    def read_int32(self, offset):
        data = self.read_bytes(
            offset,
            4,
        )

        return struct.unpack(
            "<i",
            data,
        )[0]

    # --------------------------------------------------------
    # Read int64
    # --------------------------------------------------------

    def read_int64(self, offset):
        data = self.read_bytes(
            offset,
            8,
        )

        return struct.unpack(
            "<q",
            data,
        )[0]

    # --------------------------------------------------------
    # Header
    # --------------------------------------------------------

    def read_header(self):

        metadata_length = self.read_int32(0)

        update_interval = self.read_int32(4)

        last_update = self.read_int64(8)

        header_offset = 4 + metadata_length

        index_length = self.read_int32(
            header_offset
        )

        index_offset = self.read_int32(
            header_offset + 4
        )

        index_format = self.read_int32(
            header_offset + 8
        )

        data_length = self.read_int32(
            header_offset + 12
        )

        data_offset = self.read_int32(
            header_offset + 16
        )

        return {
            "metadata_length": metadata_length,
            "update_interval": update_interval,
            "last_update": last_update,
            "index_length": index_length,
            "index_offset": index_offset,
            "index_format": index_format,
            "data_length": data_length,
            "data_offset": data_offset,
        }

    # --------------------------------------------------------
    # Index
    # --------------------------------------------------------

    def read_index(self, header):

        index_bytes = self.read_bytes(
            header["index_offset"],
            header["index_length"],
        )

        index_format = header["index_format"]

        if index_format == 1:

            return json.loads(
                index_bytes.decode(
                    "utf-8"
                )
            )

        if index_format == 2:

            return msgpack.unpackb(
                index_bytes,
                raw=False,
            )

        raise ValueError(
            f"未対応のIndex Formatです: {index_format}"
        )

    # --------------------------------------------------------
    # Sensor data
    # --------------------------------------------------------

    def read_sensor(
        self,
        entry,
        header,
    ):

        offset = int(entry["offset"])
        size = int(entry["size"])

        absolute_offset = (
            header["data_offset"]
            + offset
        )

        sensor_bytes = self.read_bytes(
            absolute_offset,
            size,
        )

        sensor_json = sensor_bytes.decode(
            "utf-8"
        )

        return json.loads(
            sensor_json
        )

    # --------------------------------------------------------
    # All sensors
    # --------------------------------------------------------

    def read_all(self):

        with LhsMutex(
            SENSORS_MUTEX_NAME
        ):

            header = self.read_header()

            print()
            print("[2] Memory map header")
            print(
                f"    Metadata length : "
                f"{header['metadata_length']}"
            )
            print(
                f"    Update interval : "
                f"{header['update_interval']} ms"
            )
            print(
                f"    Index length    : "
                f"{header['index_length']}"
            )
            print(
                f"    Index offset    : "
                f"{header['index_offset']}"
            )
            print(
                f"    Index format    : "
                f"{header['index_format']}"
            )
            print(
                f"    Data length     : "
                f"{header['data_length']}"
            )
            print(
                f"    Data offset     : "
                f"{header['data_offset']}"
            )

            index = self.read_index(
                header
            )

            print()
            print(
                f"[3] Index entries: "
                f"{len(index)}"
            )

            sensors = {}

            for entry in index:

                if isinstance(
                    entry,
                    list,
                ):

                    entry = {
                        "identifier": entry[0],
                        "offset": entry[1],
                        "size": entry[2],
                        "sensorName": entry[3],
                        "sensorType": entry[4],
                        "hardwareName": entry[5],
                    }

                identifier = entry[
                    "identifier"
                ]

                sensor_data = self.read_sensor(
                    entry,
                    header,
                )

                sensors[identifier] = {
                    "index": entry,
                    "data": sensor_data,
                }

            return header, sensors

    # --------------------------------------------------------
    # Target sensors
    # --------------------------------------------------------

    def read_target_sensors(self):

        header, sensors = self.read_all()

        result = {}

        for key, identifier in TARGET_SENSORS.items():

            sensor = sensors.get(
                identifier
            )

            if sensor is None:

                result[key] = None

                continue

            entry = sensor["index"]
            data = sensor["data"]

            result[key] = {
                "identifier": identifier,
                "name": entry.get(
                    "sensorName"
                ),
                "sensorType": entry.get(
                    "sensorType"
                ),
                "hardwareName": entry.get(
                    "hardwareName"
                ),
                "data": data,
            }

        return header, result


# ============================================================
# Output
# ============================================================

def print_result(
    header,
    sensors,
):

    print()
    print("=" * 60)
    print("LibreHardwareService Python Test")
    print("=" * 60)

    print()
    print("[LHS]")
    print(
        f"  Update interval : "
        f"{header['update_interval']} ms"
    )

    print(
        f"  Index format    : "
        f"{header['index_format']}"
    )

    print()
    print("[Target Sensors]")
    print("-" * 60)

    for key, identifier in TARGET_SENSORS.items():

        sensor = sensors.get(
            key
        )

        print()
        print(key)
        print(
            f"  Identifier : "
            f"{identifier}"
        )

        if sensor is None:

            print(
                "  Status     : NOT FOUND"
            )

            continue

        print(
            f"  Name       : "
            f"{sensor['name']}"
        )

        print(
            f"  Type       : "
            f"{sensor['sensorType']}"
        )

        print(
            f"  Hardware   : "
            f"{sensor['hardwareName']}"
        )

        print(
            f"  Data       : "
            f"{sensor['data']}"
        )


# ============================================================
# Main
# ============================================================

def main():

    print(
        "LibreHardwareService test starting..."
    )

    try:

        with LibreHardwareServiceReader() as reader:

            header, sensors = (
                reader.read_target_sensors()
            )

        print_result(
            header,
            sensors,
        )

        print()
        print("=" * 60)
        print(
            "Test completed successfully."
        )
        print("=" * 60)

    except Exception as exc:

        print()
        print("=" * 60)
        print("ERROR")
        print("=" * 60)
        print(
            type(exc).__name__
        )
        print(
            str(exc)
        )
        print("=" * 60)

        raise


if __name__ == "__main__":
    main()