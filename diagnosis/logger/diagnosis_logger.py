import json
from datetime import datetime, timedelta
from diagnosis.path_utils import LOGS_DIR
from dataclasses import asdict

from diagnosis.config import get_int


LOG_DIR = LOGS_DIR / "diagnosis"

# JSONログの保存期間（時間）
JSON_RETENTION_HOURS = get_int(
    "retention",
    "json_hours"
)


def cleanup_old_logs():
    """
    保存期間を超えた診断ログを削除する。

    config.iniで設定された保存期間を超えたログを削除する。
    """

    if not LOG_DIR.exists():
        return

    cutoff_time = datetime.now() - timedelta(
        hours=JSON_RETENTION_HOURS
    )

    log_files = LOG_DIR.glob(
        "diagnosis_*.json"
    )

    for log_file in log_files:

        try:

            # ファイルの最終更新日時を取得
            file_time = datetime.fromtimestamp(
                log_file.stat().st_mtime
            )

            # 保存期間を超えている場合は削除
            if file_time < cutoff_time:

                log_file.unlink()

                print(
                    f"保存期間を超えたログを削除しました: "
                    f"{log_file}"
                )

        except OSError as e:

            print(
                f"ログ削除に失敗しました: "
                f"{log_file}"
            )

            print(
                f"エラー: {e}"
            )


def save_diagnosis_log(
    results,
    ai_analysis=None,
):
    """
    DiagnosisResultの一覧をJSONログとして保存する。

    正常・注意・警告に関係なく保存する。
    保存期間はconfig.iniで設定する。
    """

    LOG_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    timestamp = datetime.now()

    filename = (
        f"diagnosis_"
        f"{timestamp.strftime('%Y%m%d_%H%M%S')}"
        f".json"
    )

    log_path = LOG_DIR / filename

    data = {
        "timestamp": timestamp.isoformat(),
        "results": [
            asdict(result)
            for result in results
        ],
    }

    if ai_analysis is not None:

        data["ai_analysis"] = {
            "summary": ai_analysis.summary,
            "priority": ai_analysis.priority,
            "causes": ai_analysis.causes,
            "recommendations": (
                ai_analysis.recommendations
            ),
        }

    with open(
        log_path,
        "w",
        encoding="utf-8",
    ) as f:

        json.dump(
            data,
            f,
            ensure_ascii=False,
            indent=2,
        )

    # 保存後に古いログを整理
    cleanup_old_logs()

    return log_path


def has_abnormal_result(results):
    """
    診断結果に「注意」または「警告」が
    含まれているか判定する。
    """

    return any(
        result.status in (
            "注意",
            "警告",
        )
        for result in results
    )


def save_if_abnormal(results):
    """
    注意または警告がある場合のみ
    ログを保存する。
    """

    if not has_abnormal_result(results):
        return None

    return save_diagnosis_log(
        results
    )


def save_periodic_log(results):
    """
    定期診断用のJSONログを保存する。

    正常・注意・警告に関係なく保存する。
    """

    return save_diagnosis_log(
        results
    )
