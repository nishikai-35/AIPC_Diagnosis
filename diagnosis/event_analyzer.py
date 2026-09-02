def analyze_event_logs(events):
    """
    Windowsイベントログを分析する
    """

    if not events:
        return {
            "status": "正常",
            "severity": "なし",
            "severity_counts": {
                "高": 0,
                "中": 0,
                "低": 0,
            },
            "message": "Windowsイベントログに問題は検出されませんでした。",
            "causes": [],
            "recommendations": [],
        }

    error_events = [
        event
        for event in events
        if event.get("LevelDisplayName") == "Error"
    ]

    warning_events = [
        event
        for event in events
        if event.get("LevelDisplayName") == "Warning"
    ]

    causes = []
    recommendations = []

    # ----------------------------------------
    # イベントの重要度を集計
    # ----------------------------------------

    severity_counts = {
        "高": 0,
        "中": 0,
        "低": 0,
    }

    for event in events:
        provider = event.get("ProviderName")
        event_id = event.get("Id")

        severity = get_event_severity(
            provider,
            event_id,
        )

        if severity in severity_counts:
            severity_counts[severity] += 1

    # ----------------------------------------
    # 全体の重要度を判定
    # ----------------------------------------

    if severity_counts["高"] > 0:
        overall_severity = "高"
    elif severity_counts["中"] > 0:
        overall_severity = "中"
    elif severity_counts["低"] > 0:
        overall_severity = "低"
    else:
        overall_severity = "なし"

    # ----------------------------------------
    # 件数
    # ----------------------------------------

    if error_events:
        causes.append(
            f"Windowsイベントログで"
            f"{len(error_events)}件のエラーが検出されました"
        )

    if warning_events:
        causes.append(
            f"Windowsイベントログで"
            f"{len(warning_events)}件の警告が検出されました"
        )

    # ----------------------------------------
    # 重要度件数
    # ----------------------------------------

    if severity_counts["高"] > 0:
        causes.append(
            f"重要度「高」のイベントが"
            f"{severity_counts['高']}件検出されました"
        )

    if severity_counts["中"] > 0:
        causes.append(
            f"重要度「中」のイベントが"
            f"{severity_counts['中']}件検出されました"
        )

    if severity_counts["低"] > 0:
        causes.append(
            f"重要度「低」のイベントが"
            f"{severity_counts['低']}件検出されました"
        )

    # ----------------------------------------
    # イベントごとの発生回数を集計
    # ----------------------------------------

    event_counts = {}

    for event in events:
        provider = event.get("ProviderName")
        event_id = event.get("Id")

        key = (provider, event_id)

        event_counts[key] = event_counts.get(key, 0) + 1

    # ----------------------------------------
    # イベントごとの診断
    # ----------------------------------------

    for (provider, event_id), count in event_counts.items():

        diagnosis = get_event_diagnosis(
            provider,
            event_id,
        )

        severity = get_event_severity(
            provider,
            event_id,
        )

        if diagnosis:
            causes.append(
                f"[重要度:{severity}] "
                f"{diagnosis}（{count}件）"
            )

        elif provider and event_id:
            causes.append(
                f"[重要度:{severity}] "
                f"{provider} "
                f"(Event ID: {event_id})"
                f"（{count}件）"
            )

    # ----------------------------------------
    # 推奨対策
    # ----------------------------------------

    if error_events:
        recommendations.append(
            "Windowsイベントログのエラー内容を確認してください"
        )

        recommendations.append(
            "同じエラーが繰り返し発生していないか確認してください"
        )

    if severity_counts["高"] > 0:
        recommendations.append(
            "重要度の高いイベントを優先して確認してください"
        )

    if warning_events:
        recommendations.append(
            "警告が継続的に発生している場合は原因を確認してください"
        )

    # ----------------------------------------
    # 総合判定
    # ----------------------------------------

    if severity_counts["高"] > 0:
        status = "警告"
        message = (
            "Windowsイベントログに重要度の高い"
            "問題が検出されています。"
        )

    elif error_events:
        status = "警告"
        message = (
            "Windowsイベントログにエラーが検出されています。"
        )

    elif warning_events:
        status = "注意"
        message = (
            "Windowsイベントログに警告が検出されています。"
        )

    else:
        status = "正常"
        message = (
            "Windowsイベントログに重大な問題は検出されませんでした。"
        )

    return {
        "status": status,
        "severity": overall_severity,
        "severity_counts": severity_counts,
        "message": message,
        "causes": causes,
        "recommendations": recommendations,
    }


def get_event_diagnosis(provider, event_id):
    """
    Provider / Event IDから
    Windowsイベントの意味を判定する
    """

    # Windows Update
    if (
        provider == "Microsoft-Windows-WindowsUpdateClient"
        and event_id == 20
    ):
        return (
            "Windows Updateのインストールに失敗しています"
        )

    # Application Hang
    if (
        provider == "Application Hang"
        and event_id == 1002
    ):
        return (
            "アプリケーションが応答しなくなっています"
        )

    # Application Error
    if (
        provider == "Application Error"
        and event_id == 1000
    ):
        return (
            "アプリケーションのクラッシュが発生しています"
        )

    # DistributedCOM
    if (
        provider == "Microsoft-Windows-DistributedCOM"
        and event_id == 10016
    ):
        return (
            "DistributedCOMのアクセス許可に関する警告が発生しています"
        )

    # Edge
    if (
        provider == "Edge"
        and event_id == 257
    ):
        return (
            "Microsoft Edgeの認証処理に関する警告が発生しています"
        )

    # Service Control Manager
    if (
        provider == "Service Control Manager"
        and event_id == 7011
    ):
        return (
            "Windowsサービスの応答がタイムアウトしています"
        )

    # Intel Wi-Fi
    if (
        provider == "Netwtw10"
        and event_id == 6062
    ):
        return (
            "Intel無線LANドライバー関連の警告が発生しています"
        )

    # Windows shutdown
    if (
        provider == "winsrvext"
        and event_id == 100
    ):
        return (
            "Windows終了時にアプリケーションの終了処理が遅延しています"
        )

    # TCP/IP
    if (
        provider == "Tcpip"
        and event_id == 4266
    ):
        return (
            "TCP/IPで利用可能なUDPポートが不足しています"
        )

    return None


def get_event_severity(provider, event_id):
    """
    Provider / Event IDからイベントの重要度を判定する

    戻り値:
        "高"
        "中"
        "低"
    """

    # ----------------------------------------
    # 高重要度
    # ----------------------------------------

    if (
        provider == "Application Error"
        and event_id == 1000
    ):
        return "高"

    if (
        provider == "Application Hang"
        and event_id == 1002
    ):
        return "高"

    if (
        provider == "Service Control Manager"
        and event_id == 7011
    ):
        return "高"


    # ----------------------------------------
    # 中重要度
    # ----------------------------------------

    if (
        provider == "Microsoft-Windows-WindowsUpdateClient"
        and event_id == 20
    ):
        return "中"

    if (
        provider == "Netwtw10"
        and event_id == 6062
    ):
        return "中"

    if (
        provider == "winsrvext"
        and event_id == 100
    ):
        return "中"

    if (
        provider == "Tcpip"
        and event_id == 4266
    ):
        return "中"


    # ----------------------------------------
    # 低重要度
    # ----------------------------------------

    if (
        provider == "Microsoft-Windows-DistributedCOM"
        and event_id == 10016
    ):
        return "低"

    if (
        provider == "Edge"
        and event_id == 257
    ):
        return "低"


    # ----------------------------------------
    # 未登録
    # ----------------------------------------

    return "中"