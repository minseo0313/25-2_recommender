# 스코어링 서비스: 유사도/영양/목적 점수를 가중 합산
from __future__ import annotations
from typing import Dict, Any, List
import math

class ScoringService:
    """
    최종 점수 = α*sim + β*nutrition + γ*purpose
    - sim: 코사인 유사도(0~1 스케일 가정; 내부에서 음수인 경우 0으로 클리핑 권장)
    - nutrition: 규칙 일치율(0~1)
    - purpose: 목적 태그와 상품 태그(health_tags/keywords) 매칭률(0~1)
    """

    def __init__(self, alpha: float = 0.4, beta: float = 0.4, gamma: float = 0.2):
        self.alpha = alpha
        self.beta = beta
        self.gamma = gamma

    # 간단한 규칙 일치율: target_rules의 수치형 규칙 충족 비율
    def compute_nutrition_score(self, target_rules: Dict[str, Any], facts: Dict[str, Any]) -> float:
        if not target_rules:
            return 0.5  # 규칙이 없으면 중립
        if not facts:
            return 0.0

        total = 0
        ok = 0
        for k, cond in target_rules.items():
            if k == "price":
                continue
            if isinstance(cond, bool):
                total += 1
                if bool(facts.get(k)) == cond:
                    ok += 1
            elif isinstance(cond, dict):
                v = facts.get(k)
                if v is None:
                    total += 1
                    continue
                v = float(v)
                pass_flag = True
                if "gte" in cond and v < cond["gte"]:
                    pass_flag = False
                if "lte" in cond and v > cond["lte"]:
                    pass_flag = False
                if "eq"  in cond and v != cond["eq"]:
                    pass_flag = False
                total += 1
                if pass_flag:
                    ok += 1
        return ok / total if total else 0.5

    # 목적-태그 매칭률: 목적 리스트와 상품 태그(health_tags/keywords)의 교집합 비율
    def compute_purpose_score(self, purposes: List[str] | None, tags: List[str] | None) -> float:
        if not purposes:
            return 0.3  # 목적이 없으면 낮은 기본값
        if not tags:
            return 0.0
        p = set(map(str, purposes))
        t = set(map(str, tags))
        return len(p & t) / len(p)

    def score_item(self, sim: float, nutrition_score: float, purpose_score: float) -> float:
        # 안전 클리핑
        sim = max(0.0, min(1.0, sim))
        nutrition_score = max(0.0, min(1.0, nutrition_score))
        purpose_score = max(0.0, min(1.0, purpose_score))
        return self.alpha * sim + self.beta * nutrition_score + self.gamma * purpose_score
