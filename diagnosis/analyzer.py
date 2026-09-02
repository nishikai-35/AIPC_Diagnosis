from dataclasses import dataclass

from diagnosis.event_analyzer import analyze_event_logs
from diagnosis.config import get_int


# ==========================================================
# 診断閾値
# config.iniから読み込む
# ==========================================================

CPU_CAUTION = get_int("diagnosis", "cpu_caution")
CPU_WARNING = get_int("diagnosis", "cpu_warning")

MEMORY_CAUTION = get_int("diagnosis", "memory_caution")
MEMORY_WARNING = get_int("diagnosis", "memory_warning")

DISK_CAUTION = get_int("diagnosis", "disk_caution")
DISK_WARNING = get_int("diagnosis", "disk_warning")

CPU_TEMPERATURE_CAUTION = get_int(
    "diagnosis",
    "cpu_temperature_caution",
)

CPU_TEMPERATURE_WARNING = get_int(
    "diagnosis",
    "cpu_temperature_warning",
)


@dataclass
class DiagnosisResult:
    item: str
    status: str
    value: float | str | None
    message: str
    causes: list[str]
    recommendations: list[str]


def get_memory_process_causes(processes, limit=3):
    causes = []

    application_processes = [
        process
        for process in processes
        if process.get("category") == "アプリケーション"
    ]

    for process in application_processes[:limit]:
        name = process["name"]
        memory_mb = process["memory_mb"]

        if memory_mb >= 500:
            causes.append(
                f"{name} が約{memory_mb:.0f}MBのメモリを使用しています"
            )

    return causes


def get_cpu_process_causes(processes, limit=3):
    causes = []

    application_processes = [
        process
        for process in processes
        if process.get("category") == "アプリケーション"
    ]

    significant_processes = [
        process
        for process in application_processes
        if process.get("cpu_percent", 0) >= 10
    ]

    for process in significant_processes[:limit]:
        name = process["name"]
        cpu_percent = process["cpu_percent"]

        causes.append(
            f"{name} が約{cpu_percent:.1f}%のCPUを使用しています"
        )

    return causes


def analyze_cpu(
    usage: float,
    processes=None,
) -> DiagnosisResult:

    if processes is None:
        processes = []

    process_causes = get_cpu_process_causes(processes)

    if usage >= CPU_WARNING:
        causes = [
            "CPU負荷の高いアプリケーションが実行されている可能性があります",
            "バックグラウンド処理がCPUを大量に使用している可能性があります",
            "複数のアプリケーションが同時にCPUを使用している可能性があります",
        ]

        causes.extend(process_causes)

        return DiagnosisResult(
            item="CPU",
            status="警告",
            value=usage,
            message="CPU使用率が非常に高い状態です。",
            causes=causes,
            recommendations=[
                "タスクマネージャーでCPU使用率の高いプロセスを確認してください",
                "使用していないアプリケーションを終了してください",
                "CPU使用率が長時間高い場合は、原因となっているアプリケーションを調査してください",
            ],
        )

    if usage >= CPU_CAUTION:
        causes = [
            "アプリケーションによる一時的なCPU負荷の可能性があります",
            "バックグラウンドで処理が実行されている可能性があります",
        ]

        causes.extend(process_causes)

        return DiagnosisResult(
            item="CPU",
            status="注意",
            value=usage,
            message="CPU使用率が高めです。",
            causes=causes,
            recommendations=[
                "使用していないアプリケーションを終了してください",
                "タスクマネージャーでCPU使用率を確認してください",
            ],
        )

    return DiagnosisResult(
        item="CPU",
        status="正常",
        value=usage,
        message="CPU使用率に問題は見られません。",
        causes=[],
        recommendations=[],
    )


