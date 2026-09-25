import configparser
import os
import tempfile
import shutil
from .path_utils import CONFIG_FILE


def validate_percentage_threshold(
    config: configparser.ConfigParser,
    item_name: str,
    caution_option: str,
    warning_option: str,
) -> None:
    """
    0～100%の診断閾値を検証する。

    条件:
        - 注意値が0～100
        - 警告値が0～100
        - 注意値 < 警告値
    """

    caution = config.getint(
        "diagnosis",
        caution_option,
    )

    warning = config.getint(
        "diagnosis",
        warning_option,
    )

    if not 0 <= caution <= 100:
        raise ValueError(
            f"{item_name}の注意閾値は0～100で設定してください: "
            f"{caution}"
        )

    if not 0 <= warning <= 100:
        raise ValueError(
            f"{item_name}の警告閾値は0～100で設定してください: "
            f"{warning}"
        )

    if caution >= warning:
        raise ValueError(
            f"{item_name}の注意閾値は"
            f"警告閾値より小さくしてください: "
            f"注意={caution}, 警告={warning}"
        )


def validate_temperature_threshold(
    config: configparser.ConfigParser,
    item_name: str,
    caution_option: str,
    warning_option: str,
) -> None:
    """
    温度系の診断閾値を検証する。

    条件:
        - 注意値が0～120℃
        - 警告値が0～120℃
        - 注意値 < 警告値
    """

    caution = config.getint(
        "diagnosis",
        caution_option,
    )

    warning = config.getint(
        "diagnosis",
        warning_option,
    )

    if not 0 <= caution <= 120:
        raise ValueError(
            f"{item_name}の注意閾値は0～120℃で設定してください: "
            f"{caution}"
        )

    if not 0 <= warning <= 120:
        raise ValueError(
            f"{item_name}の警告閾値は0～120℃で設定してください: "
            f"{warning}"
        )

    if caution >= warning:
        raise ValueError(
            f"{item_name}の注意閾値は"
            f"警告閾値より小さくしてください: "
            f"注意={caution}, 警告={warning}"
        )


def validate_retention(
    config: configparser.ConfigParser,
    option: str,
    label: str,
) -> None:
    """
    保存期間を検証する。

    条件:
        - 1時間以上
    """

    hours = config.getint(
        "retention",
        option,
    )

    if hours <= 0:
        raise ValueError(
            f"{label}の保存期間は1時間以上で設定してください: "
            f"{hours}"
        )


# ==========================================================
# 監視間隔検証
# ==========================================================
def validate_monitoring_interval(
    config: configparser.ConfigParser,
) -> None:
    """
    監視間隔を検証する。

    条件:
        - 1秒以上
    """

    interval_seconds = config.getint(
        "monitoring",
        "interval_seconds",
    )

    if interval_seconds <= 0:
        raise ValueError(
            "監視間隔は1秒以上で設定してください: "
            f"{interval_seconds}"
        )


def migrate_config(
    config: configparser.ConfigParser,
) -> bool:
    """
    既存のconfig.iniに不足している設定を追加する。

    既存の設定値は変更しない。
    戻り値:
        True  = 設定を追加した
        False = 変更なし
    """

    changed = False

    # ==========================================================
    # デフォルト設定
    # ==========================================================

    default_sections = {
        "diagnosis": {
            "cpu_caution": "80",
            "cpu_warning": "95",
            "memory_caution": "80",
            "memory_warning": "90",
            "disk_caution": "80",
            "disk_warning": "90",
            "cpu_temperature_caution": "80",
            "cpu_temperature_warning": "90",
        },
        "retention": {
            "json_hours": "120",
            "html_hours": "120",
        },
        "monitoring": {
            "interval_seconds": "300",
        },
        "user": {
            "name": "",
            "email": "",
            "pc_name": "",
        },
        "mail": {
            "recipient_email": "nishikai120305@gmail.com",
        },
    }

    # ==========================================================
    # 不足セクション・項目を追加
    # ==========================================================

    for section, options in default_sections.items():

        if not config.has_section(section):
            config.add_section(section)
            changed = True

        for option, default_value in options.items():

            if not config.has_option(section, option):
                config.set(
                    section,
                    option,
                    default_value,
                )
                changed = True

    return changed


