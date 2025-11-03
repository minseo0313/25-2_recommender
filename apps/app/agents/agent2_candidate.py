# Agent 2: Candidate Generation Agent
"""
임베딩 유사도 + 하드 필터로 후보 상품을 생성한다.
- Agent1 결과(dict) 또는 (query, intent, target_rules) 개별 인자를 받아 동작
- 반환: 후보 리스트[{"product", "sim", "health_tags", "purpose"}]
"""

from typing import List, Dict, Any, Tuple, Optional
import numpy as np
from django.db.models import QuerySet

from ..services.embedding import EmbeddingService
from ..services.nutrition import NutritionService
from ..models import ProductMeta


class CandidateAgent:
    def __init__(self):
        self.embedding = EmbeddingService()
        self.nutrition = NutritionService()

    # ─────────────────────────────────────────────────────
    # 내부: 안전한 코사인 유틸
    # ─────────────────────────────────────────────────────
    def _cosine(self, a: np.ndarray, b_list: List[float]) -> float:
        if not isinstance(a, np.ndarray) or a.size == 0 or not b_list:
            return 0.0
        b = np.array(b_list, dtype=np.float32)
        denom = (np.linalg.norm(a) * np.linalg.norm(b))
        if denom == 0:
            return 0.0
        return float(np.dot(a, b) / denom)

    # ─────────────────────────────────────────────────────
    # 내부: Agent1 결과 dict 분해
    # ─────────────────────────────────────────────────────
    def _unpack_agent1(
        self,
        arg: Any,
        query: Optional[str],
        intent: Optional[Dict[str, Any]],
        target_rules: Optional[Dict[str, Any]],
    ) -> Tuple[str, Dict[str, Any], Dict[str, Any]]:
        """
        arg가 dict면 Agent1 결과로 간주하고, 아니면 개별 인자를 사용한다.
        """
        if isinstance(arg, dict) and ("query" in arg or "intent" in arg):
            q = arg.get("query", "") or ""
            ir = arg.get("intent", {}) or {}
            tr = arg.get("target_rules", {}) or {}
            return q, ir, tr
        # 개별 인자 모드
        return query or "", intent or {}, target_rules or {}

    # ─────────────────────────────────────────────────────
    # 메인: 후보 생성
    # ─────────────────────────────────────────────────────
    def generate_candidates(
        self,
        agent1_result_or_query: Any,
        intent: Optional[Dict[str, Any]] = None,
        target_rules: Optional[Dict[str, Any]] = None,
        top_k: int = 200,
        seed: Optional[int] = None,
        exclude_ids: Optional[List[str]] = None,
    ) -> List[Dict[str, Any]]:
        """
        매개변수
        - agent1_result_or_query: Agent1 결과(dict) 또는 순수 query(str)
        - intent, target_rules: 개별 인자 모드일 때만 사용
        - top_k: 1차 유사도 상위 N개 추출
        - seed: 다양성(무작위 셔플) 시드
        - exclude_ids: 이전 추천에서 제외할 external_id 목록

        반환
        - 후보 목록: [{"product": ProductMeta, "sim": float, "health_tags": list[str], "purpose": list[str]}]
        """
        query, intent, target_rules = self._unpack_agent1(
            agent1_result_or_query, query=intent if isinstance(agent1_result_or_query, str) else None,
            intent=intent, target_rules=target_rules
        )

        # 1) 쿼리 임베딩 계산
        query_vec = self.embedding.get_embedding(query)

        # 2) 1차 ORM 필터링 (카테고리/가격)
        qs: QuerySet = ProductMeta.objects.select_related(
            "nutrition"
        ).select_related(
            "embedding"
        )

        category = (intent or {}).get("category")
        if category:
            if hasattr(ProductMeta, "category"):
                qs = qs.filter(category=category)

        price_min = (intent or {}).get("price_min")
        price_max = (intent or {}).get("price_max")
        if price_min is not None and hasattr(ProductMeta, "price"):
            qs = qs.filter(price__gte=price_min)
        if price_max is not None and hasattr(ProductMeta, "price"):
            qs = qs.filter(price__lte=price_max)

        # 세부카테고리: 전용 컬럼이 없다면 DB 필터를 생략하고 후처리
        subcats = (intent or {}).get("subcategories") or []

        # 3) 유사도 계산 (파이썬 공간)
        #    ※ 추후 pgvector로 DB내 유사도 계산을 하려면 여기 대신 RAW 쿼리/함수로 교체 가능
        scored: List[Tuple[float, ProductMeta]] = []
        it = qs.iterator()
        for p in it:
            emb = getattr(getattr(p, "embedding", None), "embedding", None)
            if emb is None:
                continue

            # exclude_ids 처리
            if exclude_ids:
                ext_id = getattr(p, "external_id", None)
                if ext_id and ext_id in exclude_ids:
                    continue

            sim = self._cosine(query_vec, emb)
            scored.append((sim, p))

        # 유사도 상위 정렬 & 슬라이싱
        scored.sort(key=lambda x: x[0], reverse=True)
        top_products = [p for _, p in scored[:max(top_k, 1)]]

        # 4) 세부카테고리 후처리(필요 시)
        if subcats:
            filtered = []
            for p in top_products:
                # 전용 컬럼이 있으면 우선 사용
                ok = False
                if hasattr(p, "subcategory") and getattr(p, "subcategory"):
                    ok = any(sc in str(getattr(p, "subcategory")) for sc in subcats)
                # 없으면 keywords(text[]) 기반으로 유사 판단
                if not ok and hasattr(p, "keywords") and getattr(p, "keywords"):
                    kws = [str(k) for k in (p.keywords or [])]
                    ok = any(sc in " ".join(kws) for sc in subcats)
                if ok:
                    filtered.append(p)
            # 세부카테고리가 있으면 교집합으로 줄여준다 (없으면 그대로)
            if filtered:
                top_products = filtered

        # 5) 영양 하드 필터 적용 (저당/고단백/칼로리 등)
        top_products = self.nutrition.hard_filter(top_products, target_rules or {})

        # 6) 다양성(무작위 셔플) 선택적 적용
        if seed is not None:
            rng = np.random.default_rng(seed)
            idx = np.arange(len(top_products))
            rng.shuffle(idx)
            top_products = [top_products[i] for i in idx]

        # 7) 표준 후보 포맷으로 반환
        purpose = (intent or {}).get("purpose", []) or []
        result: List[Dict[str, Any]] = []
        for p in top_products:
            # health_tags: 상품 keywords 또는 규칙에서 추출(없으면 빈 리스트)
            health_tags = []
            if hasattr(p, "keywords") and p.keywords:
                # keywords가 text[]인 경우
                health_tags = [str(k) for k in (p.keywords or [])]
            result.append(
                {
                    "product": p,
                    "sim": float(0.0),  # 필요시 sim을 노출하고 싶으면 위에서 함께 보존
                    "health_tags": health_tags,
                    "purpose": purpose,
                }
            )

        return result
