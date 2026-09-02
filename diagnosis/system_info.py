import json
import platform
from datetime import datetime
from urllib.request import urlopen

import psutil


LIBRE_HARDWARE_MONITOR_URL = "http://127.0.0.1:8085/data.json"


def get_cpu_usage() -> float:
    """
    CPU使用率を取得する
    """
    return psutil.cpu_percent(interval=1)


def get_memory_usage() -> float:
    """
    メモリ使用率を取得する
    """
    memory = psutil.virtual_memory()
    return memory.percent


def get_disk_usage() -> float:
    """
    Cドライブのディスク使用率を取得する
    """
    disk = psutil.disk_usage("C:\\")
    return disk.percent


def get_hardware_data():
    """
    LibreHardwareMonitorからハードウェア情報を取得する
    """

    # LibreHardwareMonitorを自動起動
    from diagnosis.hardware_monitor import start_libre_hardware_monitor

    ready = start_libre_hardware_monitor()

    if not ready:
        print(
            "LibreHardwareMonitorの準備が完了していないため、"
            "ハードウェア情報を取得できません。"
        )
        return None

    try:
        with urlopen(
            LIBRE_HARDWARE_MONITOR_URL,
            timeout=5,
        ) as response:

            return json.load(response)

    except Exception as e:

        print(
            f"LibreHardwareMonitorへの接続に失敗しました: {e}"
        )

        return None




def find_sensor(node, sensor_text: str, sensor_type: str):
    """
    LibreHardwareMonitorのデータから指定したセンサーを探す
    """

    if not isinstance(node, dict):
        return None

    if (
        node.get("Text") == sensor_text
        and node.get("Type") == sensor_type
    ):
        return node.get("Value")

    for child in node.get("Children", []):
        result = find_sensor(child, sensor_text, sensor_type)

        if result is not None:
            return result

    return None


def parse_sensor_value(value):
    """
    LibreHardwareMonitorの値から数値だけを取り出す
    """

    if value is None:
        return None

    try:
        return float(
            value.replace("°C", "")
            .replace("%", "")
            .replace("MHz", "")
            .strip()
        )

    except (ValueError, AttributeError):
        return None


def get_cpu_temperature(hardware_data) -> float | None:
    """
    CPU最高温度を取得する
    """

    value = find_sensor(
        hardware_data,
        "Core Max",
        "Temperature",
    )

    return parse_sensor_value(value)


def get_gpu_temperature(hardware_data) -> float | None:
    """
    GPU温度を取得する
    """

    value = find_sensor(
        hardware_data,
        "GPU Core",
        "Temperature",
    )

    return parse_sensor_value(value)


def get_gpu_usage(hardware_data) -> float | None:
    """
    GPU使用率を取得する
    """

    value = find_sensor(
        hardware_data,
        "GPU Core",
        "Load",
    )

    return parse_sensor_value(value)


def get_system_info() -> dict:
    """
    PCのシステム情報をまとめて取得する
    """

    # LibreHardwareMonitorからハードウェア情報を取得
    hardware_data = get_hardware_data()

    # psutilから基本システム情報を取得
    memory = psutil.virtual_memory()
    disk = psutil.disk_usage("C:\\")

    return {
        # OS情報
        "os": platform.system(),
        "os_version": platform.version(),
        "machine": platform.machine(),

        # CPU情報
        "cpu": platform.processor(),
        "physical_cores": psutil.cpu_count(logical=False),
        "logical_cores": psutil.cpu_count(logical=True),
        "cpu_usage": get_cpu_usage(),

        # CPU温度
        "cpu_temperature": get_cpu_temperature(hardware_data),

        # メモリ情報
        "memory_total": memory.total / (1024 ** 3),
        "memory_used": memory.used / (1024 ** 3),
        "memory_available": memory.available / (1024 ** 3),
        "memory_usage": memory.percent,

        # ディスク情報
        "disk_total": disk.total / (1024 ** 3),
        "disk_used": disk.used / (1024 ** 3),
        "disk_free": disk.free / (1024 ** 3),
        "disk_usage": disk.percent,

        # GPU情報
        "gpu_usage": get_gpu_usage(hardware_data),
        "gpu_temperature": get_gpu_temperature(hardware_data),

        # システム起動時刻
        "boot_time": datetime.fromtimestamp(psutil.boot_time()),
    }


# テスト確認
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
    print(f"Physical Cores  : {info['physical_cores']}")
    print(f"Logical Cores   : {info['logical_cores']}")
    print(f"CPU Usage       : {info['cpu_usage']:.1f} %")

    if info["cpu_temperature"] is not None:
        print(f"CPU Temperature : {info['cpu_temperature']:.1f} °C")
    else:
        print("CPU Temperature : 取得できません")

    print("\n[Memory]")
    print(f"Total           : {info['memory_total']:.2f} GB")
    print(f"Used            : {info['memory_used']:.2f} GB")
    print(f"Available       : {info['memory_available']:.2f} GB")
    print(f"Usage           : {info['memory_usage']:.1f} %")

    print("\n[Disk C:]")
    print(f"Total           : {info['disk_total']:.2f} GB")
    print(f"Used            : {info['disk_used']:.2f} GB")
    print(f"Free            : {info['disk_free']:.2f} GB")
    print(f"Usage           : {info['disk_usage']:.1f} %")

    print("\n[GPU]")
    if info["gpu_usage"] is not None:
        print(f"GPU Usage       : {info['gpu_usage']:.1f} %")
    else:
        print("GPU Usage       : 取得できません")

    if info["gpu_temperature"] is not None:
        print(f"GPU Temperature : {info['gpu_temperature']:.1f} °C")
    else:
        print("GPU Temperature : 取得できません")

    print("\n[System]")
    print(f"Boot Time       : {info['boot_time']}")

    print("\n" + "=" * 60)