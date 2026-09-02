import tkinter as tk
from tkinter import ttk, messagebox
from pathlib import Path
import webbrowser

class ReportWindow(tk.Toplevel):
    """過去のHTMLレポートを表示するウィンドウ"""

    def __init__(self, parent, reports_dir):
        super().__init__(parent)

        self.parent = parent
        self.reports_dir = Path(reports_dir)

        self.title("過去レポート")
        self.geometry("750x500")
        self.minsize(650, 400)

        self.create_widgets()
        self.load_reports()


    def create_widgets(self):
        """GUI部品を作成"""

        # ===== タイトル =====
        title_label = ttk.Label(
            self,
            text="過去レポート",
            font=("Yu Gothic UI", 16, "bold")
        )
        title_label.pack(
            pady=(15, 10)
        )

        # ===== 説明 =====
        info_label = ttk.Label(
            self,
            text="過去に作成されたHTML診断レポートを選択してください。",
            font=("Yu Gothic UI", 10)
        )
        info_label.pack(
            pady=(0, 10)
        )

        # ===== レポート一覧フレーム =====
        list_frame = ttk.Frame(self)
        list_frame.pack(
            fill="both",
            expand=True,
            padx=20,
            pady=10
        )

        # ===== Treeview =====
        columns = (
            "date",
            "filename",
        )

        self.report_tree = ttk.Treeview(
            list_frame,
            columns=columns,
            show="headings",
            selectmode="browse"
        )

        self.report_tree.heading(
            "date",
            text="作成日時"
        )

        self.report_tree.heading(
            "filename",
            text="レポートファイル"
        )

        self.report_tree.column(
            "date",
            width=180,
            anchor="center"
        )

        self.report_tree.column(
            "filename",
            width=450,
            anchor="w"
        )

        # ===== スクロールバー =====
        scrollbar = ttk.Scrollbar(
            list_frame,
            orient="vertical",
            command=self.report_tree.yview
        )

        self.report_tree.configure(
            yscrollcommand=scrollbar.set
        )

        self.report_tree.pack(
            side="left",
            fill="both",
            expand=True
        )

        scrollbar.pack(
            side="right",
            fill="y"
        )

        # ===== ダブルクリック =====
        self.report_tree.bind(
            "<Double-1>",
            self.open_selected_report
        )

        # ===== ボタンフレーム =====
        button_frame = ttk.Frame(self)
        button_frame.pack(
            fill="x",
            padx=20,
            pady=(5, 15)
        )

        # 更新ボタン
        refresh_button = ttk.Button(
            button_frame,
            text="一覧を更新",
            command=self.load_reports
        )
        refresh_button.pack(
            side="left"
        )

        # レポートを開く
        open_button = ttk.Button(
            button_frame,
            text="レポートを開く",
            command=self.open_selected_report
        )
        open_button.pack(
            side="right",
            padx=(10, 0)
        )

        # 閉じる
        close_button = ttk.Button(
            button_frame,
            text="閉じる",
            command=self.destroy
        )
        close_button.pack(
            side="right"
        )

    def load_reports(self):
        """reportsフォルダからHTMLレポートを読み込む"""

        # 現在の一覧を削除
        for item in self.report_tree.get_children():
            self.report_tree.delete(item)

        # reportsフォルダが存在しない場合
        if not self.reports_dir.exists():
            self.reports_dir.mkdir(
                parents=True,
                exist_ok=True
            )

            messagebox.showinfo(
                "過去レポート",
                "まだレポートがありません。",
                parent=self
            )

            return

        # HTMLファイルを取得
        reports = list(
            self.reports_dir.glob("*.html")
        )

        # 新しい順
        reports.sort(
            key=lambda path: path.stat().st_mtime,
            reverse=True
        )

        # Treeviewへ追加
        for report_path in reports:

            modified_time = report_path.stat().st_mtime

            from datetime import datetime

            date_text = datetime.fromtimestamp(
                modified_time
            ).strftime(
                "%Y/%m/%d %H:%M:%S"
            )

            self.report_tree.insert(
                "",
                "end",
                values=(
                    date_text,
                    report_path.name
                ),
                tags=(
                    str(report_path),
                )
            )

        # レポートがない場合
        if not reports:
            self.report_tree.insert(
                "",
                "end",
                values=(
                    "",
                    "レポートがありません"
                )
            )

    def open_selected_report(self, event=None):
        """選択されたHTMLレポートをブラウザで開く"""

        selection = self.report_tree.selection()

        if not selection:
            messagebox.showwarning(
                "レポート",
                "開くレポートを選択してください。",
                parent=self
            )
            return

        item = selection[0]

        tags = self.report_tree.item(
            item,
            "tags"
        )

        if not tags:
            return

        report_path = Path(tags[0])

        if not report_path.exists():
            messagebox.showerror(
                "レポート",
                "選択したレポートが見つかりません。",
                parent=self
            )
            return

        # 既定ブラウザでHTMLを開く
        webbrowser.open(
            report_path.resolve().as_uri()
        )
