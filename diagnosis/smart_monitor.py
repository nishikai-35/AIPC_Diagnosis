import re
import subprocess

from diagnosis.path_utils import SMARTCTL_EXE


SMARTCTL_PATH = SMARTCTL_EXE
NVME_DEVICE = "/dev/sda"


def run_smartctl():
    """
    smartctlからNVMe SMART情報を取得する
    """

    command = [
        SMARTCTL_PATH,
        "-a",
        NVME_DEVICE,
        "-d",
        "nvme",
    ]

    try:
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=15,
        )

    except FileNotFoundError:
        print("smartctlが見つかりません。")
        return None

    except subprocess.SubprocessError as e:
        print(f"smartctlの実行に失敗しました: {e}")
        return None

    # smartctlは警告・異常状態の場合でも
    # 終了コードが0以外になる場合があるため、
    # stdoutを優先して確認する。
    output = result.stdout

    if not output:
        print("smartctlから情報を取得できませんでした。")

        if result.stderr:
            print(result.stderr.strip())

        return None

    return output


def extract_value(text, label):
    """
    smartctlの出力から指定項目の値を取得する
    """

    pattern = rf"^{re.escape(label)}:\s*(.+)$"

    match = re.search(
        pattern,
        text,
        re.MULTILINE,
    )

    if match:
        return match.group(1).strip()

    return None


def extract_number(text, label):
    """
    smartctlの出力から数値を取得する

    例:
        Temperature: 36 Celsius
        Percentage Used: 1%
        Power Cycles: 1,380
        Power On Hours: 2,153
    """

    value = extract_value(text, label)

    if value is None:
        return None

    # 1,380 → 1380
    value = value.replace(",", "")

    match = re.search(r"[-+]?\d+(?:\.\d+)?", value)

    if not match:
        return None

    try:
        return float(match.group(0))

    except ValueError:
        return None


def get_smart_info():
    """
    NVMe SMART情報を取得して辞書形式で返す
    """

    output = run_smartctl()

    if output is None:
        return None

    smart_info = {
        "model": extract_value(
            output,
            "Model Number",
        ),

        "serial_number": extract_value(
            output,
            "Serial Number",
        ),

        "firmware_version": extract_value(
            output,
            "Firmware Version",
        ),

        "nvme_version": extract_value(
            output,
            "NVMe Version",
        ),

        "health": extract_value(
            output,
            "SMART overall-health self-assessment test result",
        ),

        "critical_warning": extract_value(
            output,
            "Critical Warning",
        ),

        "temperature": extract_number(
            output,
            "Temperature",
        ),

        "available_spare": extract_number(
            output,
            "Available Spare",
        ),

        "available_spare_threshold": extract_number(
            output,
            "Available Spare Threshold",
        ),

        "percentage_used": extract_number(
            output,
            "Percentage Used",
        ),

        "power_cycles": extract_number(
            output,
            "Power Cycles",
        ),

        "power_on_hours": extract_number(
            output,
            "Power On Hours",
        ),

        "unsafe_shutdowns": extract_number(
            output,
            "Unsafe Shutdowns",
        ),

        "media_errors": extract_number(
            output,
            "Media and Data Integrity Errors",
        ),

        "error_log_entries": extract_number(
            output,
            "Error Information Log Entries",
        ),

        "warning_temperature_time": extract_number(
            output,
            "Warning  Comp. Temperature Time",
        ),

        "critical_temperature_time": extract_number(
            output,
            "Critical Comp. Temperature Time",
        ),
    }

    return smart_info


def print_smart_info(info):
    """
    SMART情報を表示する
    """

    print("\n" + "=" * 60)
    print("              NVMe SMART情報")
    print("=" * 60)

    if info is None:
        print("SMART情報を取得できませんでした。")
        return

    print(f"\nModel             : {info['model']}")
    print(f"Serial Number     : {info['serial_number']}")
    print(f"Firmware          : {info['firmware_version']}")
    print(f"NVMe Version      : {info['nvme_version']}")

    print("\n[Health]")
    print(f"Health            : {info['health']}")
    print(f"Critical Warning  : {info['critical_warning']}")

    print("\n[SMART / Health]")
    print(f"Temperature       : {info['temperature']:.0f} °C")
    print(f"Available Spare   : {info['available_spare']:.0f} %")
    print(f"Percentage Used    : {info['percentage_used']:.0f} %")
    print(f"Power Cycles      : {info['power_cycles']:.0f}")
    print(f"Power On Hours    : {info['power_on_hours']:.0f} h")
    print(f"Unsafe Shutdowns  : {info['unsafe_shutdowns']:.0f}")
    print(f"Media Errors      : {info['media_errors']:.0f}")
    print(f"Error Log Entries : {info['error_log_entries']:.0f}")

    print("\n" + "=" * 60)


if __name__ == "__main__":
    smart_info = get_smart_info()

    print_smart_info(smart_info)