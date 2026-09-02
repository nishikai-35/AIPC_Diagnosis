import tkinter as tk
from tkinter import ttk, messagebox
import os
import webbrowser
from .report_window import ReportWindow
from diagnosis.path_utils import REPORTS_DIR

from .widgets import (
    DiagnosisCard,
    InfoCard,
    StatusBadge,
    TextPanel,
)

from diagnosis.report.html_report import export_html


class Dashboard:

    def __init__(
        self,
        parent,
        on_diagnosis,
        on_close,
    ):
        self.parent = parent
        self.on_diagnosis = on_diagnosis
        self.on_close = on_close

        # 最新HTMLレポートのパス
        self.html_path = None

        self.create_widgets()

    # ======================================================
    # GUI作成
    # ======================================================

    def create_widgets(self):

        # --------------------------------------------------
        # メインコンテナ
        # --------------------------------------------------

        main_frame = ttk.Frame(
            self.parent,
            padding=20,
        )

        main_frame.pack(
            fill="both",
            expand=True,
        )

        # --------------------------------------------------
        # ヘッダー
        # --------------------------------------------------

        header_frame = ttk.Frame(
            main_frame,
        )

        header_frame.pack(
            fill="x",
            pady=(0, 15),
        )

        title_frame = ttk.Frame(
            header_frame,
        )

        title_frame.pack(
            side="left",
        )

        title = ttk.Label(
            title_frame,
            text="AI PC Diagnosis",
            font=("Segoe UI", 26, "bold"),
        )

        title.pack(
            anchor="w",
        )

        subtitle = ttk.Label(
            title_frame,
            text="AI搭載 PC 診断ダッシュボード",
            font=("Segoe UI", 10),
        )

        subtitle.pack(
            anchor="w",
        )

        # --------------------------------------------------
        # 総合ステータス
        # --------------------------------------------------

        status_frame = ttk.Frame(
            header_frame,
        )

        status_frame.pack(
            side="right",
        )

        self.overall_badge = StatusBadge(
            status_frame,
            "待機中",
        )

        self.overall_badge.pack()

        # --------------------------------------------------
        # 操作エリア
        # --------------------------------------------------

        ai_frame = ttk.LabelFrame(
            main_frame,
            text="AI分析"
        )

        ai_frame.pack(
            fill="x",
            padx=10,
            pady=10
        )

        self.ai_enabled = tk.BooleanVar(value=True)

        ttk.Radiobutton(
            ai_frame,
            text="ON",
            variable=self.ai_enabled,
            value=True
        ).pack(
            side="left",
            padx=10,
            pady=5
        )

        ttk.Radiobutton(
            ai_frame,
            text="OFF",
            variable=self.ai_enabled,
            value=False
        ).pack(
            side="left",
            padx=10,
            pady=5
        )


        control_frame = ttk.Frame(
            main_frame,
        )

        control_frame.pack(
            fill="x",
            pady=(0, 10),
        )

        self.diagnosis_button = ttk.Button(
            control_frame,
            text="今すぐ診断",
            command=self.start_diagnosis,
            width=20,
        )

        self.diagnosis_button.pack(
            side="left",
        )
        
        self.html_button = ttk.Button(
            control_frame,
            text="HTMLレポートを表示",
            command=self.open_html_report,
            width=22,
            state="disabled",
        )

        self.html_button.pack(
            side="left",
            padx=(10, 0),
        )
        
        self.report_button = ttk.Button(
            control_frame,
            text="過去レポート",
            command=self.show_reports,
            width=20,
        )

        self.report_button.pack(
            side="left",
            padx=(10, 0),
        )

        self.status_label = ttk.Label(
            control_frame,
            text="待機中",
            font=("Segoe UI", 10),
        )

        self.status_label.pack(
            side="left",
            padx=15,
        )

        self.progress = ttk.Progressbar(
            control_frame,
            mode="indeterminate",
        )

        self.progress.pack(
            side="right",
            fill="x",
            expand=True,
            padx=(20, 0),
        )

        # --------------------------------------------------
        # 使用率カード
        # --------------------------------------------------

        usage_frame = ttk.LabelFrame(
            main_frame,
            text="システム使用状況",
            padding=10,
        )

        usage_frame.pack(
            fill="x",
            pady=5,
        )

        for column in range(3):

            usage_frame.columnconfigure(
                column,
                weight=1,
            )

        self.cpu_card = DiagnosisCard(
            usage_frame,
            "CPU使用率",
        )

        self.memory_card = DiagnosisCard(
            usage_frame,
            "メモリ使用率",
        )

        self.disk_card = DiagnosisCard(
            usage_frame,
            "ディスク使用率",
        )

        self.cpu_card.grid(
            row=0,
            column=0,
            sticky="nsew",
            padx=5,
        )

        self.memory_card.grid(
            row=0,
            column=1,
            sticky="nsew",
            padx=5,
        )

        self.disk_card.grid(
            row=0,
            column=2,
            sticky="nsew",
            padx=5,
        )

        # --------------------------------------------------
        # 温度・SMART
        # --------------------------------------------------

        hardware_frame = ttk.Frame(
            main_frame,
        )

        hardware_frame.pack(
            fill="x",
            pady=5,
        )

        for column in range(3):

            hardware_frame.columnconfigure(
                column,
                weight=1,
            )

        self.cpu_temp_card = DiagnosisCard(
            hardware_frame,
            "CPU温度",
        )

        self.gpu_temp_card = DiagnosisCard(
            hardware_frame,
            "GPU温度",
        )

        self.smart_card = InfoCard(
            hardware_frame,
            "ストレージ SMART",
        )

        self.cpu_temp_card.grid(
            row=0,
            column=0,
            sticky="nsew",
            padx=5,
        )

        self.gpu_temp_card.grid(
            row=0,
            column=1,
            sticky="nsew",
            padx=5,
        )

        self.smart_card.grid(
            row=0,
            column=2,
            sticky="nsew",
            padx=5,
        )

        # --------------------------------------------------
        # 下部スクロールエリア
        # --------------------------------------------------

        bottom_frame = ttk.Frame(
            main_frame,
        )

        bottom_frame.pack(
            fill="both",
            expand=True,
            pady=(10, 0),
        )

        bottom_frame.columnconfigure(
            0,
            weight=1,
        )

        bottom_frame.columnconfigure(
            1,
            weight=1,
        )

        bottom_frame.rowconfigure(
            0,
            weight=1,
        )

        # --------------------------------------------------
        # AI分析
        # --------------------------------------------------

        self.ai_panel = TextPanel(
            bottom_frame,
            "AI分析",
        )

        self.ai_panel.grid(
            row=0,
            column=0,
            sticky="nsew",
            padx=(0, 5),
        )

        # --------------------------------------------------
        # 最終診断
        # --------------------------------------------------

        self.summary_panel = TextPanel(
            bottom_frame,
            "最終診断サマリー",
        )

        self.summary_panel.grid(
            row=0,
            column=1,
            sticky="nsew",
            padx=(5, 0),
        )

        # --------------------------------------------------
        # 下部操作
        # --------------------------------------------------

        bottom_control = ttk.Frame(
            main_frame,
        )

        bottom_control.pack(
            fill="x",
            pady=(10, 0),
        )

        # 終了ボタン
        exit_button = ttk.Button(
            bottom_control,
            text="終了",
            command=self.on_close,
            width=15,
        )

        exit_button.pack(
            side="right",
        )

    # ======================================================
    # 診断開始表示
    # ======================================================
    
    def diagnosis_started(self):
    
        self.diagnosis_button.config(
            state="disabled",
        )
    
        # 診断中はHTMLボタンを無効化
        self.html_button.config(
            state="disabled",
        )
    
        # 古いHTMLパスをクリア
        self.html_path = None
    
        self.status_label.config(
            text="診断中...",
        )
    
        self.overall_badge.set_status(
            "診断中"
        )
    
        self.progress.start(10)
    
        # AI設定に応じて表示を変更
        if self.ai_enabled.get():
            self.ai_panel.set_text(
                "AI分析を実行しています...\n"
                "しばらくお待ちください。"
            )
        else:
            self.ai_panel.set_text(
                "AI分析：無効\n"
                "基本診断のみ実行しています。"
            )
    
        self.summary_panel.set_text(
            "診断を実行しています..."
        )
    
    
    def start_diagnosis(self, ai_enabled=None):
        """GUIのAI設定を取得して診断処理へ渡す"""
    
        if ai_enabled is None:
            ai_enabled = self.ai_enabled.get()
    
        print(
            f"GUI設定：AI分析 "
            f"{'ON' if ai_enabled else 'OFF'}"
        )
    
        self.on_diagnosis(ai_enabled)

    # ======================================================
    # 診断完了
    # ======================================================
    
    def show_diagnosis(
        self,
        info,
        diagnosis,
        ai_analysis,
    ):
    
        self.progress.stop()
    
        self.diagnosis_button.config(
            state="normal",
        )
    
        self.status_label.config(
            text=f"診断完了：{diagnosis.status}",
        )
    
        # --------------------------------------------------
        # 総合ステータス
        # --------------------------------------------------
    
        self.overall_badge.set_status(
            diagnosis.status
        )
    
        # --------------------------------------------------
        # CPU
        # --------------------------------------------------
    
        self.cpu_card.update_value(
            info["cpu_usage"],
            self.find_result_status(
                diagnosis,
                "CPU",
            ),
        )
    
        # --------------------------------------------------
        # メモリ
        # --------------------------------------------------
    
        self.memory_card.update_value(
            info["memory_usage"],
            self.find_result_status(
                diagnosis,
                "メモリ",
            ),
        )
    
        # --------------------------------------------------
        # ディスク
        # --------------------------------------------------
    
        self.disk_card.update_value(
            info["disk_usage"],
            self.find_result_status(
                diagnosis,
                "ディスク",
            ),
        )
    
        # --------------------------------------------------
        # CPU温度
        # --------------------------------------------------
    
        self.cpu_temp_card.update_value(
            info["cpu_temperature"],
            self.find_result_status(
                diagnosis,
                "CPU温度",
            ),
            "°C",
        )
    
        # --------------------------------------------------
        # GPU温度
        # --------------------------------------------------
    
        self.gpu_temp_card.update_value(
            info["gpu_temperature"],
            self.find_result_status(
                diagnosis,
                "GPU温度",
            ),
            "°C",
        )
    
        # --------------------------------------------------
        # SMART
        # --------------------------------------------------
    
        smart_status = self.find_result_status(
            diagnosis,
            "ストレージSMART",
        )
    
        self.smart_card.update_status(
            smart_status,
            "NVMe SSDの健康状態",
        )
    
        # --------------------------------------------------
        # AI分析
        # --------------------------------------------------
    
        if ai_analysis is None:
        
            # AI OFFの場合
            ai_text = ""
    
            ai_text += "AI分析：無効\n"
            ai_text += "────────────────────\n"
            ai_text += (
                "AI分析は実行されていません。\n"
                "基本診断のみ実行しました。"
            )
    
        else:
        
            # AI ONの場合
            ai_text = ""
    
            ai_text += "概要\n"
            ai_text += "────────────────────\n"
            ai_text += (
                f"{ai_analysis.summary}\n\n"
            )
    
            ai_text += "優先度\n"
            ai_text += "────────────────────\n"
            ai_text += (
                f"{ai_analysis.priority}\n\n"
            )
    
            if ai_analysis.causes:
            
                ai_text += "AI分析による原因\n"
                ai_text += "────────────────────\n"
    
                for cause in ai_analysis.causes:
                
                    ai_text += (
                        f"・{cause}\n"
                    )
    
                ai_text += "\n"
    
            if ai_analysis.recommendations:
            
                ai_text += "AI分析による推奨対策\n"
                ai_text += "────────────────────\n"
    
                for recommendation in (
                    ai_analysis.recommendations
                ):
    
                    ai_text += (
                        f"・{recommendation}\n"
                    )
    
        self.ai_panel.set_text(
            ai_text
        )
    
        # --------------------------------------------------
        # 最終診断
        # --------------------------------------------------
    
        summary_text = ""
    
        summary_text += (
            f"総合評価：{diagnosis.status}\n\n"
        )
    
        summary_text += (
            f"{diagnosis.message}\n\n"
        )
    
        if diagnosis.causes:
        
            summary_text += "主な原因\n"
            summary_text += "────────────────────\n"
    
            for cause in diagnosis.causes:
            
                summary_text += (
                    f"・{cause}\n"
                )
    
            summary_text += "\n"
    
        if diagnosis.recommendations:
        
            summary_text += "推奨対策\n"
            summary_text += "────────────────────\n"
    
            for index, recommendation in enumerate(
                diagnosis.recommendations,
                start=1,
            ):
    
                summary_text += (
                    f"{index}. "
                    f"{recommendation}\n"
                )
    
        self.summary_panel.set_text(
            summary_text
        )
    
        # --------------------------------------------------
        # HTMLレポート生成
        # --------------------------------------------------
    
        self.generate_html_report(
            diagnosis,
            ai_analysis,
        )

    # ======================================================
    # HTMLレポート生成
    # ======================================================

    def generate_html_report(
        self,
        diagnosis,
        ai_analysis,
    ):

        try:

            self.html_path = export_html(
                diagnosis,
                ai_analysis,
                "reports",
            )

            # ファイルが実際に存在するか確認
            if self.html_path and os.path.exists(
                self.html_path
            ):

                self.html_button.config(
                    state="normal",
                )

                self.status_label.config(
                    text=(
                        f"診断完了：{diagnosis.status}"
                        " / HTMLレポート生成済み"
                    ),
                )

            else:

                self.html_path = None

                self.html_button.config(
                    state="disabled",
                )

        except Exception as e:

            self.html_path = None

            self.html_button.config(
                state="disabled",
            )

            print(
                "HTMLレポート生成エラー:",
                e,
            )

    # ======================================================
    # HTMLレポート表示
    # ======================================================

    def open_html_report(self):

        if not self.html_path:

            messagebox.showwarning(
                "HTMLレポート",
                "HTMLレポートがまだ生成されていません。",
            )

            return

        if not os.path.exists(
            self.html_path
        ):

            messagebox.showerror(
                "HTMLレポート",
                "HTMLレポートファイルが見つかりません。\n\n"
                f"{self.html_path}",
            )

            self.html_button.config(
                state="disabled",
            )

            return

        try:

            # 絶対パスへ変換
            absolute_path = os.path.abspath(
                self.html_path
            )

            # Windowsの既定ブラウザで開く
            webbrowser.open(
                "file:///"
                + absolute_path.replace(
                    "\\",
                    "/",
                )
            )

        except Exception as e:

            messagebox.showerror(
                "HTMLレポート",
                "HTMLレポートを開けませんでした。\n\n"
                f"{e}",
            )

    # ======================================================
    # 個別診断ステータス取得
    # ======================================================

    @staticmethod
    def find_result_status(
        diagnosis,
        item,
    ):

        for result in diagnosis.results:

            if result.item == item:

                return result.status

        return "情報"

    # ======================================================
    # 過去レポート
    # ======================================================
    def show_reports(self):
        """過去のHTMLレポート一覧を表示"""

        ReportWindow(
            self.parent,
            REPORTS_DIR
        )

    # ======================================================
    # エラー
    # ======================================================

    def show_error(
        self,
        error,
    ):

        self.progress.stop()

        self.diagnosis_button.config(
            state="normal",
        )

        self.html_button.config(
            state="disabled",
        )

        self.html_path = None

        self.status_label.config(
            text="診断エラー",
        )

        self.overall_badge.set_status(
            "警告"
        )

        self.summary_panel.set_text(
            "診断処理中にエラーが発生しました。\n\n"
            f"{error}"
        )

    # ======================================================
    # 初期表示
    # ======================================================

    def show_initial(self):

        self.html_path = None

        self.html_button.config(
            state="disabled",
        )

        self.overall_badge.set_status(
            "待機中"
        )

        self.status_label.config(
            text="待機中",
        )