def analyze_memory(usage: float, processes=None) -> DiagnosisResult:
    
    if processes is None:
        processes = []
        
    process_causes = get_memory_process_causes(processes)
    
    if usage >= MEMORY_WARNING:
        causes = [
            "多数のアプリケーションが同時に実行されている可能性があります",
            "ブラウザや常駐アプリケーションが大量のメモリを使用している可能性があります",
            "搭載メモリ容量が現在の利用状況に対して不足している可能性があります",
        ]

        causes.extend(process_causes)

        return DiagnosisResult(
            item="メモリ",
            status="警告",
            value=usage,
            message="メモリ使用率が非常に高い状態です。",
            causes=causes,
            
            recommendations=[
                "使用していないアプリケーションを終了してください",
                "不要なブラウザタブを閉じてください",
                "タスクマネージャーでメモリ使用量の多いアプリケーションを確認してください",
                "頻繁に発生する場合はメモリ増設を検討してください",
            ],
        )

    if usage >= MEMORY_CAUTION:
        causes = [
            "複数のアプリケーションが同時にメモリを使用している可能性があります",
            "ブラウザのタブや常駐アプリケーションがメモリを消費している可能性があります",
        ]
    
        causes.extend(process_causes)
    
        return DiagnosisResult(
            item="メモリ",
            status="注意",
            value=usage,
            message="メモリ使用率が高めです。",
            causes=causes,
        
            recommendations=[
                "使用していないアプリケーションを終了してください",
                "不要なブラウザタブを閉じてください",
                "タスクマネージャーでメモリ使用量を確認してください",
            ],
        )

    return DiagnosisResult(
        item="メモリ",
        status="正常",
        value=usage,
        message="メモリ使用率に大きな問題は見られません。",
        causes=[],
        recommendations=[],
    )


def analyze_disk(usage: float) -> DiagnosisResult:
    if usage >= DISK_WARNING:
        return DiagnosisResult(
            item="ディスク",
            status="警告",
            value=usage,
            message="ディスクの空き容量が非常に少なくなっています。",
            causes=[
                "大量のファイルやアプリケーションが保存されている可能性があります",
                "一時ファイルや不要なファイルが蓄積している可能性があります",
                "ディスク容量そのものが不足している可能性があります",
            ],
            recommendations=[
                "不要なファイルを削除してください",
                "ごみ箱を空にしてください",
                "不要なアプリケーションをアンインストールしてください",
                "必要に応じて大容量ファイルを別のストレージへ移動してください", 
            ],
        )

    if usage >= DISK_CAUTION:
        return DiagnosisResult(
            item="ディスク",
            status="注意",
            value=usage,
            message="ディスク使用率が高くなっています。",
            causes=[
                "不要なファイルが蓄積している可能性があります",
                "アプリケーションや動画などの大容量ファイルが増えている可能性があります",
            ],
            recommendations=[
                "不要なファイルを整理してください",
                "ごみ箱を確認してください",
                "不要なアプリケーションをアンインストールしてください",
            ],
        )

    return DiagnosisResult(
        item="ディスク",
        status="正常",
        value=usage,
        message="ディスク容量に問題は見られません。",
        causes=[],
        recommendations=[],
    )
    
    
def analyze_cpu_temperature(temperature: float) -> DiagnosisResult:
    """
    CPU温度を診断する
    """

    if temperature >= CPU_TEMPERATURE_WARNING:
        return DiagnosisResult(
            item="CPU温度",
            status="警告",
            value=temperature,
            message="CPU温度が非常に高い状態です。",
            causes=[
                "CPUに高い負荷がかかっている可能性があります",
                "CPUクーラーの冷却性能が不足している可能性があります",
                "CPUクーラーやヒートシンクにホコリが蓄積している可能性があります",
                "PC内部のエアフローが十分でない可能性があります",
            ],
            recommendations=[
                "CPU使用率の高いプロセスを確認してください",
                "PC内部のホコリを確認してください",
                "CPUクーラーの動作を確認してください",
                "PC内部のエアフローを確認してください",
            ],
        )

    if temperature >= CPU_TEMPERATURE_CAUTION:
        return DiagnosisResult(
            item="CPU温度",
            status="注意",
            value=temperature,
            message="CPU温度が高めです。",
            causes=[
                "CPUに比較的高い負荷がかかっている可能性があります",
                "冷却性能が低下している可能性があります",
            ],
            recommendations=[
                "CPU使用率の高いアプリケーションを確認してください",
                "長時間高温が続く場合は冷却状態を確認してください",
            ],
        )

    return DiagnosisResult(
        item="CPU温度",
        status="正常",
        value=temperature,
        message="CPU温度に問題は見られません。",
        causes=[],
        recommendations=[],
    )
    
    
