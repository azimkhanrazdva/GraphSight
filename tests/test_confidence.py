from graphsight.confidence.engine import ConfidenceEngine


def test_confidence_uses_available_weighted_signals() -> None:
    score = ConfidenceEngine().calculate({"detector": 1.0, "connector": 0.5})
    assert score == 0.727
