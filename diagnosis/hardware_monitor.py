import socket
import subprocess
import time

import psutil

from diagnosis.path_utils import LHM_EXE


LHM_HOST = "127.0.0.1"
LHM_PORT = 8085


def is_libre_hardware_monitor_running():
    """
    LibreHardwareMonitorが起動しているか確認する。
    """

    try:
        for process in psutil.process_iter(["name"]):
            name = process.info.get("name")

            if name and name.lower() == "librehardwaremonitor.exe":
                return True

    except Exception as e:
        print(
            f"LibreHardwareMonitorの起動確認に失敗しました: {e}"
        )

    return False


def is_libre_hardware_monitor_ready():
    """
    LibreHardwareMonitorのWeb Serverが
    8085番ポートで接続可能か確認する。
    """

    try:
        with socket.create_connection(
            (LHM_HOST, LHM_PORT),
            timeout=1,
        ):
            return True

    except OSError:
        return False


def wait_for_libre_hardware_monitor(
    timeout=15,
    interval=0.5,
):
    """
    LibreHardwareMonitorのWeb Serverが
    利用可能になるまで待機する。

    timeout:
        最大待機時間（秒）

    interval:
        確認間隔（秒）
    """

    print(
        "LibreHardwareMonitorの起動完了を待っています..."
    )

    start_time = time.time()

    while time.time() - start_time < timeout:

        if is_libre_hardware_monitor_ready():
            print(
                "LibreHardwareMonitorの接続準備が完了しました。"
            )
            return True

        time.sleep(interval)

    print(
        "LibreHardwareMonitorの起動完了を確認できませんでした。"
    )

    return False


def start_libre_hardware_monitor():
    """
    LibreHardwareMonitorを管理者権限で起動する。

    すでに起動している場合でも、
    Web Serverが利用可能になるまで確認する。
    """

    # --------------------------------------------------
    # すでに起動している場合
    # --------------------------------------------------

    if is_libre_hardware_monitor_running():

        print(
            "LibreHardwareMonitorはすでに起動しています。"
        )

        # プロセスは存在するがWeb Serverが
        # 起動途中の可能性があるため待機する
        return wait_for_libre_hardware_monitor()

    # --------------------------------------------------
    # EXE存在確認
    # --------------------------------------------------

    if not LHM_EXE.exists():

        print(
            "LibreHardwareMonitor.exeが見つかりません: "
            f"{LHM_EXE}"
        )

        return False

    # --------------------------------------------------
    # LibreHardwareMonitor起動
    # --------------------------------------------------

    try:

        print(
            "LibreHardwareMonitorを管理者権限で起動しています..."
        )

        # WindowsのUACを使用して管理者権限で起動
        subprocess.Popen(
            [
                "powershell",
                "-Command",
                (
                    f'Start-Process '
                    f'-FilePath "{LHM_EXE}" '
                    f'-WorkingDirectory "{LHM_EXE.parent}" '
                    f'-Verb RunAs'
                ),
            ],
            creationflags=subprocess.CREATE_NO_WINDOW,
        )

        print(
            "LibreHardwareMonitorの起動処理を開始しました。"
        )

        # --------------------------------------------------
        # プロセス起動待機
        # --------------------------------------------------

        process_timeout = 10
        start_time = time.time()

        while (
            time.time() - start_time < process_timeout
        ):

            if is_libre_hardware_monitor_running():
                print(
                    "LibreHardwareMonitorのプロセス起動を確認しました。"
                )
                break

            time.sleep(0.5)

        else:

            print(
                "LibreHardwareMonitorのプロセス起動を確認できませんでした。"
            )

            return False

        # --------------------------------------------------
        # Web Server起動待機
        # --------------------------------------------------

        return wait_for_libre_hardware_monitor()

    except Exception as e:

        print(
            f"LibreHardwareMonitorの起動に失敗しました: {e}"
        )

        return False