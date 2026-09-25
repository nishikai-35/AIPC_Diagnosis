import json
import logging
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path

# ============================================================
# パス設定
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parent.parent

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


# ============================================================
# アプリケーション内部
# ============================================================

from diagnosis.config import get_int, load_config
from diagnosis.path_utils import DATA_DIR
from diagnosis.system_info import get_monitoring_system_info
from diagnosis.analyzer import analyze_system
from diagnosis.email_sender import send_diagnosis_email

# 注意 / 警告時に実行する完全診断
from app import run_diagnosis_process


# ============================================================
# ファイル・ディレクトリ
# ============================================================

CURRENT_DATA_DIR = DATA_DIR / "data"
CURRENT_JSON = CURRENT_DATA_DIR / "current.json"

MONITORING_LOG_DIR = DATA_DIR / "logs" / "monitoring"

LOGGER_NAME = "AI_PC_Diagnosis.monitoring"


# ============================================================
# ログファイル
# ============================================================

def get_monitoring_log_file() -> Path:
    """
    当日の監視ログファイルを返す。
    """
    today = datetime.now().strftime("%Y-%m-%d")
    return MONITORING_LOG_DIR / f"monitoring_{today}.log"


def cleanup_old_monitoring_logs(retention_hours: int) -> None:
    """
    保持期間を超えた監視ログを削除する。
    """
    if retention_hours <= 0:
        return

    cutoff = datetime.now() - timedelta(hours=retention_hours)

    if not MONITORING_LOG_DIR.exists():
        return

    for log_file in MONITORING_LOG_DIR.glob("monitoring_*.log"):
        try:
            date_text = log_file.stem.replace("monitoring_", "")
            log_date = datetime.strptime(
                date_text,
                "%Y-%m-%d",
            )

            # 日単位のログなので、その日の終了時刻を基準にする
            log_datetime = log_date + timedelta(days=1)

            if log_datetime <= cutoff:
                log_file.unlink()

        except (ValueError, OSError):
            continue


def setup_logger() -> logging.Logger:
    """
    監視用ロガーを初期化する。
    """
    MONITORING_LOG_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    retention_hours = get_int(
        "retention",
        "json_hours",
    )

    if retention_hours <= 0:
        retention_hours = 120

    cleanup_old_monitoring_logs(
        retention_hours
    )

    logger = logging.getLogger(
        LOGGER_NAME
    )

    logger.setLevel(
        logging.INFO
    )

    # 既存Handlerを解除
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)
        handler.close()

    log_file = get_monitoring_log_file()

    file_handler = logging.FileHandler(
        log_file,
        encoding="utf-8",
    )

    formatter = logging.Formatter(
        "%(asctime)s [%(levelname)s] %(message)s"
    )

    file_handler.setFormatter(
        formatter
    )

    logger.addHandler(
        file_handler
    )

    logger.propagate = False

    return logger


def rotate_monitoring_log_if_needed(
    logger: logging.Logger,
) -> None:
    """
    日付が変わった場合、
    監視ログを翌日のファイルへ切り替える。
    """
    current_log_file = get_monitoring_log_file()

    for handler in logger.handlers:

        if isinstance(
            handler,
            logging.FileHandler,
        ):

            if Path(
                handler.baseFilename
            ) != current_log_file:

                logger.removeHandler(
                    handler
                )

                handler.close()

                new_handler = logging.FileHandler(
                    current_log_file,
                    encoding="utf-8",
                )

                formatter = logging.Formatter(
                    "%(asctime)s [%(levelname)s] %(message)s"
                )

                new_handler.setFormatter(
                    formatter
                )

                logger.addHandler(
                    new_handler
                )

                break


# ============================================================
# 軽量監視データ取得
# ============================================================

def collect_monitoring_data() -> dict:
    """
    LibreHardwareService等から
    軽量な監視データを取得する。

    ここでは以下の完全診断処理は実行しない。

        - SMART
        - Windowsイベントログ
        - CPUプロセス
        - メモリプロセス
    """
    return get_monitoring_system_info()


# ============================================================
# センサー値確認
# ============================================================

def is_sensor_data_ready(
    data: dict,
) -> bool:
    """
    軽量監視に必要なセンサー値が
    取得できているか確認する。
    """

    required_values = (
        data.get("cpu_usage"),
        data.get("cpu_temperature"),
        data.get("memory_usage"),
        data.get("disk_usage"),
    )

    return all(
        value is not None
        for value in required_values
    )


