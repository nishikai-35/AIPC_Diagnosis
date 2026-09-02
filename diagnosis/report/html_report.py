from datetime import datetime, timedelta
from html import escape
from pathlib import Path

from diagnosis.config import get_int
from diagnosis.path_utils import REPORTS_DIR


# HTMLレポートの保存期間（時間）
HTML_RETENTION_HOURS = get_int(
    "retention",
    "html_hours"
)


def get_status_class(status):
    return {
        "正常": "normal",
        "注意": "caution",
        "警告": "warning",
    }.get(status, "normal")


def cleanup_old_html_files(output_dir):
    """
    保存期間を超えたHTMLレポートを削除する。

    作成から{HTML_RETENTION_HOURS}時間を超えたHTMLレポートを
    削除する。
    """

    if not output_dir.exists():
        return

    cutoff_time = datetime.now() - timedelta(
        hours=HTML_RETENTION_HOURS
    )

    html_files = output_dir.glob(
        "diagnosis_report_*.html"
    )

    for html_file in html_files:

        try:
            file_time = datetime.fromtimestamp(
                html_file.stat().st_mtime
            )

            if file_time < cutoff_time:

                html_file.unlink()

                print(
                    f"保存期間を超えたHTMLレポートを削除しました: "
                    f"{html_file}"
                )

        except OSError as e:

            print(
                f"HTMLレポートの削除に失敗しました: "
                f"{html_file}"
            )

            print(
                f"エラー: {e}"
            )


