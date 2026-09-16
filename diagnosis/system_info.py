import platform
from datetime import datetime

import psutil

from diagnosis.lhs_client import LHSClient


# ============================================================
# LibreHardwareService sensor identifiers
# ============================================================

CPU_USAGE_SENSOR = "/intelcpu/0/load/0"
CPU_TEMPERATURE_SENSOR = "/intelcpu/0/temperature/0"

GPU_USAGE_SENSOR = "/gpu-nvidia/0/load/0"
GPU_TEMPERATURE_SENSOR = "/gpu-nvidia/0/temperature/0"

MEMORY_USAGE_SENSOR = "/ram/load/0"


# ============================================================
# LHS sensor access
# ============================================================

def get_lhs_sensor_values() -> dict:
    """
    LibreHardwareServiceから必要なセンサー値を取得する。

    LibreHardwareServiceはWindowsサービスとして常駐しているため、
    LibreHardwareMonitor.exeを起動したり、
    HTTP/8085へ接続したりしない。
    """

    result = {
        "cpu_usage": None,
        "cpu_temperature": None,
        "gpu_usage": None,
        "gpu_temperature": None,
        "memory_usage": None,
    }

    try:
        with LHSClient() as client:
            sensors = client.get_sensors()

        sensor_map = {
            sensor["identifier"]: sensor
            for sensor in sensors
            if isinstance(sensor, dict)
        }

        result["cpu_usage"] = get_sensor_value(
            sensor_map,
            CPU_USAGE_SENSOR,
        )

        result["cpu_temperature"] = get_sensor_value(
            sensor_map,
            CPU_TEMPERATURE_SENSOR,
        )

        result["gpu_usage"] = get_sensor_value(
            sensor_map,
            GPU_USAGE_SENSOR,
        )

        result["gpu_temperature"] = get_sensor_value(
            sensor_map,
            GPU_TEMPERATURE_SENSOR,
        )

        result["memory_usage"] = get_sensor_value(
            sensor_map,
            MEMORY_USAGE_SENSOR,
        )

    except Exception as e:
        print(
            f"LibreHardwareServiceからのセンサー取得に失敗しました: {e}"
        )

    return result


def get_sensor_value(
    sensor_map: dict,
    identifier: str,
):
    """
    LHSセンサー辞書からvalueを取得する。
    """

    sensor = sensor_map.get(identifier)

    if sensor is None:
        return None

    value = sensor.get("value")

    if value is None:
        return None

    try:
        return float(value)
    except (TypeError, ValueError):
        return None


# ============================================================
# Basic system information
# ============================================================

def get_cpu_usage() -> float | None:
    """
    CPU使用率を取得する。

    LibreHardwareServiceのCPUセンサーを使用する。
    """

    values = get_lhs_sensor_values()

    return values["cpu_usage"]


def get_memory_usage() -> float | None:
    """
    メモリ使用率を取得する。

    LibreHardwareServiceのメモリセンサーを使用する。
    """

    values = get_lhs_sensor_values()

    return values["memory_usage"]


def get_disk_usage() -> float:
    """
    Cドライブのディスク使用率を取得する。
    """

    disk = psutil.disk_usage("C:\\")

    return disk.percent


# ============================================================
# Monitoring information
# ============================================================

def get_monitoring_system_info() -> dict:
    """
    Windows Serviceによる継続監視用のシステム情報を取得する。

    CPU/GPU/メモリ:
        LibreHardwareService

    ディスク:
        psutil

    LibreHardwareMonitor.exeは起動しない。
    HTTP/8085も使用しない。
    """

    lhs_values = get_lhs_sensor_values()

    memory = psutil.virtual_memory()
    disk = psutil.disk_usage("C:\\")

    return {
        "cpu_usage": lhs_values["cpu_usage"],
        "cpu_temperature": lhs_values["cpu_temperature"],

        "memory_total": memory.total / (1024 ** 3),
        "memory_used": memory.used / (1024 ** 3),
        "memory_available": memory.available / (1024 ** 3),
        "memory_usage": lhs_values["memory_usage"],

        "disk_total": disk.total / (1024 ** 3),
        "disk_used": disk.used / (1024 ** 3),
        "disk_free": disk.free / (1024 ** 3),
        "disk_usage": disk.percent,

        "gpu_usage": lhs_values["gpu_usage"],
        "gpu_temperature": lhs_values["gpu_temperature"],
    }


