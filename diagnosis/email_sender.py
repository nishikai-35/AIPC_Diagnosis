from __future__ import annotations

import base64
from email.message import EmailMessage
from pathlib import Path
from typing import Any

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

from .path_utils import GMAIL_TOKEN_FILE


# ============================================================
# Gmail API設定
# ============================================================

GMAIL_SCOPES = [
    "https://www.googleapis.com/auth/gmail.send",
]


# ============================================================
# Gmail OAuth認証情報
# ============================================================

def _load_gmail_credentials() -> Credentials:
    """
    Gmail OAuth 2.0の認証情報を読み込む。

    通常の監視処理ではブラウザ認証を行わず、
    事前にインストール時などで作成された
    gmail_token.jsonを使用する。

    Returns
    -------
    Credentials
        Gmail APIで使用するOAuth認証情報。

    Raises
    ------
    FileNotFoundError
        gmail_token.jsonが存在しない場合。

    ValueError
        OAuth認証情報が無効な場合。
    """

    if not GMAIL_TOKEN_FILE.is_file():
        raise FileNotFoundError(
            "Gmail OAuth認証トークンが見つかりません: "
            f"{GMAIL_TOKEN_FILE}"
        )

    try:
        credentials = Credentials.from_authorized_user_file(
            str(GMAIL_TOKEN_FILE),
            GMAIL_SCOPES,
        )

    except Exception as exc:
        raise ValueError(
            "Gmail OAuth認証トークンの読み込みに失敗しました。"
        ) from exc

    # --------------------------------------------------------
    # 有効な認証情報
    # --------------------------------------------------------

    if credentials.valid:
        return credentials

    # --------------------------------------------------------
    # 期限切れの場合
    # Refresh Tokenがあれば自動更新
    # --------------------------------------------------------

    if credentials.expired and credentials.refresh_token:

        try:
            credentials.refresh(
                Request()
            )

        except Exception as exc:
            raise ValueError(
                "Gmail OAuth認証トークンの更新に失敗しました。"
            ) from exc

        # 更新後のトークンを保存
        try:
            GMAIL_TOKEN_FILE.write_text(
                credentials.to_json(),
                encoding="utf-8",
            )

        except OSError as exc:
            raise OSError(
                "Gmail OAuth認証トークンの保存に失敗しました: "
                f"{GMAIL_TOKEN_FILE}"
            ) from exc

        return credentials

    raise ValueError(
        "Gmail OAuth認証情報が無効です。"
        "インストール時のGmail OAuth認証を再実行してください。"
    )


# ============================================================
# Gmail APIサービス
# ============================================================

def _build_gmail_service():
    """
    Gmail APIサービスを作成する。

    OAuthブラウザ認証は実行しない。
    """

    credentials = _load_gmail_credentials()

    try:
        return build(
            "gmail",
            "v1",
            credentials=credentials,
            cache_discovery=False,
        )

    except Exception as exc:
        raise RuntimeError(
            "Gmail APIサービスの初期化に失敗しました。"
        ) from exc


# ============================================================
# メール件名
# ============================================================

def _build_subject(
    diagnosis: Any,
) -> str:
    """
    診断結果からメール件名を作成する。
    """

    status = getattr(
        diagnosis,
        "status",
        "不明",
    )

    return f"【AI PC Diagnosis】PC診断結果：{status}"


# ============================================================
# メール本文
# ============================================================

def _build_body(
    diagnosis: Any,
    pc_name: str = "",
) -> str:
    """
    診断結果からメール本文を作成する。
    """

    status = getattr(
        diagnosis,
        "status",
        "不明",
    )

    message = getattr(
        diagnosis,
        "message",
        "",
    )

    lines = [
        "AI PC Diagnosis によりPCの自動診断を実行しました。",
        "",
    ]

    if pc_name:
        lines.extend(
            [
                f"PC名: {pc_name}",
                "",
            ]
        )

    lines.extend(
        [
            f"診断結果: {status}",
            "",
        ]
    )

    if message:
        lines.extend(
            [
                f"概要: {message}",
                "",
            ]
        )

    lines.extend(
        [
            "詳細については添付されたHTML診断レポートをご確認ください。",
            "",
            "このメールは AI PC Diagnosis により自動送信されています。",
        ]
    )

    return "\n".join(lines)


# ============================================================
# メール送信
# ============================================================

def send_diagnosis_email(
    html_path: Path | str,
    diagnosis: Any,
    recipient_email: str,
    pc_name: str = "",
) -> None:
    """
    完全診断で生成されたHTMLレポートを
    Gmail API経由でメール送信する。

    Parameters
    ----------
    html_path:
        添付するHTML診断レポートのパス。

    diagnosis:
        OverallDiagnosisなどの完全診断結果。

    recipient_email:
        config.iniの[mail] recipient_emailに設定された
        診断レポート送信先。

    pc_name:
        config.iniの[user] pc_nameに登録されたPC名。

    Raises
    ------
    FileNotFoundError
        HTMLレポートまたはGmail OAuthトークンが
        存在しない場合。

    ValueError
        メール送信先またはOAuth認証情報が不正な場合。

    OSError
        HTMLファイルまたはOAuthトークンの読み書きに
        失敗した場合。

    RuntimeError
        Gmail APIの初期化または送信に失敗した場合。
    """

    # --------------------------------------------------------
    # HTMLレポート確認
    # --------------------------------------------------------

    html_path = Path(
        html_path
    )

    if not html_path.is_file():
        raise FileNotFoundError(
            "添付するHTML診断レポートが見つかりません: "
            f"{html_path}"
        )

    # --------------------------------------------------------
    # 送信先確認
    # --------------------------------------------------------

    recipient_email = recipient_email.strip()

    if not recipient_email:
        raise ValueError(
            "メール送信先が設定されていません。"
        )

    # --------------------------------------------------------
    # HTML読み込み
    # --------------------------------------------------------

    try:
        html_content = html_path.read_text(
            encoding="utf-8",
        )

    except OSError as exc:
        raise OSError(
            "HTML診断レポートの読み込みに失敗しました: "
            f"{html_path}"
        ) from exc

    # --------------------------------------------------------
    # メール作成
    # --------------------------------------------------------

    message = EmailMessage()

    message["Subject"] = _build_subject(
        diagnosis
    )

    message["To"] = recipient_email

    message.set_content(
        _build_body(
            diagnosis,
            pc_name=pc_name,
        )
    )

    # --------------------------------------------------------
    # HTMLレポートを添付
    # --------------------------------------------------------

    message.add_attachment(
        html_content.encode("utf-8"),
        maintype="text",
        subtype="html",
        filename=html_path.name,
    )

    # --------------------------------------------------------
    # Gmail APIサービス取得
    # --------------------------------------------------------

    service = _build_gmail_service()

    # --------------------------------------------------------
    # Gmail API送信用データ作成
    # --------------------------------------------------------

    encoded_message = base64.urlsafe_b64encode(
        message.as_bytes()
    ).decode("utf-8")

    request_body = {
        "raw": encoded_message,
    }

    # --------------------------------------------------------
    # Gmail API送信
    # --------------------------------------------------------

    try:
        result = (
            service.users()
            .messages()
            .send(
                userId="me",
                body=request_body,
            )
            .execute()
        )

    except Exception as exc:
        raise RuntimeError(
            "Gmail APIによる診断レポートの送信に失敗しました。"
        ) from exc

    # --------------------------------------------------------
    # 送信結果確認
    # --------------------------------------------------------

    message_id = result.get(
        "id",
        "",
    )

    if not message_id:
        raise RuntimeError(
            "Gmail APIから送信結果を取得できませんでした。"
        )