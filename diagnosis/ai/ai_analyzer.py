import json
import urllib.error
import urllib.request
from dataclasses import dataclass


# ============================================================
# Ollama設定
# ============================================================

OLLAMA_URL = "http://127.0.0.1:11434/api/generate"

OLLAMA_MODEL = "gemma4"

# AI応答の最大待機時間（秒）
OLLAMA_TIMEOUT = 300


# ============================================================
# AI分析結果
# ============================================================

@dataclass
class AIAnalysis:
    summary: str
    priority: str
    causes: list[str]
    recommendations: list[str]


# ============================================================
# 診断結果 → AI用データ
# ============================================================

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


# ============================================================
# Ollama呼び出し
# ============================================================

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

    try:

        with urllib.request.urlopen(
            request,
            timeout=OLLAMA_TIMEOUT,
        ) as response:

            response_data = json.loads(
                response.read().decode("utf-8")
            )

    except urllib.error.URLError as e:

        raise RuntimeError(
            f"Ollamaへ接続できませんでした: {e}"
        ) from e

    except TimeoutError as e:

        raise RuntimeError(
            "Ollamaの応答がタイムアウトしました。"
        ) from e

    except json.JSONDecodeError as e:

        raise RuntimeError(
            "Ollamaから不正なJSONレスポンスが返されました。"
        ) from e

    if "response" not in response_data:

        raise RuntimeError(
            "Ollamaのレスポンスにresponseが含まれていません。"
        )

    response_text = response_data["response"]

    if not isinstance(response_text, str):

        raise RuntimeError(
            "OllamaのAI回答が文字列ではありません。"
        )

    if not response_text.strip():

        raise RuntimeError(
            "Ollamaから空のAI回答が返されました。"
        )

    return response_text.strip()


# ============================================================
# AI回答のJSON整形
# ============================================================

def clean_json_response(response):
    """
    AIが返したJSON文字列を整形する。

    ```json
    {...}
    ```

    のようなコードブロックにも対応する。
    """

    response = response.strip()

    if response.startswith("```json"):

        response = response[len("```json"):].strip()

    elif response.startswith("```"):

        response = response[len("```"):].strip()

    if response.endswith("```"):

        response = response[:-3].strip()

    return response


# ============================================================
# AI回答の検証
# ============================================================

def validate_ai_result(result, diagnosis):
    """
    AIが返したJSONの内容を検証する。

    問題がある場合はValueErrorを発生させる。
    """

    if not isinstance(result, dict):

        raise ValueError(
            "AIの回答がJSONオブジェクトではありません。"
        )

    # summary
    summary = result.get("summary")

    if not isinstance(summary, str) or not summary.strip():

        raise ValueError(
            "AI回答のsummaryが不正です。"
        )

    # priority
    priority = result.get(
        "priority",
        diagnosis.status,
    )

    if priority not in (
        "正常",
        "注意",
        "警告",
    ):

        raise ValueError(
            f"AI回答のpriorityが不正です: {priority}"
        )

    # causes
    causes = result.get("causes", [])

    if not isinstance(causes, list):

        raise ValueError(
            "AI回答のcausesがリストではありません。"
        )

    if not all(
        isinstance(cause, str)
        for cause in causes
    ):

        raise ValueError(
            "AI回答のcausesに文字列以外が含まれています。"
        )

    # recommendations
    recommendations = result.get(
        "recommendations",
        [],
    )

    if not isinstance(recommendations, list):

        raise ValueError(
            "AI回答のrecommendationsがリストではありません。"
        )

    if not all(
        isinstance(recommendation, str)
        for recommendation in recommendations
    ):

        raise ValueError(
            "AI回答のrecommendationsに文字列以外が含まれています。"
        )

    return AIAnalysis(
        summary=summary.strip(),
        priority=priority,
        causes=causes,
        recommendations=recommendations,
    )


# ============================================================
# フォールバック
# ============================================================

def create_fallback_analysis(diagnosis):
    """
    Ollamaが利用できない場合の代替AI分析結果を作成する。

    診断エンジンの結果をそのまま利用する。
    """

    return AIAnalysis(
        summary="AI分析を実行できませんでした。診断エンジンの結果を表示しています。",
        priority=diagnosis.status,
        causes=list(diagnosis.causes),
        recommendations=list(diagnosis.recommendations),
    )


# ============================================================
# AI分析
# ============================================================

def analyze_with_ai(diagnosis):
    """
    診断結果をOllamaのローカルAIで分析する。

    Ollamaが利用できない場合でも、
    診断システム全体は停止せず、
    診断エンジンの結果をフォールバックとして返す。
    """

    data = diagnosis_to_dict(diagnosis)

    print("\n" + "=" * 60)
    print("                 AI分析")
    print("=" * 60)

    print("OllamaによるAI分析を開始します...")
    print(f"使用モデル: {OLLAMA_MODEL}")

    prompt = f"""
あなたはPC診断を専門とするAIです。

以下のPC診断結果だけを根拠として分析してください。

診断結果:
{json.dumps(data, ensure_ascii=False, indent=2)}

重要なルール:

- 診断結果に存在しない事実を作らないでください。
- ハードウェア故障などを断定しないでください。
- 原因は「可能性」として説明してください。
- 対策はユーザーが安全に実施できる内容にしてください。
- priorityは診断結果の重要度を参考にしてください。
- priorityは必ず「正常」「注意」「警告」のいずれかにしてください。

以下の4項目について日本語で回答してください。

1. summary
PCの状態を簡潔に説明してください。

2. priority
重要度を
「正常」「注意」「警告」
のいずれかで回答してください。

3. causes
考えられる原因を箇条書きで説明してください。

4. recommendations
ユーザーが実施すべき対策を箇条書きで説明してください。

必ず以下のJSON形式だけで回答してください。

{{
  "summary": "PCの状態の概要",
  "priority": "注意",
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
"""

    try:

        # ----------------------------------------------------
        # Ollama呼び出し
        # ----------------------------------------------------

        response = call_ollama(prompt)

        print("OllamaからAI分析結果を取得しました。")

        # ----------------------------------------------------
        # JSON整形
        # ----------------------------------------------------

        response = clean_json_response(response)

        # ----------------------------------------------------
        # JSON解析
        # ----------------------------------------------------

        result = json.loads(response)

        # ----------------------------------------------------
        # 内容検証
        # ----------------------------------------------------

        analysis = validate_ai_result(
            result,
            diagnosis,
        )

        print("AI分析結果の解析に成功しました。")

        return analysis

    except json.JSONDecodeError as e:

        print("AI分析結果のJSON解析に失敗しました。")
        print(f"エラー: {e}")

    except ValueError as e:

        print("AI分析結果の形式が不正です。")
        print(f"エラー: {e}")

    except RuntimeError as e:

        print("OllamaによるAI分析に失敗しました。")
        print(f"エラー: {e}")

    except Exception as e:

        print("AI分析中に予期しないエラーが発生しました。")
        print(f"エラー: {e}")

    # --------------------------------------------------------
    # フォールバック
    # --------------------------------------------------------

    print("診断エンジンの結果を使用します。")

    return create_fallback_analysis(diagnosis)