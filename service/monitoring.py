import json
import logging
import sys
import time
from datetime import datetime
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from diagnosis.config import get_int
from diagnosis.path_utils import DATA_DIR
from diagnosis.system_info import get_monitoring_system_info


# ============================================================
# Paths
# ============================================================

CURRENT_DATA_DIR = DATA_DIR / "data"
CURRENT_JSON = CURRENT_DATA_DIR / "current.json"

MONITORING_LOG_DIR = DATA_DIR / "logs" / "monitoring"
MONITORING_LOG_FILE = MONITORING_LOG_DIR / "monitoring.log"

LOGGER_NAME = "AI_PC_Diagnosis.monitoring"


# ============================================================
# Logger
# ============================================================

def setup_logger():
    """
    監視サービス用ログを初期化する。
    """

    MONITORING_LOG_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    logger = logging.getLogger(LOGGER_NAME)
    logger.setLevel(logging.INFO)
    logger.propagate = False

    if not logger.handlers:
        handler = logging.FileHandler(
            MONITORING_LOG_FILE,
            encoding="utf-8",
        )

        formatter = logging.Formatter(
            "%(asctime)s [%(levelname)s] %(message)s"
        )

        handler.setFormatter(formatter)
        logger.addHandler(handler)

    return logger


# ============================================================
# Monitoring data collection
# ============================================================

def collect_monitoring_data():
    """
    LibreHardwareServiceおよびpsutilから
    監視用システム情報を取得する。
    """

    info = get_monitoring_system_info()

    return {
        "timestamp": datetime.now().isoformat(),

        "cpu": {
            "usage": info["cpu_usage"],
            "temperature": info["cpu_temperature"],
        },

        "memory": {
            "total": info["memory_total"],
            "used": info["memory_used"],
            "available": info["memory_available"],
            "usage": info["memory_usage"],
        },

        "gpu": {
            "usage": info["gpu_usage"],
            "temperature": info["gpu_temperature"],
        },

        "disk": {
            "total": info["disk_total"],
            "used": info["disk_used"],
            "free": info["disk_free"],
            "usage": info["disk_usage"],
        },
    }


# ============================================================
# Sensor readiness
# ============================================================

def is_sensor_data_ready(data):
    """
    起動時診断に必要なセンサー値が取得できているか確認する。

    必須:
        CPU使用率
        CPU温度
        メモリ使用率

    任意:
        GPU使用率
        GPU温度

    GPUを搭載していないPCや、GPUセンサーを取得できない環境でも
    CPU / CPU温度 / メモリが取得できれば診断を開始できる。
    """

    required_values = [
        data["cpu"]["usage"],
        data["cpu"]["temperature"],
        data["memory"]["usage"],
    ]

    return all(
        value is not None
        for value in required_values
    )


# ============================================================
# Current data
# ============================================================

def save_current_data(data):
    """
    current.jsonを安全に保存する。
    """

    CURRENT_DATA_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    temp_file = CURRENT_JSON.with_suffix(".tmp")

    with temp_file.open(
        "w",
        encoding="utf-8",
    ) as file:
        json.dump(
            data,
            file,
            ensure_ascii=False,
            indent=4,
        )

    temp_file.replace(CURRENT_JSON)


def save_monitoring_data(data):
    """
    監視データをcurrent.jsonへ保存する。
    """

    logger = logging.getLogger(LOGGER_NAME)

    save_current_data(data)

    logger.info(
        "監視データを更新しました: %s",
        CURRENT_JSON,
    )

    return data


# ============================================================
# Combined collection
# ============================================================

def collect_and_save():
    """
    システム情報を取得してcurrent.jsonへ保存する。
    """

    data = collect_monitoring_data()

    return save_monitoring_data(data)


# ============================================================
# Continuous monitoring loop
# ============================================================

def run_monitoring_loop():
    """
    単独実行用の監視ループ。

    Windowsサービスからは通常、
    service/windows_service.py の監視ループを使用する。
    """

    logger = setup_logger()

    interval_seconds = get_int(
        "monitoring",
        "interval_seconds",
    )

    logger.info(
        "監視ループを開始しました。interval=%s秒",
        interval_seconds,
    )

    while True:

        try:
            collect_and_save()

        except Exception:
            logger.exception(
                "監視処理でエラーが発生しました。"
            )

        time.sleep(interval_seconds)
