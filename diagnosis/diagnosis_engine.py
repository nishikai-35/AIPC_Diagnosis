from dataclasses import dataclass
from diagnosis.analyzer import DiagnosisResult

@dataclass
class OverallDiagnosis:
    status: str
    message: str
    causes: list[str]
    recommendations: list[str]
    results: list[DiagnosisResult]


def determine_overall_status(
    results: list[DiagnosisResult],
) -> str:

    if any(result.status == "警告" for result in results):
        return "警告"

    if any(result.status == "注意" for result in results):
        return "注意"

    return "正常"


def collect_causes(
    results: list[DiagnosisResult],
) -> list[str]:

    causes = []

    for result in results:
        for cause in result.causes:
            if cause not in causes:
                causes.append(cause)

    return causes


def collect_recommendations(
    results: list[DiagnosisResult],
) -> list[str]:

    recommendations = []

    for result in results:
        for recommendation in result.recommendations:
            if recommendation not in recommendations:
                recommendations.append(recommendation)

    return recommendations


def create_overall_message(status: str) -> str:

    if status == "警告":
        return "PCに注意が必要な問題が検出されています。"

    if status == "注意":
        return "PCにいくつか注意が必要な項目があります。"

    return "PCの状態に大きな問題は見られません。"


def run_diagnosis(
    results: list[DiagnosisResult],
) -> OverallDiagnosis:

    overall_status = determine_overall_status(results)

    causes = collect_causes(results)

    recommendations = collect_recommendations(results)

    message = create_overall_message(overall_status)

    return OverallDiagnosis(
        status=overall_status,
        message=message,
        causes=causes,
        recommendations=recommendations,
        results=results,
    )