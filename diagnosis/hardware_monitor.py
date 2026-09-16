import logging
from typing import Any

from diagnosis.lhs_client import (
    LHSClient,
    get_lhs_monitoring_values,
)


LOGGER_NAME = "AI_PC_Diagnosis.monitoring"
logger = logging.getLogger(LOGGER_NAME)


# ============================================================
# LibreHardwareService
# ============================================================

def is_libre_hardware_service_ready() -> bool:
    """
    LibreHardwareServiceの共有メモリが利用可能か確認する。

    LibreHardwareServiceはWindowsサービスとして常駐するため、
    LibreHardwareMonitor.exeを起動したり、
    HTTP/8085へ接続したりしない。
    """

    try:
        with LHSClient() as client:
            client.get_sensors()

        logger.debug(
            "LibreHardwareServiceの共有メモリが利用可能です。"
        )

        return True

    except Exception as e:
        logger.debug(
            "LibreHardwareServiceの共有メモリを利用できません: %s",
            e,
        )

        return False


def get_hardware_monitor_values() -> dict[str, Any]:
    """
    LibreHardwareServiceから監視用センサー値を取得する。

    Returns:
        {
            "cpu_usage": ...,
            "cpu_temperature": ...,
            "gpu_usage": ...,
            "gpu_temperature": ...,
            "memory_usage": ...,
        }

    センサーを取得できない場合は各値がNoneになる。
    """

    result = {
        "cpu_usage": None,
        "cpu_temperature": None,
        "gpu_usage": None,
        "gpu_temperature": None,
        "memory_usage": None,
    }

    try:
        values = get_lhs_monitoring_values()

        result.update(
            {
                "cpu_usage": _to_float(
                    values.get("cpu_usage")
                ),
                "cpu_temperature": _to_float(
                    values.get("cpu_temperature")
                ),
                "gpu_usage": _to_float(
                    values.get("gpu_usage")
                ),
                "gpu_temperature": _to_float(
                    values.get("gpu_temperature")
                ),
                "memory_usage": _to_float(
                    values.get("memory_usage")
                ),
            }
        )

        logger.debug(
            "LibreHardwareServiceからセンサー値を取得しました。 "
            "CPU=%s%% CPU温度=%s℃ GPU=%s%% GPU温度=%s℃ Memory=%s%%",
            result["cpu_usage"],
            result["cpu_temperature"],
            result["gpu_usage"],
            result["gpu_temperature"],
            result["memory_usage"],
        )

    except Exception:
        logger.exception(
            "LibreHardwareServiceからのセンサー取得に失敗しました。"
        )

    return result


def get_hardware_sensor_value(
    identifier: str,
) -> float | None:
    """
    LibreHardwareServiceから指定identifierの
    センサー値を取得する。
    """

    try:
        with LHSClient() as client:
            value = client.get_sensor_value(identifier)

        return _to_float(value)

    except Exception:
        logger.exception(
            "LHSセンサー値の取得に失敗しました。 "
            "identifier=%s",
            identifier,
        )

        return None


def _to_float(value: Any) -> float | None:
    """
    センサー値をfloatへ変換する。
    """

    if value is None:
        return None

    try:
        return float(value)

    except (TypeError, ValueError):
        return None


# ============================================================
# Compatibility functions
# ============================================================
#
# 旧LibreHardwareMonitor方式との互換性を維持するための関数。
#
# v1.0.6ではLibreHardwareMonitor.exeを起動しない。
# ============================================================

def is_libre_hardware_monitor_running() -> bool:
    """
    旧API互換用。

    v1.0.6ではLibreHardwareMonitor.exeを検索しない。
    LibreHardwareServiceが利用可能かを確認する。
    """

    return is_libre_hardware_service_ready()


def is_libre_hardware_monitor_ready() -> bool:
    """
    旧API互換用。

    v1.0.6では8085 Web Serverを確認しない。
    LibreHardwareServiceの共有メモリを確認する。
    """

    return is_libre_hardware_service_ready()


def wait_for_libre_hardware_monitor(
    timeout_seconds: int = 30,
) -> bool:
    """
    旧API互換用。

    LibreHardwareMonitorのWeb Serverを待機する処理は
    v1.0.6では使用しない。

    LibreHardwareServiceはWindowsサービスとして
    常駐しているため、短時間の再試行だけを行う。
    """

    logger.info(
        "LibreHardwareServiceの利用可能状態を確認します。 "
        "timeout=%s秒",
        timeout_seconds,
    )

    # LHSの共有メモリがすぐに利用できる場合
    if is_libre_hardware_service_ready():
        return True

    logger.warning(
        "LibreHardwareServiceの共有メモリが利用できません。"
    )

    return False


def start_libre_hardware_monitor(
    wait_timeout: int = 30,
) -> bool:
    """
    旧API互換用。

    v1.0.6ではLibreHardwareMonitor.exeを起動しない。

    LibreHardwareServiceはWindowsサービスとして
    事前に起動していることを前提とする。
    """

    logger.info(
        "LibreHardwareMonitor.exeの起動処理は"
        "v1.0.6では実行しません。"
    )

    logger.info(
        "LibreHardwareServiceの利用可能状態を確認します。"
    )

    return wait_for_libre_hardware_monitor(
        timeout_seconds=wait_timeout
    )


def stop_libre_hardware_monitor(
    process=None,
) -> None:
    """
    旧API互換用。

    v1.0.6ではLibreHardwareMonitor.exeを
    AI PC Diagnosisから終了させない。

    LibreHardwareServiceの起動・停止は
    Windows Service側で管理する。
    """

    logger.debug(
        "LibreHardwareMonitorの停止処理は"
        "v1.0.6では実行しません。"
    )

    return None