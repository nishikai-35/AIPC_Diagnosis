import os
import sys

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow


# ============================================================
# Gmail OAuth 設定
# ============================================================

# Gmail APIでメール送信を行うための権限
SCOPES = [
    "https://www.googleapis.com/auth/gmail.send",
]

# AI PC Diagnosis 共通データフォルダ
PROGRAM_DATA_DIR = os.path.join(
    os.environ.get("PROGRAMDATA", r"C:\ProgramData"),
    "AI_PC_Diagnosis",
)

# OAuth認証トークン保存先
TOKEN_FILE = os.path.join(
    PROGRAM_DATA_DIR,
    "gmail_token.json",
)


# ============================================================
# credentials.json の場所を取得
# ============================================================

def get_credentials_file() -> str:
    """
    PyInstaller EXE / 開発環境の両方に対応して
    credentials.json のパスを取得する。
    """

    if getattr(sys, "frozen", False):
        # PyInstallerで実行した場合
        base_dir = getattr(sys, "_MEIPASS", os.path.dirname(sys.executable))

        candidates = [
            os.path.join(base_dir, "credentials.json"),
            os.path.join(os.path.dirname(sys.executable), "credentials.json"),
        ]
    else:
        # Pythonから直接実行した場合
        base_dir = os.path.dirname(os.path.abspath(__file__))

        candidates = [
            os.path.join(base_dir, "credentials.json"),
            os.path.join(os.getcwd(), "credentials.json"),
        ]

    for path in candidates:
        if os.path.isfile(path):
            return path

    raise FileNotFoundError(
        "Google OAuth認証情報が見つかりません: credentials.json"
    )


# ============================================================
# Gmail OAuth認証
# ============================================================

def authenticate_gmail() -> Credentials:
    """
    Gmail OAuth認証を実行する。

    動作:
        1. 既存のgmail_token.jsonを確認
        2. 有効なトークンがあれば再利用
        3. 期限切れでもrefresh_tokenがあれば自動更新
        4. トークンがない場合はブラウザでOAuth認証
        5. 認証情報をgmail_token.jsonへ保存
    """

    creds = None

    # --------------------------------------------------------
    # ProgramDataフォルダ作成
    # --------------------------------------------------------

    os.makedirs(PROGRAM_DATA_DIR, exist_ok=True)

    # --------------------------------------------------------
    # 既存トークンを読み込む
    # --------------------------------------------------------

    if os.path.isfile(TOKEN_FILE):
        try:
            creds = Credentials.from_authorized_user_file(
                TOKEN_FILE,
                SCOPES,
            )
        except Exception as exc:
            print(
                f"既存のGmail OAuth認証情報を読み込めませんでした: {exc}"
            )
            creds = None

    # --------------------------------------------------------
    # 認証情報が無い / 無効な場合
    # --------------------------------------------------------

    if not creds or not creds.valid:

        # ----------------------------------------------------
        # アクセストークン期限切れ
        # refresh_tokenがあれば自動更新
        # ----------------------------------------------------

        if creds and creds.expired and creds.refresh_token:
            print("Gmail OAuthアクセストークンを更新しています。")

            try:
                creds.refresh(Request())
            except Exception as exc:
                print(
                    f"Gmail OAuthトークンの更新に失敗しました: {exc}"
                )
                creds = None

        # ----------------------------------------------------
        # refreshできない場合は初回OAuth認証
        # ----------------------------------------------------

        if not creds or not creds.valid:
            credentials_file = get_credentials_file()

            print("Gmail OAuth認証を開始します。")
            print("ブラウザが起動しますので、Googleアカウントで認証してください。")

            flow = InstalledAppFlow.from_client_secrets_file(
                credentials_file,
                SCOPES,
            )

            # ローカルWebサーバーを使用してブラウザ認証
            creds = flow.run_local_server(
                port=0,
                access_type="offline",
                prompt="consent",
            )

    # --------------------------------------------------------
    # 認証情報を保存
    # --------------------------------------------------------

    if not creds or not creds.valid:
        raise RuntimeError(
            "Gmail OAuth認証に失敗しました。"
        )

    with open(TOKEN_FILE, "w", encoding="utf-8") as token:
        token.write(creds.to_json())

    print("Gmail OAuth認証成功")
    print(f"Token file: {TOKEN_FILE}")

    return creds


# ============================================================
# メイン処理
# ============================================================

def main() -> int:
    """
    Gmail OAuth認証のエントリーポイント。
    """

    try:
        authenticate_gmail()
        return 0

    except FileNotFoundError as exc:
        print(f"ERROR: {exc}")
        return 1

    except Exception as exc:
        print(f"Gmail OAuth認証に失敗しました: {exc}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
