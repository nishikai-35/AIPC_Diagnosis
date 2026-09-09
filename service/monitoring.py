import json
import logging
import sys
import time
from datetime import datetime
from pathlib import Path


# プロジェクトルートをPythonのモジュール検索パスへ追加
PROJECT_ROOT = Path(__file__).resolve().parent.parent

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


from diagnosis.system_info import get_monitoring_system_info
from diagnosis.path_utils import DATA_DIR
from diagnosis.config import get_int


CURRENT_DATA_DIR = DATA_DIR / "data"
CURRENT_JSON = CURRENT_DATA_DIR / "current.json"
MONITORING_LOG_DIR = DATA_DIR / "logs" / "monitoring"
MONITORING_LOG_FILE = MONITORING_LOG_DIR / "monitoring.log"


def setup_logger() -> logging.Logger:
    """
    監視用ログを設定する。
    """

    MONITORING_LOG_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    logger = logging.getLogger("ai_pc_diagnosis_monitoring")

    logger.setLevel(logging.INFO)

    if not logger.handlers:

        file_handler = logging.FileHandler(
            MONITORING_LOG_FILE,
            encoding="utf-8",
        )

        formatter = logging.Formatter(
            "%(asctime)s [%(levelname)s] %(message)s"
        )

        file_handler.setFormatter(formatter)

        logger.addHandler(file_handler)

    return logger


def collect_monitoring_data() -> dict:
    """
    現在のPC状態を取得する。

    監視専用のget_monitoring_system_info()を利用して、
    CPU / Memory / GPU / Diskの情報を取得する。
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


def save_current_data(data: dict) -> None:
    """
    最新の監視データをcurrent.jsonへ保存する。
    """

    CURRENT_DATA_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    with CURRENT_JSON.open(
        "w",
        encoding="utf-8",
    ) as file:

        json.dump(
            data,
            file,
            ensure_ascii=False,
            indent=4,
        )


def collect_and_save() -> dict:
    """
    PC状態を取得してcurrent.jsonへ保存する。
    """

    data = collect_monitoring_data()

    save_current_data(data)

    return data


def run_monitoring_loop() -> None:
    """
    設定された監視間隔でPC状態を継続監視する。
    """

    logger = setup_logger()

    interval_seconds = get_int(
        "monitoring",
        "interval_seconds",
    )

    logger.info("監視を開始しました。")
    logger.info(
        f"監視間隔: {interval_seconds}秒"
    )

    print()
    print("監視を開始します。")
    print(f"監視間隔: {interval_seconds}秒")
    print()

    while True:

        try:

            data = collect_and_save()

            message = (
                f"監視データを保存しました。"
                f" timestamp={data['timestamp']}"
            )

            logger.info(message)

            print(
                f"[{data['timestamp']}] "
                f"監視データを保存しました。"
            )

        except Exception as e:

            logger.exception(
                "監視データの取得・保存に失敗しました。"
            )

            print(
                f"[{datetime.now().isoformat()}] "
                f"監視データの取得に失敗しました: {e}"
            )

        time.sleep(interval_seconds)


if __name__ == "__main__":

    print("=" * 60)
    print("       AI PC Diagnosis Monitoring")
    print("=" * 60)

    try:

        run_monitoring_loop()

    except KeyboardInterrupt:

        logger = setup_logger()
        logger.info("監視を終了しました。")

        print()
        print("監視を終了しました。")

    except Exception as e:

        print()
        print("監視でエラーが発生しました。")
        print(f"エラー: {e}")

    print()
    print("=" * 60)