# ============================================================
# current.json保存
# ============================================================

def save_current_data(
    data: dict,
) -> None:
    """
    現在のPC状態をcurrent.jsonへ
    原子的に保存する。
    """

    CURRENT_DATA_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    output = {
        "timestamp": datetime.now().isoformat(),

        "cpu": {
            "usage": data.get(
                "cpu_usage"
            ),
            "temperature": data.get(
                "cpu_temperature"
            ),
        },

        "memory": {
            "total": data.get(
                "memory_total"
            ),
            "used": data.get(
                "memory_used"
            ),
            "available": data.get(
                "memory_available"
            ),
            "usage": data.get(
                "memory_usage"
            ),
        },

        "gpu": {
            "usage": data.get(
                "gpu_usage"
            ),
            "temperature": data.get(
                "gpu_temperature"
            ),
        },

        "disk": {
            "total": data.get(
                "disk_total"
            ),
            "used": data.get(
                "disk_used"
            ),
            "free": data.get(
                "disk_free"
            ),
            "usage": data.get(
                "disk_usage"
            ),
        },
    }

    temp_file = CURRENT_JSON.with_suffix(
        ".tmp"
    )

    with temp_file.open(
        "w",
        encoding="utf-8",
    ) as f:

        json.dump(
            output,
            f,
            ensure_ascii=False,
            indent=4,
        )

    temp_file.replace(
        CURRENT_JSON
    )


# ============================================================
# 軽量診断
# ============================================================

def run_lightweight_analysis(
    data: dict,
    logger: logging.Logger,
):
    """
    軽量監視データを既存analyzer.pyへ渡す。

    注意:
        SMART
        Windowsイベントログ
        CPUプロセス
        メモリプロセス

    はここでは取得しない。
    """

    try:

        results = analyze_system(
            cpu_usage=data.get("cpu_usage"),
            memory_usage=data.get("memory_usage"),
            disk_usage=data.get("disk_usage"),
            cpu_temperature=data.get("cpu_temperature"),
            gpu_usage=data.get("gpu_usage"),
            gpu_temperature=data.get("gpu_temperature"),
        )

        logger.info(
            "軽量診断を実行しました。"
        )

        for result in results:

            logger.info(
                "軽量診断: %s=%s value=%s",
                result.item,
                result.status,
                result.value,
            )

        return results

    except Exception:

        logger.exception(
            "軽量診断(analyzer.py)でエラーが発生しました。"
        )

        return None


def get_lightweight_status(
    results,
) -> str:
    """
    analyzer.pyが返したDiagnosisResult一覧から
    総合ステータスを取得する。

    優先順位:
        警告 > 注意 > 正常
    """

    if not results:
        return "正常"

    if any(
        result.status == "警告"
        for result in results
    ):
        return "警告"

    if any(
        result.status == "注意"
        for result in results
    ):
        return "注意"

    return "正常"


# ============================================================
# 完全診断
# ============================================================

def run_full_diagnosis(
    logger: logging.Logger,
) -> None:
    """
    軽量診断で注意または警告となった場合のみ、
    完全な故障診断を実行する。

    run_diagnosis_process()側で、

        SMART
        Windowsイベントログ
        CPUプロセス
        メモリプロセス
        run_diagnosis()
        OverallDiagnosis
        HTML
        JSON

    を処理する。
    """

    logger.warning(
        "軽量診断で異常を検出しました。"
        "完全故障診断を開始します。"
    )

    try:

        diagnosis_result = run_diagnosis_process(ai_enabled=False)

        logger.info(
            "完全故障診断が完了しました。"
        )
        
        return diagnosis_result

    except Exception:

        logger.exception(
            "完全故障診断でエラーが発生しました。"
        )
        
        return None


# ============================================================
# 監視データ保存
# ============================================================

def save_monitoring_data(
    data: dict,
    logger: logging.Logger,
) -> None:
    """
    軽量監視データをcurrent.jsonへ保存する。
    """

    rotate_monitoring_log_if_needed(
        logger
    )

    save_current_data(
        data
    )

    logger.info(
        "監視データを更新しました。 "
        "CPU=%.2f%%, CPU_TEMP=%s°C, "
        "Memory=%.2f%%, GPU=%s%%, "
        "GPU_TEMP=%s°C, Disk=%.2f%%",

        data.get("cpu_usage") or 0.0,
        data.get("cpu_temperature"),
        data.get("memory_usage") or 0.0,
        data.get("gpu_usage"),
        data.get("gpu_temperature"),
        data.get("disk_usage") or 0.0,
    )