def analyze_gpu_temperature(temperature: float) -> DiagnosisResult:
    """
    GPU温度を診断する
    """

    if temperature >= 90:
        return DiagnosisResult(
            item="GPU温度",
            status="警告",
            value=temperature,
            message="GPU温度が非常に高い状態です。",
            causes=[
                "GPUに高い負荷がかかっている可能性があります",
                "GPUファンやヒートシンクの冷却性能が低下している可能性があります",
                "GPU周辺のエアフローが十分でない可能性があります",
            ],
            recommendations=[
                "GPU使用率を確認してください",
                "GPUファンの動作を確認してください",
                "PC内部のホコリを確認してください",
                "長時間高温が続く場合は冷却環境を確認してください",
            ],
        )

    if temperature >= 80:
        return DiagnosisResult(
            item="GPU温度",
            status="注意",
            value=temperature,
            message="GPU温度が高めです。",
            causes=[
                "GPUに比較的高い負荷がかかっている可能性があります",
                "GPUの冷却性能が低下している可能性があります",
            ],
            recommendations=[
                "GPU使用率を確認してください",
                "長時間高温が続く場合は冷却状態を確認してください",
            ],
        )

    return DiagnosisResult(
        item="GPU温度",
        status="正常",
        value=temperature,
        message="GPU温度に問題は見られません。",
        causes=[],
        recommendations=[],
    )