# ============================================================
# Full system information
# ============================================================

def get_system_info() -> dict:
    """
    PCのシステム情報をまとめて取得する。

    v1.0.6ではLibreHardwareMonitorを起動しない。

    CPU/GPU/メモリのセンサー情報は
    LibreHardwareServiceから取得する。
    """

    lhs_values = get_lhs_sensor_values()

    memory = psutil.virtual_memory()
    disk = psutil.disk_usage("C:\\")

    return {
        # OS情報
        "os": platform.system(),
        "os_version": platform.version(),
        "machine": platform.machine(),

        # CPU情報
        "cpu": platform.processor(),
        "physical_cores": psutil.cpu_count(
            logical=False
        ),
        "logical_cores": psutil.cpu_count(
            logical=True
        ),
        "cpu_usage": lhs_values["cpu_usage"],

        # CPU温度
        "cpu_temperature": lhs_values["cpu_temperature"],

        # メモリ情報
        "memory_total": memory.total / (1024 ** 3),
        "memory_used": memory.used / (1024 ** 3),
        "memory_available": memory.available / (1024 ** 3),
        "memory_usage": lhs_values["memory_usage"],

        # ディスク情報
        "disk_total": disk.total / (1024 ** 3),
        "disk_used": disk.used / (1024 ** 3),
        "disk_free": disk.free / (1024 ** 3),
        "disk_usage": disk.percent,

        # GPU情報
        "gpu_usage": lhs_values["gpu_usage"],
        "gpu_temperature": lhs_values["gpu_temperature"],

        # システム起動時刻
        "boot_time": datetime.fromtimestamp(
            psutil.boot_time()
        ),
    }


# ============================================================
# Direct execution test
# ============================================================

if __name__ == "__main__":

    info = get_system_info()

    print("=" * 60)
    print("                 システム情報")
    print("=" * 60)

    print("\n[OS]")
    print(f"OS              : {info['os']}")
    print(f"OS Version      : {info['os_version']}")
    print(f"Machine         : {info['machine']}")

    print("\n[CPU]")
    print(f"CPU             : {info['cpu']}")
    print(
        f"Physical Cores  : "
        f"{info['physical_cores']}"
    )
    print(
        f"Logical Cores   : "
        f"{info['logical_cores']}"
    )

    if info["cpu_usage"] is not None:
        print(
            f"CPU Usage       : "
            f"{info['cpu_usage']:.1f} %"
        )
    else:
        print("CPU Usage       : 取得できません")

    if info["cpu_temperature"] is not None:
        print(
            f"CPU Temperature : "
            f"{info['cpu_temperature']:.1f} °C"
        )
    else:
        print("CPU Temperature : 取得できません")

    print("\n[Memory]")
    print(
        f"Total           : "
        f"{info['memory_total']:.2f} GB"
    )
    print(
        f"Used            : "
        f"{info['memory_used']:.2f} GB"
    )
    print(
        f"Available       : "
        f"{info['memory_available']:.2f} GB"
    )

    if info["memory_usage"] is not None:
        print(
            f"Usage           : "
            f"{info['memory_usage']:.1f} %"
        )
    else:
        print("Usage           : 取得できません")

    print("\n[Disk C:]")
    print(
        f"Total           : "
        f"{info['disk_total']:.2f} GB"
    )
    print(
        f"Used            : "
        f"{info['disk_used']:.2f} GB"
    )
    print(
        f"Free            : "
        f"{info['disk_free']:.2f} GB"
    )
    print(
        f"Usage           : "
        f"{info['disk_usage']:.1f} %"
    )

    print("\n[GPU]")

    if info["gpu_usage"] is not None:
        print(
            f"GPU Usage       : "
            f"{info['gpu_usage']:.1f} %"
        )
    else:
        print("GPU Usage       : 取得できません")

    if info["gpu_temperature"] is not None:
        print(
            f"GPU Temperature : "
            f"{info['gpu_temperature']:.1f} °C"
        )
    else:
        print("GPU Temperature : 取得できません")

    print("\n[System]")
    print(f"Boot Time       : {info['boot_time']}")

    print("\n" + "=" * 60)
