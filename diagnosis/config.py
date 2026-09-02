import configparser

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


def load_config() -> configparser.ConfigParser:
    """
    config.iniを読み込み、
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
