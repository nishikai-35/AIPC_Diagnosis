import json
import urllib.request
from dataclasses import dataclass


# Ollamaの接続先
OLLAMA_URL = "http://127.0.0.1:11434/api/generate"

# 使用するモデル
OLLAMA_MODEL = "gemma4"

# Ollamaへのタイムアウト
OLLAMA_TIMEOUT = 300


@dataclass
class AIAnalysis:
    summary: str
    priority: str
    causes: list[str]
    recommendations: list[str]


def diagnosis_to_dict(diagnosis):
    """
    OverallDiagnosisをAI分析用の辞書に変換する。
    """

    return {
        "overall_status": diagnosis.status,
        "message": diagnosis.message,
        "causes": diagnosis.causes,
        "recommendations": diagnosis.recommendations,
        "results": [
            {
                "item": result.item,
                "status": result.status,
                "value": result.value,
                "message": result.message,
                "causes": result.causes,
                "recommendations": result.recommendations,
            }
            for result in diagnosis.results
        ],
    }


def call_ollama(prompt):
    """
    Ollamaにプロンプトを送信し、
    AIの回答文字列を取得する。
    """

    request_data = {
        "model": OLLAMA_MODEL,
        "prompt": prompt,
        "stream": False,
    }

    data = json.dumps(
        request_data,
        ensure_ascii=False,
    ).encode("utf-8")

    request = urllib.request.Request(
        OLLAMA_URL,
        data=data,
        headers={
            "Content-Type": "application/json",
        },
        method="POST",
    )

    with urllib.request.urlopen(
        request,
        timeout=OLLAMA_TIMEOUT,
    ) as response:

        response_data = json.loads(
            response.read().decode("utf-8")
        )

    return response_data["response"]


def clean_json_response(response):
    """
    AIが返したJSON文字列を整理する。

    Markdownのコードブロックが付いている場合は除去する。
    """

    response = response.strip()

    # ```json ... ``` を除去
    if response.startswith("```json"):
        response = response[len("```json"):]

    elif response.startswith("```"):
        response = response[len("```"):]

    if response.endswith("```"):
        response = response[:-3]

    return response.strip()


def validate_ai_result(result):
    """
    AIから返されたJSONの内容を検証する。
    """

    required_keys = [
        "summary",
        "priority",
        "causes",
        "recommendations",
    ]

    for key in required_keys:
        if key not in result:
            raise ValueError(
                f"AIレスポンスに必須項目がありません: {key}"
            )

    if not isinstance(result["summary"], str):
        raise ValueError(
            "summaryは文字列である必要があります。"
        )

    if result["priority"] not in (
        "正常",
        "注意",
        "警告",
    ):
        raise ValueError(
            f"priorityの値が不正です: {result['priority']}"
        )

    if not isinstance(result["causes"], list):
        raise ValueError(
            "causesは配列である必要があります。"
        )

    if not isinstance(
        result["recommendations"],
        list,
    ):
        raise ValueError(
            "recommendationsは配列である必要があります。"
        )


def analyze_with_ai(diagnosis):
    """
    診断結果をOllamaのローカルAIで分析する。
    """

    data = diagnosis_to_dict(diagnosis)

    print("\n" + "=" * 60)
    print("                 AI分析")
    print("=" * 60)

    print("OllamaによるAI分析を開始します...")
    print(f"使用モデル: {OLLAMA_MODEL}")

    prompt = f"""
あなたはPC診断を専門とするAIです。

以下のPC診断結果を分析してください。

診断結果:
{json.dumps(data, ensure_ascii=False, indent=2)}

以下の4項目について日本語で回答してください。

1. summary
PCの状態を簡潔に説明してください。

2. priority
診断結果の重要度を、
「正常」「注意」「警告」
のいずれかで回答してください。

3. causes
問題の原因を箇条書きで説明してください。

4. recommendations
ユーザーが実施すべき対策を箇条書きで説明してください。

【重要なルール】

- 診断結果に存在しない事実を断定しないでください。
- 正常な項目を不必要に問題視しないでください。
- ハードウェア故障を断定しないでください。
- Windowsイベントログの警告とエラーを区別してください。
- 原因は診断結果から考えられるものを説明してください。
- 推奨対策はユーザーが実行しやすい内容にしてください。

回答は必ず以下のJSON形式だけで返してください。

{{
  "summary": "PCの状態の概要",
  "priority": "正常",
  "causes": [
    "原因1",
    "原因2"
  ],
  "recommendations": [
    "対策1",
    "対策2"
  ]
}}

JSON以外の文章は出力しないでください。
Markdownのコードブロックも使用しないでください。
"""

    try:

        # Ollamaへ送信
        response = call_ollama(prompt)

        print("OllamaからAI分析結果を取得しました。")

        # AIが返したJSONを整理
        response = clean_json_response(response)

        # JSONとして解析
        result = json.loads(response)

        # JSON内容を検証
        validate_ai_result(result)

        # AIAnalysisへ変換
        analysis = AIAnalysis(
            summary=result["summary"],
            priority=result["priority"],
            causes=result["causes"],
            recommendations=result["recommendations"],
        )

        print("AI分析結果の解析に成功しました。")

        return analysis

    except Exception as e:

        print("OllamaによるAI分析に失敗しました。")
        print(f"エラー: {e}")

        print("ルールベースの診断結果を使用します。")

        # AIが使用できない場合のフォールバック
        return AIAnalysis(
            summary="AI分析を実行できなかったため、通常の診断結果を表示します。",
            priority=data["overall_status"],
            causes=data["causes"],
            recommendations=data["recommendations"],
        )
