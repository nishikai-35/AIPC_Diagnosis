import argparse

from diagnosis.analyzer import analyze_system
from diagnosis.system_info import get_system_info
from diagnosis.smart_monitor import get_smart_info
from diagnosis.diagnosis_engine import run_diagnosis
from diagnosis.report.html_report import export_html
from diagnosis.event_log import get_windows_event_logs
from diagnosis.logger.diagnosis_logger import save_diagnosis_log
from diagnosis.ai.ai_analyzer import analyze_with_ai
from diagnosis.path_utils import REPORTS_DIR

from diagnosis.process_monitor import (
    get_top_memory_processes,
    get_top_cpu_processes,
)


def print_system_info(info):
    print("=" * 60)
    print("                 AI PC Diagnosis")
    print("=" * 60)

    print("\n[OS]")
    print(f"OS              : {info['os']}")
    print(f"OS Version      : {info['os_version']}")
    print(f"Machine         : {info['machine']}")

    print("\n[CPU]")
    print(f"CPU             : {info['cpu']}")
    print(f"Physical Cores  : {info['physical_cores']}")
    print(f"Logical Cores   : {info['logical_cores']}")
    print(f"CPU Usage       : {info['cpu_usage']:.1f} %")

    if info["cpu_temperature"] is not None:
        print(f"CPU Temperature : {info['cpu_temperature']:.1f} °C")
    else:
        print("CPU Temperature : 取得できません")

    print("\n[Memory]")
    print(f"Total           : {info['memory_total']:.2f} GB")
    print(f"Used            : {info['memory_used']:.2f} GB")
    print(f"Available       : {info['memory_available']:.2f} GB")
    print(f"Usage           : {info['memory_usage']:.1f} %")

    print("\n[Disk C:]")
    print(f"Total           : {info['disk_total']:.2f} GB")
    print(f"Used            : {info['disk_used']:.2f} GB")
    print(f"Free            : {info['disk_free']:.2f} GB")
    print(f"Usage           : {info['disk_usage']:.1f} %")

    print("\n[GPU]")
    if info["gpu_usage"] is not None:
        print(f"GPU Usage       : {info['gpu_usage']:.1f} %")
    else:
        print("GPU Usage       : 取得できません")

    if info["gpu_temperature"] is not None:
        print(f"GPU Temperature : {info['gpu_temperature']:.1f} °C")
    else:
        print("GPU Temperature : 取得できません")

    print("\n[System]")
    print(f"Boot Time       : {info['boot_time']}")

    print("\n" + "=" * 60)


def print_diagnosis(diagnosis):
    print("\n" + "=" * 60)
    print("                 診断結果")
    print("=" * 60)

    print(f"\n総合評価：{diagnosis.status}")
    print(f"総合説明：{diagnosis.message}")

    if diagnosis.causes:
        print("\n主な原因:")
        for cause in diagnosis.causes:
            print(f"  - {cause}")

    if diagnosis.recommendations:
        print("\n総合推奨対策:")
        for index, recommendation in enumerate(
            diagnosis.recommendations,
            start=1,
        ):
            print(f"  {index}. {recommendation}")

    print("\n" + "-" * 60)
    print("                 個別診断")
    print("-" * 60)

    for result in diagnosis.results:
        print(f"\n[{result.item}]")
        print(f"判定    : {result.status}")

        if isinstance(result.value, (int, float)):
            print(f"数値    : {result.value:.1f}")
        elif result.value is not None:
            print(f"数値    : {result.value}")
        else:
            print("数値    : 取得できません")

        print(f"説明    : {result.message}")

        if result.causes:
            print("\n原因候補:")
            for cause in result.causes:
                print(f"  - {cause}")

        if result.recommendations:
            print("\n推奨対策:")
            for index, recommendation in enumerate(
                result.recommendations,
                start=1,
            ):
                print(f"  {index}. {recommendation}")

    print("\n" + "=" * 60)


def print_top_memory_processes(processes):
    print("\n" + "=" * 60)
    print("          メモリ使用量の多いプロセス")
    print("=" * 60)

    for index, process in enumerate(processes, start=1):
        print(
            f"{index}. "
            f"{process['name']} "
            f"(PID: {process['pid']}) "
            f"{process['memory_mb']:.1f} MB "
            f"[{process['category']}]"
        )


