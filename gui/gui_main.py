import tkinter as tk
from tkinter import messagebox
import threading

from app import run_diagnosis_process
from gui.dashboard import Dashboard


class AIPCDiagnosisApp:

    def __init__(self, root):

        self.root = root

        self.root.title(
            "AI PC Diagnosis"
        )

        self.root.geometry(
            "1100x800"
        )

        self.root.minsize(
            900,
            650,
        )

        self.diagnosis_running = False

        self.dashboard = Dashboard(
            self.root,
            on_diagnosis=self.start_diagnosis,
            on_close=self.on_close,
        )

    # ======================================================
    # 診断開始
    # ======================================================

    def start_diagnosis(self, ai_enabled=None):
        """診断を開始する"""

        if self.diagnosis_running:
            return

        self.diagnosis_running = True

        # Dashboard側のAI分析設定を取得
        if ai_enabled is None:
            ai_enabled = getattr(
                self.dashboard,
            "ai_enabled",
            True,
        )

        print(
            f"診断開始：AI分析 "
            f"{'ON' if ai_enabled else 'OFF'}"
        )

        self.dashboard.diagnosis_started()

        thread = threading.Thread(
            target=self.run_diagnosis,
            args=(ai_enabled,),
            daemon=True,
        )

        thread.start()

    # ======================================================
    # バックグラウンド診断
    # ======================================================

    def run_diagnosis(self, ai_enabled=True):

        try:

            (
                info,
                memory_processes,
                cpu_processes,
                diagnosis,
                ai_analysis,
                log_path,
            ) = run_diagnosis_process(
                ai_enabled=ai_enabled
            )

            self.root.after(
                0,
                self.diagnosis_completed,
                info,
                memory_processes,
                cpu_processes,
                diagnosis,
                ai_analysis,
                log_path,
            )

        except Exception as e:

            self.root.after(
                0,
                self.diagnosis_error,
                str(e),
            )

    # ======================================================
    # 診断完了
    # ======================================================

    def diagnosis_completed(
        self,
        info,
        memory_processes,
        cpu_processes,
        diagnosis,
        ai_analysis,
        log_path,
    ):

        self.diagnosis_running = False

        self.dashboard.show_diagnosis(
            info,
            diagnosis,
            ai_analysis,
        )

    # ======================================================
    # 診断エラー
    # ======================================================

    def diagnosis_error(
        self,
        error,
    ):

        self.diagnosis_running = False

        self.dashboard.show_error(
            error,
        )

    # ======================================================
    # 終了
    # ======================================================

    def on_close(self):

        if self.diagnosis_running:

            result = messagebox.askyesno(
                "終了確認",
                "現在診断を実行中です。\n"
                "GUIを終了してもよろしいですか？",
            )

            if not result:
                return

        self.root.destroy()


def main():

    root = tk.Tk()

    app = AIPCDiagnosisApp(
        root
    )

    root.mainloop()


if __name__ == "__main__":

    main()