# ============================================================
# 1回分の監視処理
# ============================================================

def collect_and_save(
    logger: logging.Logger,
) -> None:
    """
    1回分の監視処理。

    処理順:

        1. 軽量監視データ取得
        2. current.json保存
        3. analyzer.pyで軽量診断
        4. 正常なら終了
        5. 注意/警告なら完全診断
    """

    # --------------------------------------------------------
    # 1. 軽量監視データ取得
    # --------------------------------------------------------

    data = collect_monitoring_data()

    # --------------------------------------------------------
    # 2. センサー値確認
    # --------------------------------------------------------

    if not is_sensor_data_ready(
        data
    ):

        logger.warning(
            "監視に必要なセンサー値が取得できませんでした。"
            "完全診断は実行せず、次回監視まで待機します。"
        )

        save_current_data(
            data
        )

        return

    # --------------------------------------------------------
    # 3. current.json保存
    # --------------------------------------------------------

    save_monitoring_data(
        data,
        logger,
    )

    # --------------------------------------------------------
    # 4. 軽量診断
    # --------------------------------------------------------

    results = run_lightweight_analysis(
        data,
        logger,
    )
    
    if results is None:
        logger.error(
            "軽量診断に失敗したため、"
            "今回は完全診断を実行せず、次回監視まで待機します。"
        )
        
        return

    status = get_lightweight_status(
        results
    )

    logger.info(
        "軽量診断の総合判定: %s",
        status,
    )

    # --------------------------------------------------------
    # 5. 正常
    # --------------------------------------------------------

    if status == "正常":

        logger.info(
            "異常なし。"
            "完全故障診断は実行しません。"
        )

        return

    # --------------------------------------------------------
    # 6. 注意 / 警告
    # --------------------------------------------------------

    if status in (
        "注意",
        "警告",
    ):

        diagnosis_result = run_full_diagnosis(
            logger
        )

        if diagnosis_result is None:
            logger.error(
                "完全診断の結果を取得できませんでした。"
            )
            return

        (
            info,
            memory_processes,
            cpu_processes,
            diagnosis,
            ai_analysis,
            log_path,
            html_path,
        ) = diagnosis_result

        logger.info(
            "完全診断レポートを取得しました。"
            "JSON=%s HTML=%s",
            log_path,
            html_path,
        )
        
        # --------------------------------------------------------
        # 7. 診断結果メール送信
        # --------------------------------------------------------
        
        try:
            config = load_config()
        
            recipient_email = config.get(
                "mail",
                "recipient_email",
                fallback="",
            ).strip()
        
            pc_name = config.get(
                "user",
                "pc_name",
                fallback="",
            ).strip()
        
            if not recipient_email:
                logger.warning(
                    "メール送信先が設定されていないため、"
                    "診断レポートのメール送信をスキップしました。"
                )
                return
        
            send_diagnosis_email(
                html_path=html_path,
                diagnosis=diagnosis,
                recipient_email=recipient_email,
                pc_name=pc_name,
            )
        
            logger.info(
                "診断レポートのメール送信が完了しました。"
                "宛先=%s HTML=%s",
                recipient_email,
                html_path,
            )
        
        except Exception:
            logger.exception(
                "診断レポートのメール送信に失敗しました。"
            )
        
        return


# ============================================================
# 監視ループ
# ============================================================

def run_monitoring_loop() -> None:
    """
    Windowsサービスから呼び出される監視ループ。

    config.ini:
        [monitoring]
        interval_seconds=300

    デフォルト:
        300秒 = 5分
    """

    logger = setup_logger()

    interval_seconds = get_int(
        "monitoring",
        "interval_seconds",
    )

    if interval_seconds <= 0:
        interval_seconds = 300

    logger.info(
        "監視を開始します。interval=%d秒",
        interval_seconds,
    )

    logger.info(
        "LibreHardwareServiceを使用して"
        "軽量監視を開始します。"
    )

    while True:

        try:

            rotate_monitoring_log_if_needed(
                logger
            )

            # ------------------------------------------------
            # 5分ごとの監視
            # ------------------------------------------------

            collect_and_save(
                logger
            )

        except Exception:

            logger.exception(
                "監視処理で予期しないエラーが発生しました。"
            )

        # ----------------------------------------------------
        # 次回監視まで待機
        # ----------------------------------------------------

        time.sleep(
            interval_seconds
        )
