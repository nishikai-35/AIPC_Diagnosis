import tkinter as tk
from tkinter import ttk


# ==========================================================
# ステータスカラー
# ==========================================================

STATUS_COLORS = {
    "正常": "#2E7D32",
    "注意": "#F9A825",
    "警告": "#C62828",
    "情報": "#1565C0",
}


def get_status_color(status):
    """
    診断ステータスに応じた色を返す。
    """

    return STATUS_COLORS.get(
        status,
        "#616161",
    )


# ==========================================================
# ステータスバッジ
# ==========================================================

class StatusBadge(ttk.Frame):

    def __init__(
        self,
        parent,
        status="待機中",
        width=180,
        height=55,
    ):

        super().__init__(parent)

        self.canvas = tk.Canvas(
            self,
            width=width,
            height=height,
            highlightthickness=0,
        )

        self.canvas.pack()

        self.width = width
        self.height = height

        self.set_status(status)

    def set_status(self, status):

        self.canvas.delete("all")

        color = get_status_color(status)

        self.canvas.create_rectangle(
            2,
            2,
            self.width - 2,
            self.height - 2,
            fill=color,
            outline=color,
        )

        self.canvas.create_text(
            self.width / 2,
            self.height / 2,
            text=status,
            fill="white",
            font=("Segoe UI", 18, "bold"),
        )


# ==========================================================
# 診断カード
# ==========================================================

class DiagnosisCard(ttk.LabelFrame):

    def __init__(
        self,
        parent,
        title,
    ):

        super().__init__(
            parent,
            text=title,
            padding=10,
        )

        self.value_label = ttk.Label(
            self,
            text="--",
            font=("Segoe UI", 20, "bold"),
        )

        self.value_label.pack(
            pady=(5, 2),
        )

        self.progress = ttk.Progressbar(
            self,
            orient="horizontal",
            mode="determinate",
            maximum=100,
        )

        self.progress.pack(
            fill="x",
            pady=5,
        )

        self.status_label = ttk.Label(
            self,
            text="待機中",
            font=("Segoe UI", 10, "bold"),
        )

        self.status_label.pack(
            pady=(2, 0),
        )

    def update_value(
        self,
        value,
        status,
        suffix="%",
    ):

        if value is None:

            self.value_label.config(
                text="取得不可",
            )

            self.progress["value"] = 0

        else:

            try:
                numeric_value = float(value)

                self.value_label.config(
                    text=f"{numeric_value:.1f}{suffix}",
                )

                self.progress["value"] = min(
                    max(numeric_value, 0),
                    100,
                )

            except (
                TypeError,
                ValueError,
            ):

                self.value_label.config(
                    text=str(value),
                )

                self.progress["value"] = 0

        self.status_label.config(
            text=status,
            foreground=get_status_color(status),
        )


# ==========================================================
# シンプルな情報カード
# ==========================================================

class InfoCard(ttk.LabelFrame):

    def __init__(
        self,
        parent,
        title,
    ):

        super().__init__(
            parent,
            text=title,
            padding=10,
        )

        self.status_label = ttk.Label(
            self,
            text="待機中",
            font=("Segoe UI", 14, "bold"),
        )

        self.status_label.pack(
            pady=5,
        )

        self.detail_label = ttk.Label(
            self,
            text="",
            justify="left",
            wraplength=260,
        )

        self.detail_label.pack(
            fill="x",
        )

    def update_status(
        self,
        status,
        detail="",
    ):

        self.status_label.config(
            text=status,
            foreground=get_status_color(status),
        )

        self.detail_label.config(
            text=detail,
        )


# ==========================================================
# テキストパネル
# ==========================================================

class TextPanel(ttk.LabelFrame):

    def __init__(
        self,
        parent,
        title,
    ):

        super().__init__(
            parent,
            text=title,
            padding=8,
        )

        text_frame = ttk.Frame(self)

        text_frame.pack(
            fill="both",
            expand=True,
        )

        self.text = tk.Text(
            text_frame,
            wrap="word",
            font=("Segoe UI", 10),
            state="disabled",
            padx=10,
            pady=10,
        )

        scrollbar = ttk.Scrollbar(
            text_frame,
            orient="vertical",
            command=self.text.yview,
        )

        self.text.configure(
            yscrollcommand=scrollbar.set,
        )

        self.text.pack(
            side="left",
            fill="both",
            expand=True,
        )

        scrollbar.pack(
            side="right",
            fill="y",
        )

    def set_text(self, text):

        self.text.config(
            state="normal",
        )

        self.text.delete(
            "1.0",
            tk.END,
        )

        self.text.insert(
            tk.END,
            text,
        )

        self.text.config(
            state="disabled",
        )