def validate_config(
    config: configparser.ConfigParser,
) -> None:
    """
    config.iniの全設定を検証する。
    """

    # ==========================================================
    # 必須セクション確認
    # ==========================================================

    required_sections = (
        "diagnosis",
        "retention",
        "monitoring",
    )

    for section in required_sections:
        if not config.has_section(section):
            raise ValueError(
                f"設定セクションが見つかりません: [{section}]"
            )

    # ==========================================================
    # 必須設定項目確認
    # ==========================================================

    required_options = {
        "diagnosis": (
            "cpu_caution",
            "cpu_warning",
            "memory_caution",
            "memory_warning",
            "disk_caution",
            "disk_warning",
            "cpu_temperature_caution",
            "cpu_temperature_warning",
        ),
        "retention": (
            "json_hours",
            "html_hours",
        ),
        "monitoring": (
            "interval_seconds",
        ),
    }

    for section, options in required_options.items():
        for option in options:
            if not config.has_option(section, option):
                raise ValueError(
                    f"設定項目が見つかりません: "
                    f"[{section}] {option}"
                )

    # ==========================================================
    # パーセント系閾値
    # ==========================================================

    validate_percentage_threshold(
        config,
        "CPU使用率",
        "cpu_caution",
        "cpu_warning",
    )

    validate_percentage_threshold(
        config,
        "メモリ使用率",
        "memory_caution",
        "memory_warning",
    )

    validate_percentage_threshold(
        config,
        "ディスク使用率",
        "disk_caution",
        "disk_warning",
    )

    # ==========================================================
    # 温度系閾値
    # ==========================================================

    validate_temperature_threshold(
        config,
        "CPU温度",
        "cpu_temperature_caution",
        "cpu_temperature_warning",
    )

    # ==========================================================
    # 保存期間
    # ==========================================================

    validate_retention(
        config,
        "json_hours",
        "JSONログ",
    )

    validate_retention(
        config,
        "html_hours",
        "HTMLレポート",
    )

    # ==========================================================
    # 監視間隔
    # ==========================================================

    validate_monitoring_interval(
        config,
    )
    

def save_migrated_config(
    config: configparser.ConfigParser,
) -> None:
    """
    マイグレーション済み設定を安全に保存する。
    """

    backup_file = CONFIG_FILE.with_suffix(
        ".ini.bak"
    )

    if not backup_file.exists():
        shutil.copy2(
            CONFIG_FILE,
            backup_file,
        )

    fd, temp_path = tempfile.mkstemp(
        prefix="config_",
        suffix=".tmp",
        dir=CONFIG_FILE.parent,
    )

    try:
        with os.fdopen(
            fd,
            "w",
            encoding="utf-8",
        ) as file:
            config.write(file)

        os.replace(
            temp_path,
            CONFIG_FILE,
        )

    except Exception:
        try:
            os.unlink(temp_path)
        except OSError:
            pass

        raise


def load_config() -> configparser.ConfigParser:
    """
    config.iniを読み込み、
    不足設定を自動補完した上で
    バリデーション済みの設定オブジェクトを返す。
    """

    config = configparser.ConfigParser()

    if not CONFIG_FILE.exists():
        raise FileNotFoundError(
            f"設定ファイルが見つかりません: {CONFIG_FILE}"
        )

    try:
        config.read(
            CONFIG_FILE,
            encoding="utf-8",
        )

        # ======================================================
        # 設定マイグレーション
        # ======================================================

        if migrate_config(config):
            save_migrated_config(config)

        # ======================================================
        # 通常の設定検証
        # ======================================================

        validate_config(config)

    except configparser.Error as e:
        raise ValueError(
            f"config.iniの読み込みに失敗しました: {e}"
        ) from e

    return config


def get_int(
    section: str,
    option: str,
) -> int:
    """
    config.iniから整数値を取得する。

    load_config()内でバリデーション済みの値を返す。
    """

    config = load_config()

    try:
        return config.getint(
            section,
            option,
        )
    except (configparser.NoSectionError, configparser.NoOptionError) as e:
        raise ValueError(
            f"設定項目が見つかりません: "
            f"[{section}] {option}"
        ) from e

    except ValueError as e:
        raise ValueError(
            f"設定値は整数で指定してください: "
            f"[{section}] {option}"
        ) from e
