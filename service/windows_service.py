import sys
import servicemanager
import win32event
import win32service
import win32serviceutil


from service.monitoring import collect_and_save
from diagnosis.config import get_int


class AIPCDiagnosisMonitoringService(win32serviceutil.ServiceFramework):
    """
    AI PC Diagnosis Monitoring Windows Service
    """

    _svc_name_ = "AIPCDiagnosisMonitoring"
    _svc_display_name_ = "AI PC Diagnosis Monitoring"
    _svc_description_ = (
        "AI PC DiagnosisのPC状態監視サービスです。"
        "CPU、メモリ、GPU、ディスクの状態を定期的に監視します。"
    )

    def __init__(self, args):
        super().__init__(args)

        self.stop_event = win32event.CreateEvent(
            None,
            0,
            0,
            None,
        )

        self.running = True

    def SvcStop(self):
        """
        Windowsからサービス停止要求を受けたときに呼ばれる。
        """

        self.ReportServiceStatus(
            win32service.SERVICE_STOP_PENDING
        )

        self.running = False

        win32event.SetEvent(
            self.stop_event
        )

        servicemanager.LogInfoMsg(
            "AI PC Diagnosis Monitoring Serviceを停止しています。"
        )

    def SvcDoRun(self):
        """
        Windowsサービス開始時に呼ばれる。
        """

        servicemanager.LogInfoMsg(
            "AI PC Diagnosis Monitoring Serviceを開始しました。"
        )

        self.main()

    def main(self):
        """
        監視処理本体。
        """

        interval_seconds = get_int(
            "monitoring",
            "interval_seconds",
        )

        servicemanager.LogInfoMsg(
            f"監視間隔: {interval_seconds}秒"
        )

        while self.running:

            try:
                data = collect_and_save()

                servicemanager.LogInfoMsg(
                    "監視データを保存しました。"
                    f" timestamp={data['timestamp']}"
                )

            except Exception as e:

                servicemanager.LogErrorMsg(
                    "監視データの取得・保存に失敗しました。"
                    f" error={e}"
                )

            result = win32event.WaitForSingleObject(
                self.stop_event,
                interval_seconds * 1000,
            )

            if result == win32event.WAIT_OBJECT_0:
                break

        servicemanager.LogInfoMsg(
            "AI PC Diagnosis Monitoring Serviceを終了しました。"
        )


if __name__ == "__main__":
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