def print_top_cpu_processes(processes):
    print("\n" + "=" * 60)
    print("          CPU使用率の高いプロセス")
    print("=" * 60)

    for index, process in enumerate(processes, start=1):
        print(
            f"{index}. "
            f"{process['name']} "
            f"(PID: {process['pid']}) "
            f"{process['cpu_percent']:.1f} % "
            f"[{process['category']}]"
        )


def run_diagnosis_process(ai_enabled=True):
    """
    PC情報を取得して診断を実行し、
    診断結果とAI分析結果をJSONログとして保存する。
    """

    # PC情報を取得
    info = get_system_info()

    # メモリ使用量の多いプロセス
    memory_processes = get_top_memory_processes(limit=10)

    # CPU使用率の高いプロセス
    cpu_processes = get_top_cpu_processes(limit=10)

    # SMART情報
    smart_info = get_smart_info()

    # Windowsイベントログ
    event_logs = get_windows_event_logs()

    # PCを診断
    results = analyze_system(
        cpu_usage=info["cpu_usage"],
        memory_usage=info["memory_usage"],
        disk_usage=info["disk_usage"],
        cpu_temperature=info["cpu_temperature"],
        gpu_usage=info["gpu_usage"],
        gpu_temperature=info["gpu_temperature"],
        memory_processes=memory_processes,
        cpu_processes=cpu_processes,
        smart_info=smart_info,
        event_logs=event_logs,
    )

    # 総合診断
    diagnosis = run_diagnosis(results)

    # AI分析
    if ai_enabled:
        ai_analysis = analyze_with_ai(diagnosis)
    else:
        ai_analysis = None

    # JSONログ保存
    log_path = save_diagnosis_log(
        results,
        ai_analysis,
    )

    return (
        info,
        memory_processes,
        cpu_processes,
        diagnosis,
        ai_analysis,
        log_path,
    )


def main(scheduled=False, ai_enabled=True):

    (
        info,
        memory_processes,
        cpu_processes,
        diagnosis,
        ai_analysis,
        log_path,
    ) = run_diagnosis_process(
        ai_enabled=ai_enabled
    )

    # ============================================================
    # AI分析結果
    # ============================================================

    if ai_analysis is not None:

        print()
        print("=" * 60)
        print("                 AI分析結果")
        print("=" * 60)

        print("\n概要:")
        print(f"  {ai_analysis.summary}")

        print("\n優先度:")
        print(f"  {ai_analysis.priority}")

        if ai_analysis.causes:
            print("\nAI分析による原因:")

            for cause in ai_analysis.causes:
                print(f"  - {cause}")

        if ai_analysis.recommendations:
            print("\nAI分析による推奨対策:")

            for recommendation in ai_analysis.recommendations:
                print(f"  - {recommendation}")

        print("=" * 60)

    else:

        print()
        print("=" * 60)
        print("                 AI分析")
        print("=" * 60)
        print("AI分析：無効")
        print("=" * 60)

    # ============================================================
    # 手動実行時は詳細情報を表示
    # ============================================================

    if not scheduled:

        print_system_info(info)

        print_top_memory_processes(
            memory_processes
        )

        print_top_cpu_processes(
            cpu_processes
        )

    # ============================================================
    # 診断結果を表示
    # ============================================================

    print_diagnosis(
        diagnosis
    )

    # ============================================================
    # 手動実行時のみHTMLを出力
    # ============================================================

    if not scheduled:

        html_path = export_html(
            diagnosis,
            ai_analysis,
            REPORTS_DIR,
        )

        print()
        print("=" * 60)
        print("レポート出力完了")
        print("=" * 60)

        print(f"JSON: {log_path}")
        print(f"HTML: {html_path}")

        print("=" * 60)

    else:

        print()
        print("=" * 60)
        print("定期診断完了")
        print("=" * 60)

        print(f"JSON: {log_path}")

        print("=" * 60)



if __name__ == "__main__":

    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--scheduled",
        action="store_true",
        help="定期診断モードで実行する",
    )

    parser.add_argument(
        "--no-ai",
        action="store_true",
        help="AI分析を無効にする",
    )

    args = parser.parse_args()

    main(
        scheduled=args.scheduled,
        ai_enabled=not args.no_ai,
    )

