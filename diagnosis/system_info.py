import platform
from datetime import datetime

import psutil

from diagnosis.lhs_client import LHSClient


# ============================================================
# LHS sensor access
# ============================================================
def get_sensor_value(
    sensor_map: dict,
    identifier: str,
):
    """
    LHSセンサー辞書からvalueを取得する。

    LHSのtypeフィールドには依存せず、
    identifierで対象センサーを特定する。
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
# CPU sensor detection
# ============================================================
def get_cpu_usage_sensor(sensor_map: dict):
    """
    CPU使用率センサーを取得する。

    Intel:
        /intelcpu/0/load/0

    AMD:
        /amdcpu/0/load/0

    LHSのtypeフィールドには依存せず、
    identifierを基準に判定する。
    """

    for identifier in sensor_map:
        if not (
            identifier.startswith("/intelcpu/")
            or identifier.startswith("/amdcpu/")
        ):
            continue

        if identifier.endswith("/load/0"):
            return get_sensor_value(
                sensor_map,
                identifier,
            )

    return None


def get_cpu_temperature_sensor(sensor_map: dict):
    """
    CPU温度センサーを取得する。

    Intel:
        /intelcpu/0/temperature/...

    AMD:
        /amdcpu/0/temperature/...

    AMDではTctl/Tdieを優先する。
    """

    # --------------------------------------------------------
    # 1. AMDのTctl/Tdieを優先
    # --------------------------------------------------------
    for identifier, sensor in sensor_map.items():
        if not identifier.startswith("/amdcpu/"):
            continue

        if not identifier.startswith("/amdcpu/0/temperature/"):
            continue

        if not isinstance(sensor, dict):
            continue

        name = str(
            sensor.get("name", "")
        ).lower()

        if "tctl" in name or "tdie" in name:
            return get_sensor_value(
                sensor_map,
                identifier,
            )

    # --------------------------------------------------------
    # 2. Intel / AMDのCPU温度を取得
    #
    # Intelでは /temperature/0 が Core Max
    # AMDではTctl/Tdieが存在しない場合もあるため、
    # temperature配下の最初の有効値を使用する。
    # --------------------------------------------------------
    for identifier in sensor_map:
        if not (
            identifier.startswith("/intelcpu/")
            or identifier.startswith("/amdcpu/")
        ):
            continue

        if "/temperature/" not in identifier:
            continue

        value = get_sensor_value(
            sensor_map,
            identifier,
        )

        if value is not None:
            return value

    return None


# ============================================================
# GPU sensor detection
# ============================================================
def get_gpu_usage_sensor(sensor_map: dict):
    """
    GPU使用率センサーを取得する。

    NVIDIA:
        /gpu-nvidia/0/load/0

    AMD:
        /gpu-amd/0/load/0

    LHSのtypeフィールドには依存せず、
    identifierを基準に判定する。
    """

    for identifier in sensor_map:
        if not (
            identifier.startswith("/gpu-nvidia/")
            or identifier.startswith("/gpu-amd/")
        ):
            continue

        if identifier.endswith("/load/0"):
            return get_sensor_value(
                sensor_map,
                identifier,
            )

    return None


def get_gpu_temperature_sensor(sensor_map: dict):
    """
    GPU温度センサーを取得する。

    NVIDIA:
        /gpu-nvidia/0/temperature/...

    AMD:
        /gpu-amd/0/temperature/...

    GPUによって温度センサーが存在しない場合があるため、
    存在しない場合はNoneを返す。
    """

    for identifier in sensor_map:
        if not (
            identifier.startswith("/gpu-nvidia/")
            or identifier.startswith("/gpu-amd/")
        ):
            continue

        if "/temperature/" not in identifier:
            continue

        value = get_sensor_value(
            sensor_map,
            identifier,
        )

        if value is not None:
            return value

    return None


# ============================================================
# LHS sensor values
# ============================================================
def get_lhs_sensor_values() -> dict:
    """
    LibreHardwareServiceから必要なセンサー値を取得する。

    LibreHardwareServiceはWindowsサービスとして常駐しているため、
    LibreHardwareMonitor.exeを起動したり、
    HTTP/8085へ接続したりしない。

    CPU:
        Intel / AMD

    GPU:
        NVIDIA / AMD

    Memory:
        /ram/load/0
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
            and "identifier" in sensor
        }

        # ----------------------------------------------------
        # CPU
        # ----------------------------------------------------
        result["cpu_usage"] = get_cpu_usage_sensor(
            sensor_map
        )

        result["cpu_temperature"] = get_cpu_temperature_sensor(
            sensor_map
        )

        # ----------------------------------------------------
        # GPU
        # ----------------------------------------------------
        result["gpu_usage"] = get_gpu_usage_sensor(
            sensor_map
        )

        result["gpu_temperature"] = get_gpu_temperature_sensor(
            sensor_map
        )

        # ----------------------------------------------------
        # Memory
        # ----------------------------------------------------
        result["memory_usage"] = get_sensor_value(
            sensor_map,
            "/ram/load/0",
        )

    except Exception as e:
        print(
            f"LibreHardwareServiceからのセンサー取得に失敗しました: {e}"
        )

    return result


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
        # ----------------------------------------------------
        # OS情報
        # ----------------------------------------------------
        "os": platform.system(),
        "os_version": platform.version(),
        "machine": platform.machine(),

        # ----------------------------------------------------
        # CPU情報
        # ----------------------------------------------------
        "cpu": platform.processor(),
        "physical_cores": psutil.cpu_count(
            logical=False
        ),
        "logical_cores": psutil.cpu_count(
            logical=True
        ),
        "cpu_usage": lhs_values["cpu_usage"],

        # ----------------------------------------------------
        # CPU温度
        # ----------------------------------------------------
        "cpu_temperature": lhs_values["cpu_temperature"],

        # ----------------------------------------------------
        # メモリ情報
        # ----------------------------------------------------
        "memory_total": memory.total / (1024 ** 3),
        "memory_used": memory.used / (1024 ** 3),
        "memory_available": memory.available / (1024 ** 3),
        "memory_usage": lhs_values["memory_usage"],

        # ----------------------------------------------------
        # ディスク情報
        # ----------------------------------------------------
        "disk_total": disk.total / (1024 ** 3),
        "disk_used": disk.used / (1024 ** 3),
        "disk_free": disk.free / (1024 ** 3),
        "disk_usage": disk.percent,

        # ----------------------------------------------------
        # GPU情報
        # ----------------------------------------------------
        "gpu_usage": lhs_values["gpu_usage"],
        "gpu_temperature": lhs_values["gpu_temperature"],

        # ----------------------------------------------------
        # システム起動時刻
        # ----------------------------------------------------
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