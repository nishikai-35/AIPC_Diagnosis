from graphviz import Digraph

# ---------------------------------------------------------
# AIPC_Diagnosis 専用フローチャート自動生成スクリプト
# ---------------------------------------------------------

dot = Digraph(comment='AIPC Diagnosis Tool Flow')
dot.attr(rankdir='TB', size='8,10')  # 縦方向のフローに最適化

# ---------------------------------------------------------
# ノード定義（あなたのプロジェクト構造に合わせて最適化）
# ---------------------------------------------------------

# 起動
dot.node('A', 'Start (app.py)\n起動・初期化')

# 設定読み込み
dot.node('B', 'Load Config\n(config.ini / diagnosis.config)')

# 診断エンジン
dot.node('C', 'Diagnosis Engine\n(diagnosis_engine.py)\nハードウェア・SMART・プロセス監視')

# システム情報取得
dot.node('D', 'Collect System Info\n(system_info.py / hardware_monitor.py)')

# イベントログ解析
dot.node('E', 'Event Log Analyzer\n(event_analyzer.py)')

# 条件分岐（AI ON/OFF）
dot.node('F', 'AI Enabled?\n(config.ai_enabled)')

# AI 分析
dot.node('G', 'AI Analysis\n(ai/ai_analyzer.py)\nGemma / Ollama')

# レポート生成
dot.node('H', 'Generate Report\n(report/html_report.py)')

# GUI 表示（任意）
dot.node('I', 'GUI Dashboard\n(gui_main.py / dashboard.py)')

# 終了
dot.node('J', 'End')

# ---------------------------------------------------------
# フロー定義（あなたの処理順に合わせて最適化）
# ---------------------------------------------------------

dot.edge('A', 'B')
dot.edge('B', 'C')
dot.edge('C', 'D')
dot.edge('D', 'E')
dot.edge('E', 'F')

# AI ON → AI 分析 → レポート
dot.edge('F', 'G', label='AI ON')
dot.edge('G', 'H')

# AI OFF → レポートへ直行
dot.edge('F', 'H', label='AI OFF')

# レポート → GUI（任意）
dot.edge('H', 'I', label='GUI Mode')

# 終了
dot.edge('I', 'J')

# ---------------------------------------------------------
# 出力（docs フォルダに保存）
# ---------------------------------------------------------

dot.render('docs/diagnosis_flowchart', format='png', cleanup=True)

print("✔ フローチャートを docs/diagnosis_flowchart.png に生成しました。")
