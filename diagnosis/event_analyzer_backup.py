def analyze_event_logs(events):
    """
    Windowsイベントログを分析する
    """

    if not events:
        return {
            "status": "正常",
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
    # 件数
    # ----------------------------------------

    if error_events:
        causes.append(
            f"Windowsイベントログで{len(error_events)}件のエラーが検出されました"
        )

    if warning_events:
        causes.append(
            f"Windowsイベントログで{len(warning_events)}件の警告が検出されました"
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

        if diagnosis:
            causes.append(
                f"{diagnosis}（{count}件）"
            )

        elif provider and event_id:
            causes.append(
                f"{provider} (Event ID: {event_id})（{count}件）"
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

    if warning_events:
        recommendations.append(
            "警告が継続的に発生している場合は原因を確認してください"
        )

    # ----------------------------------------
    # 総合判定
    # ----------------------------------------

    if error_events:
        status = "警告"
    elif warning_events:
        status = "注意"
    else:
        status = "正常"

    return {
        "status": status,
        "message": (
            "Windowsイベントログにエラーが検出されています。"
            if error_events
            else "Windowsイベントログに重大な問題は検出されませんでした。"
        ),
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