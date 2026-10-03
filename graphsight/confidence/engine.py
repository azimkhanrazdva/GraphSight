from __future__ import annotations


class ConfidenceEngine:
    def __init__(self, weights: dict[str, float] | None = None) -> None:
        self.weights = weights or {
            "detector": 0.25,
            "ocr": 0.15,
            "connector": 0.3,
            "arrow": 0.1,
            "rules": 0.2,
        }

    def calculate(self, signals: dict[str, float]) -> float:
        used = {name: score for name, score in signals.items() if name in self.weights}
        if not used:
            return 0.0
        total_weight = sum(self.weights[name] for name in used)
        score = sum(self.weights[name] * max(0.0, min(1.0, value)) for name, value in used.items())
        return round(score / total_weight, 3)

