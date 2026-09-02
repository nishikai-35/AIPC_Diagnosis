import psutil
import time

WINDOWS_PROCESSES = {
    "memcompression",
    "system",
    "registry",
    "explorer.exe",
    "svchost.exe",
    "dwm.exe",
    "lsass.exe",
    "services.exe",
    "winlogon.exe",
    "csrss.exe",
    "smss.exe",
}


VIRTUALIZATION_PROCESSES = {
    "vmmem",
    "vmmemwsl",
    "vmmemwsl.exe",
}


def classify_process(name):
    name_lower = name.lower()

    if name_lower in WINDOWS_PROCESSES:
        return "Windows"

    if name_lower in VIRTUALIZATION_PROCESSES:
        return "WSL/仮想環境"

    return "アプリケーション"


# メモリー監視
def get_top_memory_processes(limit=10):
    processes = []

    for process in psutil.process_iter(
        ["pid", "name", "memory_info"]
    ):
        try:
            info = process.info
            memory_info = info["memory_info"]

            if memory_info is None:
                continue

            memory_mb = memory_info.rss / (1024 ** 2)

            name = info["name"] or "Unknown"

            processes.append(
                {
                    "pid": info["pid"],
                    "name": name,
                    "memory_mb": memory_mb,
                    "category": classify_process(name),
                }
            )

        except (
            psutil.NoSuchProcess,
            psutil.AccessDenied,
            psutil.ZombieProcess,
        ):
            continue

    processes.sort(
        key=lambda process: process["memory_mb"],
        reverse=True,
    )

    return processes[:limit]


# CPUプロセス監視
def get_top_cpu_processes(limit=10):
    processes = []

    # CPU使用率の測定開始
    for process in psutil.process_iter(["pid", "name"]):
        try:
            process.cpu_percent(None)
        except (
            psutil.NoSuchProcess,
            psutil.AccessDenied,
            psutil.ZombieProcess,
        ):
            continue

    # 1秒間測定
    time.sleep(1)

    # CPU使用率取得
    for process in psutil.process_iter(["pid", "name"]):
        try:
            cpu_percent = process.cpu_percent(None)
            name = process.info["name"] or "Unknown"

            # System Idle ProcessはCPU負荷の診断対象から除外
            if name.lower() == "system idle process":
                continue

            processes.append(
                {
                    "pid": process.info["pid"],
                    "name": name,
                    "cpu_percent": cpu_percent,
                    "category": classify_process(name),
                }
            )

        except (
            psutil.NoSuchProcess,
            psutil.AccessDenied,
            psutil.ZombieProcess,
        ):
            continue

    processes.sort(
        key=lambda process: process["cpu_percent"],
        reverse=True,
    )

    return processes[:limit]