# 영양 필터링 서비스: 하드 규칙 적용
from __future__ import annotations
from typing import List, Dict, Any
from ..models import ProductMeta

class NutritionService:
    """
    target_rules 예:
      {
        "sugar_g": {"lte": 5},
        "protein_g": {"gte": 15},
        "kcal": {"lte": 200},
        "price": {"gte": 1000, "lte": 100000},
        "unit_size_g": {"gte": 3, "lte": 100},
        "lactose_free": True,
      }
    """

    def _check_numeric(self, value: float, rule: Dict[str, float]) -> bool:
        if value is None:
            return False
        if "gte" in rule and value < rule["gte"]:
            return False
        if "lte" in rule and value > rule["lte"]:
            return False
        if "eq" in rule and value != rule["eq"]:
            return False
        return True

    def hard_filter(self, products: List[ProductMeta], target_rules: Dict[str, Any]) -> List[ProductMeta]:
        if not target_rules:
            return products

        out: List[ProductMeta] = []
        for p in products:
            ok = True

            # 가격 규칙
            price_rule = target_rules.get("price")
            if price_rule:
                if not self._check_numeric(getattr(p, "price", None), price_rule):
                    ok = False

            # 영양 성분 규칙(JSON facts)
            facts = {}
            if hasattr(p, "nutrition") and p.nutrition and isinstance(p.nutrition.facts, dict):
                facts = p.nutrition.facts

            for k, cond in target_rules.items():
                if k in ("price",):  # 이미 처리
                    continue
                # boolean 플래그 (예: lactose_free)
                if isinstance(cond, bool):
                    if bool(facts.get(k)) != cond:
                        ok = False
                        break
                # 수치 규칙
                elif isinstance(cond, dict):
                    val = facts.get(k)
                    if val is None:
                        ok = False
                        break
                    if not self._check_numeric(float(val), cond):
                        ok = False
                        break
                # 기타형은 무시

            if ok:
                out.append(p)

        return out
