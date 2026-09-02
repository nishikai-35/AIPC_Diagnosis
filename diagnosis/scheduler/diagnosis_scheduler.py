import argparse

from apscheduler.schedulers.blocking import BlockingScheduler
from app import run_diagnosis_process


def scheduled_diagnosis():
    """
    定期診断を1回実行する。
    """

    print()
    print("=" * 60)
    print("定期診断を開始します")
    print("=" * 60)

    try:
        (
            info,
            memory_processes,
            cpu_processes,
            diagnosis,
            ai_analysis,
            log_path,
        ) = run_diagnosis_process()

        print()
        print("=" * 60)
        print("定期診断完了")
        print("=" * 60)

        print(f"診断結果 : {diagnosis.status}")
        print(f"JSON     : {log_path}")

        print("=" * 60)

    except Exception as e:
        import traceback

        print()
        print("=" * 60)
        print("定期診断でエラーが発生しました")
        print("=" * 60)

        print(f"エラー: {e}")
        print()
        print("詳細:")

        traceback.print_exc()

        print("=" * 60)


def main(test_mode=False):
    """
    APSchedulerを起動する。

    test_mode=True:
        1分ごと

    test_mode=False:
        毎日 09:00 / 21:00
    """

    print()
    print("=" * 60)
    print("       AI PC Diagnosis Scheduler")
    print("=" * 60)

    # ----------------------------------------
    # 起動時に1回だけ診断
    # ----------------------------------------

    print("初回診断を開始します")

    scheduled_diagnosis()

    # ----------------------------------------
    # スケジューラ作成
    # ----------------------------------------

    scheduler = BlockingScheduler()

    # ----------------------------------------
    # テストモード
    # ----------------------------------------

    if test_mode:

        scheduler.add_job(
            scheduled_diagnosis,
            "interval",
            minutes=1,
            id="scheduled_diagnosis_test",
            max_instances=1,
            coalesce=True,
        )

        schedule_message = (
            "テストモード：1分ごとに定期診断します"
        )

    # ----------------------------------------
    # 本番モード
    # ----------------------------------------

    else:

        scheduler.add_job(
            scheduled_diagnosis,
            "cron",
            hour="9,21",
            minute=0,
            id="scheduled_diagnosis",
            max_instances=1,
            coalesce=True,
        )

        schedule_message = (
            "本番モード：毎日 09:00 と 21:00 に定期診断します"
        )

    # ----------------------------------------
    # 起動メッセージ
    # ----------------------------------------

    print()
    print("スケジューラを起動しました")
    print(schedule_message)
    print("終了する場合は Ctrl + C")
    print("=" * 60)

    # ----------------------------------------
    # スケジューラ開始
    # ----------------------------------------

    try:

        scheduler.start()

    except (KeyboardInterrupt, SystemExit):

        print()
        print("スケジューラを終了しました")


if __name__ == "__main__":

    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--test",
        action="store_true",
        help="定期診断テスト：1分ごとに実行する",
    )

    args = parser.parse_args()

    main(test_mode=args.test)