def export_html(
    diagnosis,
    ai_analysis=None,
    output_dir=REPORTS_DIR,
):
    """
    診断結果をHTMLファイルとして出力する。

    Parameters
    ----------
    diagnosis : OverallDiagnosis
        run_diagnosis() が返す総合診断結果

    output_dir : str | Path
        HTMLファイルを保存するディレクトリ

    Returns
    -------
    Path
        保存したHTMLファイルのパス
    """

    output_dir = Path(output_dir)

    # 保存先ディレクトリを作成
    output_dir.mkdir(parents=True, exist_ok=True)

    # 現在日時
    now = datetime.now()

    # CSVと同じ形式のファイル名
    filename = (
        f"diagnosis_report_"
        f"{now.strftime('%Y%m%d_%H%M%S')}.html"
    )

    output_path = output_dir / filename

    # 総合評価に応じたCSSクラス
    status_class = {
        "正常": "normal",
        "注意": "caution",
        "警告": "warning",
    }.get(diagnosis.status, "normal")
    
    # AI分析
    if ai_analysis is not None:

        ai_summary_html = escape(
            ai_analysis.summary
        )

        ai_priority = escape(
            ai_analysis.priority
        )

        ai_causes_html = ""

        for cause in ai_analysis.causes:
            ai_causes_html += (
                f"<li>{escape(cause)}</li>"
            )

        ai_recommendations_html = ""

        for recommendation in ai_analysis.recommendations:
            ai_recommendations_html += (
                f"<li>{escape(recommendation)}</li>"
            )

    else:

        ai_summary_html = "AI分析は実行されていません。"
        ai_priority = "未実行"
        ai_causes_html = "<li>なし</li>"
        ai_recommendations_html = "<li>なし</li>"
        
    ai_priority_class = get_status_class(ai_priority)


    # 原因一覧
    causes_html = ""

    for cause in diagnosis.causes:
        causes_html += f"<li>{escape(cause)}</li>"


    # 推奨対策一覧
    recommendations_html = ""

    for recommendation in diagnosis.recommendations:
        recommendations_html += (
            f"<li>{escape(recommendation)}</li>"
        )


    # 個別診断
    results_html = ""

    for result in diagnosis.results:

        result_status_class = get_status_class(
            result.status
        )

        causes = "<br>".join(
            escape(cause)
            for cause in result.causes
        )

        recommendations = "<br>".join(
            escape(recommendation)
            for recommendation in result.recommendations
        )

        value = (
            escape(str(result.value))
            if result.value is not None
            else "取得できません"
        )

        results_html += f"""
        <tr>
            <td>{escape(result.item)}</td>
            <td>
                <span class="status {result_status_class}">
                    {escape(result.status)}
                </span>
            </td>
            <td>{value}</td>
            <td>{escape(result.message)}</td>
            <td>{causes}</td>
            <td>{recommendations}</td>
        </tr>
        """

    html = f"""<!DOCTYPE html>
<html lang="ja">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">

<title>AI PC Diagnosis Report</title>
<style>
body {{
    font-family:
        -apple-system,
        BlinkMacSystemFont,
        "Segoe UI",
        sans-serif;

    background: #f5f7fa;
    color: #333;

    margin: 0;
    padding: 30px;
}}

.container {{
    max-width: 1200px;
    margin: auto;
}}

h1 {{
    margin-bottom: 5px;
}}

.timestamp {{
    color: #666;
    margin-bottom: 30px;
}}

.card {{
    background: white;
    border-radius: 10px;
    padding: 25px;
    margin-bottom: 20px;

    box-shadow:
        0 2px 8px rgba(0,0,0,0.08);
}}

.overall {{
    border-left: 6px solid;
}}

.overall.normal {{
    border-color: #28a745;
}}

.overall.caution {{
    border-color: #ffc107;
}}

.overall.warning {{
    border-color: #dc3545;
}}

.ai-analysis {{
    border-left: 6px solid #6f42c1;
}}

.ai-analysis h2 {{
    margin-top: 0;
}}

.ai-analysis h3 {{
    margin-top: 20px;
    margin-bottom: 8px;
}}

.status {{
    display: inline-block;

    padding: 4px 10px;

    border-radius: 20px;

    font-weight: bold;
}}

.status.normal {{
    background: #d4edda;
    color: #155724;
}}

.status.caution {{
    background: #fff3cd;
    color: #856404;
}}

.status.warning {{
    background: #f8d7da;
    color: #721c24;
}}

table {{
    width: 100%;
    border-collapse: collapse;
}}

th,
td {{
    padding: 12px;
    border-bottom: 1px solid #ddd;

    text-align: left;
    vertical-align: top;
}}

th {{
    background: #f0f2f5;
}}

ul {{
    line-height: 1.8;
}}

footer {{
    text-align: center;
    color: #777;
    margin-top: 30px;
}}
</style>

</head>
<body>
<div class="container">
    <h1>AI PC Diagnosis</h1>
    <div class="timestamp">
        診断日時：
        {now.strftime("%Y-%m-%d %H:%M:%S")}
    </div>

    <div class="card overall {status_class}">
        <h2>総合評価</h2>
        <p>
            <span class="status {status_class}">
                {escape(diagnosis.status)}
            </span>
        </p>
        <p>
            {escape(diagnosis.message)}
        </p>
    </div>
    
    <div class="card ai-analysis">
        <h2>AI分析</h2>

        <h3>概要</h3>

        <p>
            {ai_summary_html}
        </p>

        <h3>優先度</h3>

        <p>
            <span class="status {ai_priority_class}">
                {ai_priority}
            </span>
        </p>

        <h3>AI分析による原因</h3>

        <ul>
            {ai_causes_html}
        </ul>

        <h3>AI分析による推奨対策</h3>

        <ul>
            {ai_recommendations_html}
        </ul>
    </div>

    <div class="card">
        <h2>主な原因</h2>
        <ul>
            {causes_html}
        </ul>
    </div>


    <div class="card">
        <h2>総合推奨対策</h2>
        <ul>
            {recommendations_html}
        </ul>
    </div>

    <div class="card">
        <h2>個別診断</h2>
        <table>
            <thead>
                <tr>
                    <th>項目</th>
                    <th>判定</th>
                    <th>数値</th>
                    <th>説明</th>
                    <th>原因</th>
                    <th>推奨対策</th>
                </tr>
            </thead>
            <tbody>
                {results_html}
            </tbody>
        </table>
    </div>


    <footer>
        AI PC Diagnosis
    </footer>
</div>

</body>
</html>
"""

    # HTMLファイルを書き込む
    with open(
        output_path,
        "w",
        encoding="utf-8",
    ) as html_file:

        html_file.write(html)

    # 古いHTMLレポートを整理
    cleanup_old_html_files(output_dir)

    return output_path