def analyze_smart(smart_info) -> DiagnosisResult:
    """
    NVMe SSDのSMART情報を診断する
    """

    # SMART情報を取得できなかった場合
    if not smart_info:
        return DiagnosisResult(
            item="ストレージSMART",
            status="注意",
            value=None,
            message="ストレージのSMART情報を取得できませんでした。",
            causes=[
                "SMART情報を取得できない可能性があります",
                "ストレージまたはドライバがSMART情報へのアクセスを制限している可能性があります",
            ],
            recommendations=[
                "ストレージの接続状態を確認してください",
                "SMART情報を取得できる環境か確認してください",
            ],
        )

    # SMART情報取得
    health = smart_info.get("health")
    critical_warning = smart_info.get("critical_warning")
    temperature = smart_info.get("temperature")
    available_spare = smart_info.get("available_spare")
    percentage_used = smart_info.get("percentage_used")
    media_errors = smart_info.get("media_errors")
    error_log_entries = smart_info.get("error_log_entries")

    causes = []
    recommendations = []

    # ==========================================================
    # 原因・推奨対策
    # ==========================================================

    # SMART Health FAILED
    if health is not None and health.upper() == "FAILED":
        causes.append(
            "SSDのSMART自己診断で異常が検出されています"
        )

        recommendations.append(
            "重要なデータを速やかにバックアップしてください"
        )

        recommendations.append(
            "SSDの交換を検討してください"
        )

    # Critical Warning
    if critical_warning and critical_warning != "0x00":
        causes.append(
            f"NVMe SSDでCritical Warningが検出されています（{critical_warning}）"
        )

        recommendations.append(
            "重要なデータをバックアップしてください"
        )

    # Media Errors
    if media_errors is not None and media_errors > 0:
        causes.append(
            f"メディアエラーが{media_errors:.0f}件検出されています"
        )

        recommendations.append(
            "重要なデータをバックアップし、SSDの状態を継続的に確認してください"
        )

    # Error Log
    if error_log_entries is not None and error_log_entries > 0:
        causes.append(
            f"NVMeエラーログが{error_log_entries:.0f}件記録されています"
        )

        recommendations.append(
            "エラーログの増加がないか継続的に確認してください"
        )

    # Temperature
    if temperature is not None and temperature >= 80:
        causes.append(
            f"SSD温度が{temperature:.0f}℃と高くなっています"
        )

        recommendations.append(
            "SSD周辺の冷却状態とPC内部のエアフローを確認してください"
        )

    elif temperature is not None and temperature >= 70:
        causes.append(
            f"SSD温度が{temperature:.0f}℃とやや高めです"
        )

        recommendations.append(
            "長時間高温が続く場合はSSDの冷却状態を確認してください"
        )

    # Available Spare
    if available_spare is not None and available_spare < 10:
        causes.append(
            f"Available Spareが{available_spare:.0f}%まで低下しています"
        )

        recommendations.append(
            "SSDの状態を確認し、必要に応じて交換を検討してください"
        )

    elif available_spare is not None and available_spare < 20:
        causes.append(
            f"Available Spareが{available_spare:.0f}%と低下しています"
        )

        recommendations.append(
            "SSDの状態を継続的に監視してください"
        )

    # Percentage Used
    if percentage_used is not None and percentage_used >= 90:
        causes.append(
            f"SSDの推定使用率が{percentage_used:.0f}%に達しています"
        )

        recommendations.append(
            "SSDの交換を検討してください"
        )

    elif percentage_used is not None and percentage_used >= 80:
        causes.append(
            f"SSDの推定使用率が{percentage_used:.0f}%と高くなっています"
        )

        recommendations.append(
            "SSDの状態を継続的に監視してください"
        )

    # ==========================================================
    # 総合判定
    # ==========================================================

    # 重大な異常
    if health is not None and health.upper() == "FAILED":
        status = "警告"
        message = "NVMe SSDのSMART健康状態がFAILEDです。"

    elif critical_warning and critical_warning != "0x00":
        status = "警告"
        message = "NVMe SSDで重大な警告が検出されています。"

    elif media_errors is not None and media_errors > 0:
        status = "警告"
        message = "NVMe SSDでメディアエラーが検出されています。"

    elif percentage_used is not None and percentage_used >= 90:
        status = "警告"
        message = "NVMe SSDの推定使用率が非常に高くなっています。"

    elif temperature is not None and temperature >= 80:
        status = "警告"
        message = "NVMe SSDの温度が非常に高い状態です。"

    elif available_spare is not None and available_spare < 10:
        status = "警告"
        message = "NVMe SSDのAvailable Spareが低下しています。"

    # 注意
    elif percentage_used is not None and percentage_used >= 80:
        status = "注意"
        message = "NVMe SSDの推定使用率が高くなっています。"

    elif temperature is not None and temperature >= 70:
        status = "注意"
        message = "NVMe SSDの温度がやや高めです。"

    elif available_spare is not None and available_spare < 20:
        status = "注意"
        message = "NVMe SSDのAvailable Spareが低下しています。"

    elif error_log_entries is not None and error_log_entries > 0:
        status = "注意"
        message = "NVMe SSDにエラーログが記録されています。"

    # 正常
    else:
        status = "正常"
        message = "NVMe SSDの健康状態に問題は見られません。"

    return DiagnosisResult(
        item="ストレージSMART",
        status=status,
        value=percentage_used,
        message=message,
        causes=causes,
        recommendations=recommendations,
    )
    

def analyze_system(
    cpu_usage,
    memory_usage,
    disk_usage,
    cpu_temperature=None,
    gpu_usage=None,
    gpu_temperature=None,
    memory_processes=None,
    cpu_processes=None,
    smart_info=None,
    event_logs=None,
):
    results = [
        analyze_cpu(cpu_usage, cpu_processes),
        analyze_memory(memory_usage, memory_processes),
        analyze_disk(disk_usage),
    ]

    if cpu_temperature is not None:
        results.append(
            analyze_cpu_temperature(cpu_temperature)
        )

    if gpu_temperature is not None:
        results.append(
            analyze_gpu_temperature(gpu_temperature)
        )
        
    if smart_info is not None:
        results.append(
            analyze_smart(smart_info)
        )

    if event_logs is not None:
        event_result = analyze_event_logs(event_logs)
    
        results.append(
            DiagnosisResult(
                item="Windowsイベントログ",
                status=event_result["status"],
                value=len(event_logs),
                message=event_result["message"],
                causes=event_result["causes"],
                recommendations=event_result["recommendations"],
            )
        )

    if any(result.status == "警告" for result in results):
        overall_status = "警告"
    elif any(result.status == "注意" for result in results):
        overall_status = "注意"
    else:
        overall_status = "正常"

    return results
