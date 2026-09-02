from pathlib import Path
import os
import sys


def get_app_dir() -> Path:
    """
    アプリケーション本体の基準ディレクトリを取得する。

    開発環境:
        AI_pcDiagnosis/

    PyInstaller:
        AI_PC_Diagnosis.exe が存在するフォルダ
    """
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent

    return Path(__file__).resolve().parent.parent


def get_data_dir(app_dir: Path) -> Path:
    """
    設定・ログ・レポートなどのデータ保存先を取得する。

    開発環境:
        プロジェクトフォルダを使用する。

    PyInstaller:
        C:\\ProgramData\\AI_PC_Diagnosis を使用する。
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

DATA_DIR = get_data_dir(APP_DIR)

# アプリ本体と一緒に配置するもの
TOOLS_DIR = APP_DIR / "tools"

LHM_DIR = TOOLS_DIR / "LibreHardwareMonitor"

LHM_EXE = LHM_DIR / "LibreHardwareMonitor.exe"

SMARTCTL_DIR = TOOLS_DIR / "smartctl"

SMARTCTL_EXE = SMARTCTL_DIR / "smartctl.exe"


# 管理・運用データ
CONFIG_FILE = DATA_DIR / "config.ini"

REPORTS_DIR = DATA_DIR / "reports"

LOGS_DIR = DATA_DIR / "logs"
