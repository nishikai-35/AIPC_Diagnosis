import servicemanager
import win32event
import win32service
import win32serviceutil

from diagnosis.config import get_int
from diagnosis.path_utils import REPORTS_DIR

from service.monitoring import (
    collect_and_save,
    collect_monitoring_data,
    is_sensor_data_ready,
    save_monitoring_data,
    setup_logger,
)

class AIPCDiagnosisMonitoringService(
    win32serviceutil.ServiceFramework
):

    _svc_name_ = "AIPCDiagnosisMonitoring"

    _svc_display_name_ = (
        "AI PC Diagnosis Monitoring"
    )

    _svc_description_ = (
        "AI PC DiagnosisのPC状態監視サービスです。"
        "CPU、メモリ、GPU、ディスクの状態を"
        "定期的に監視します。"
        "CPU、GPU、メモリのセンサー情報は"
        "LibreHardwareServiceから取得します。"
    )

    # ========================================================
    # Startup sensor wait settings
    # ========================================================

    SENSOR_RETRY_SECONDS = 5
    SENSOR_WAIT_TIMEOUT_SECONDS = 120

    def __init__(self, args):

        super().__init__(args)

        self.stop_event = win32event.CreateEvent(
            None,
            0,
            0,
            None,
        )

        self.running = True
        self.logger = None

    # ========================================================
    # Service stop
    # ========================================================

    def SvcStop(self):

        self.ReportServiceStatus(
            win32service.SERVICE_STOP_PENDING
        )

        self.running = False

        if self.logger:
            self.logger.info(
                "AI PC Diagnosis Monitoring Service "
                "の停止要求を受信しました。"
            )

        win32event.SetEvent(
            self.stop_event
        )

    # ========================================================
    # Service start
    # ========================================================

    def SvcDoRun(self):

        self.ReportServiceStatus(
            win32service.SERVICE_RUNNING
        )

        self.logger = setup_logger()

        self.logger.info(
            "AI PC Diagnosis Monitoring Service "
            "のSvcDoRun()を開始しました。"
        )

        servicemanager.LogInfoMsg(
            "AI PC Diagnosis Monitoring Service "
            "SvcDoRun started."
        )

        self.logger.info(
            "AI PC Diagnosis Monitoring Service "
            "を開始します。"
        )

        servicemanager.LogInfoMsg(
            "AI PC Diagnosis Monitoring Service "
            "starting."
        )

        self.main()

    # ========================================================
    # Startup sensor wait
    # ========================================================

    def wait_for_sensor_data(self):
        """
        LibreHardwareServiceのセンサーが
        利用可能になるまで待機する。

        CPU使用率、CPU温度、メモリ使用率が
        取得できれば診断開始可能とする。

        GPUセンサーは任意。
        """

        self.logger.info(
            "起動時診断のため、"
            "LibreHardwareServiceのセンサー初期化を待機します。"
        )

        start_time = __import__(
            "time"
        ).time()

        while self.running:

            try:
                data = collect_monitoring_data()

                if is_sensor_data_ready(data):

                    self.logger.info(
                        "LibreHardwareServiceの"
                        "必須センサー取得が完了しました。"
                    )

                    self.logger.info(
                        "初期センサー値 "
                        "CPU=%s%% CPU_TEMP=%s°C "
                        "MEMORY=%s%% GPU=%s%% GPU_TEMP=%s°C",
                        data["cpu"]["usage"],
                        data["cpu"]["temperature"],
                        data["memory"]["usage"],
                        data["gpu"]["usage"],
                        data["gpu"]["temperature"],
                    )

                    return data

                elapsed = int(
                    __import__(
                        "time"
                    ).time() - start_time
                )

                self.logger.info(
                    "LibreHardwareServiceの"
                    "センサー初期化を待機中です。"
                    " CPU=%s CPU_TEMP=%s "
                    "MEMORY=%s GPU=%s GPU_TEMP=%s "
                    "経過=%s秒",
                    data["cpu"]["usage"],
                    data["cpu"]["temperature"],
                    data["memory"]["usage"],
                    data["gpu"]["usage"],
                    data["gpu"]["temperature"],
                    elapsed,
                )

                if (
                    elapsed
                    >= self.SENSOR_WAIT_TIMEOUT_SECONDS
                ):
                    self.logger.warning(
                        "LibreHardwareServiceの"
                        "センサー待機がタイムアウトしました。"
                        "通常監視へ移行します。"
                    )

                    return None

            except Exception as e:

                self.logger.exception(
                    "起動時センサー取得中に"
                    "エラーが発生しました: %s",
                    e,
                )

            result = win32event.WaitForSingleObject(
                self.stop_event,
                self.SENSOR_RETRY_SECONDS * 1000,
            )

            if result == win32event.WAIT_OBJECT_0:
                self.logger.info(
                    "センサー待機中に"
                    "サービス停止要求を受信しました。"
                )
                return None

        return None

    # ========================================================
    # Startup diagnosis
    # ========================================================

    def generate_startup_diagnosis(self):
        """
        Windows起動時の診断レポートを1回生成する。

        AI分析は実行しない。
        """

        self.logger.info(
            "起動時診断レポートの生成を開始します。"
        )

        try:

            from app import run_diagnosis_process
            from diagnosis.report.html_report import (
                export_html,
            )

            (
                info,
                memory_processes,
                cpu_processes,
                diagnosis,
                ai_analysis,
                log_path,
            ) = run_diagnosis_process(
                ai_enabled=False,
            )

            self.logger.info(
                "起動時診断JSONを生成しました: %s",
                log_path,
            )

            html_path = export_html(
                diagnosis,
                ai_analysis,
                REPORTS_DIR,
            )

            self.logger.info(
                "起動時診断HTMLを生成しました: %s",
                html_path,
            )

            servicemanager.LogInfoMsg(
                "AI PC Diagnosis startup diagnosis "
                "completed successfully."
            )

            return {
                "info": info,
                "diagnosis": diagnosis,
                "log_path": log_path,
                "html_path": html_path,
            }

        except Exception as e:

            self.logger.exception(
                "起動時診断レポート生成中に"
                "エラーが発生しました: %s",
                e,
            )

            servicemanager.LogErrorMsg(
                "AI PC Diagnosis startup diagnosis "
                f"error: {e}"
            )

            return None

    # ========================================================
    # Main service loop
    # ========================================================

    def main(self):

        try:

            interval_seconds = get_int(
                "monitoring",
                "interval_seconds",
            )

            self.logger.info(
                "監視間隔: %s秒",
                interval_seconds,
            )

            self.logger.info(
                "LibreHardwareServiceを使用して"
                "監視を開始します。"
            )

            # =================================================
            # 1. LHSセンサー初期化待ち
            # =================================================

            initial_data = (
                self.wait_for_sensor_data()
            )

            if not self.running:
                return

            # =================================================
            # 2. センサー確定後にcurrent.json保存
            # =================================================

            if initial_data is not None:

                self.logger.info(
                    "起動時の診断データが確定しました。"
                )

                save_monitoring_data(
                    initial_data
                )

                self.logger.info(
                    "起動時のcurrent.jsonを保存しました。"
                )

                # =============================================
                # 3. 起動時診断レポート生成
                # =============================================

                self.generate_startup_diagnosis()

            else:

                self.logger.warning(
                    "起動時のセンサー情報を"
                    "確定できませんでした。"
                    "起動時診断はスキップして"
                    "通常監視へ移行します。"
                )

            # =================================================
            # 4. 通常監視ループ
            # =================================================

            while self.running:

                try:

                    data = collect_and_save()

                    self.logger.info(
                        "監視データ更新完了 "
                        "CPU=%s%% Memory=%s%% GPU=%s%%",
                        data["cpu"]["usage"],
                        data["memory"]["usage"],
                        data["gpu"]["usage"],
                    )

                    servicemanager.LogInfoMsg(
                        "AI PC Diagnosis Monitoring "
                        "updated successfully."
                    )

                except Exception as e:

                    self.logger.exception(
                        "監視処理中に"
                        "エラーが発生しました: %s",
                        e,
                    )

                    servicemanager.LogErrorMsg(
                        "AI PC Diagnosis Monitoring "
                        f"error: {e}"
                    )

                result = win32event.WaitForSingleObject(
                    self.stop_event,
                    interval_seconds * 1000,
                )

                if result == win32event.WAIT_OBJECT_0:
                    break

            self.logger.info(
                "監視ループを終了しました。"
            )

        except Exception as e:

            if self.logger:
                self.logger.exception(
                    "サービスで致命的なエラーが"
                    "発生しました: %s",
                    e,
                )

            servicemanager.LogErrorMsg(
                "AI PC Diagnosis Monitoring "
                f"fatal error: {e}"
            )

            raise

        finally:

            if self.logger:
                self.logger.info(
                    "AI PC Diagnosis Monitoring Service "
                    "を終了します。"
                )


# ============================================================
# Service entry point
# ============================================================

if __name__ == "__main__":

    import sys

    if len(sys.argv) == 1:
        servicemanager.Initialize()
        servicemanager.PrepareToHostSingle(
            AIPCDiagnosisMonitoringService
        )
        servicemanager.StartServiceCtrlDispatcher()

    else:
        win32serviceutil.HandleCommandLine(
            AIPCDiagnosisMonitoringService
        )
