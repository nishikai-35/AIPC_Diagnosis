from pathlib import Path
import os
import sys


def get_app_dir() -> Path:
    """
    アプリケーション本体の基準ディレクトリを取得する。

    GUI:
        C:\\Program Files\\AI_PC_Diagnosis

    Service:
        C:\\Program Files\\AI_PC_Diagnosis\\AI_PC_Diagnosis_Service

    開発環境:
        AI_PC_Diagnosis/
    """
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent

    return Path(__file__).resolve().parent.parent


def get_install_dir(app_dir: Path) -> Path:
    """
    インストール全体の基準ディレクトリを取得する。

    GUI:
        app_dirそのもの

    Service:
        AI_PC_Diagnosis_Serviceの親ディレクトリ
    """
    if not getattr(sys, "frozen", False):
        return app_dir

    tools_dir = app_dir / "tools"

    if tools_dir.exists():
        return app_dir

    parent_tools_dir = app_dir.parent / "tools"

    if parent_tools_dir.exists():
        return app_dir.parent

    # toolsがまだ存在しない場合は従来のapp_dirを返す
    return app_dir


def get_data_dir(app_dir: Path) -> Path:
    """
    設定・ログ・レポートなどのデータ保存先を取得する。

    開発環境:
        プロジェクトフォルダ

    PyInstaller:
        C:\\ProgramData\\AI_PC_Diagnosis
    """
    if getattr(sys, "frozen", False):
        program_data = os.environ.get("PROGRAMDATA")

        if not program_data:
            raise EnvironmentError(
                "PROGRAMDATA環境変数が取得できません。"
            )

        return Path(program_data) / "AI_PC_Diagnosis"

    return app_dir


APP_DIR = get_app_dir()

# GUI / Service共通のインストールルート
INSTALL_DIR = get_install_dir(APP_DIR)

DATA_DIR = get_data_dir(APP_DIR)


# アプリ本体と一緒に配置するもの
TOOLS_DIR = INSTALL_DIR / "tools"

SMARTCTL_DIR = TOOLS_DIR / "smartctl"

SMARTCTL_EXE = SMARTCTL_DIR / "smartctl.exe"


# 管理・運用データ
CONFIG_FILE = DATA_DIR / "config.ini"

# Gmail OAuth認証トークン
GMAIL_TOKEN_FILE = DATA_DIR / "gmail_token.json"

REPORTS_DIR = DATA_DIR / "reports"

LOGS_DIR = DATA_DIR / "logs"