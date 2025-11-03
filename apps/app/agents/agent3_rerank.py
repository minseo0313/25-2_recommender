# Agent 3: Reranking Agent
"""
후보를 재랭킹하고(유사도/영양/목적 점수), 필요 시 상위 N개를 DB에 저장한다.
- 입력 후보 형태: {"product": ProductMeta, "sim": float, "health_tags": list[str], "purpose": list[str]}
- 출력: API 친화적 dict 리스트 (model 인스턴스 제외)
"""

from typing import List, Dict, Any, Tuple
import numpy as np
from django.db import transaction

from ..services.embedding import EmbeddingService
from ..services.scoring import ScoringService
from ..models import Session, ProductMeta, RecommendResult


class RerankAgent:
    def __init__(self):
        self.embedding = EmbeddingService()
        self.scoring = ScoringService()

    # ─────────────────────────────────────────────────────
    # 내부: 안전 코사인 계산
    # ─────────────────────────────────────────────────────
    def _cosine(self, q: np.ndarray, emb_list: List[float]) -> float:
        if not isinstance(q, np.ndarray) or q.size == 0 or not emb_list:
            return 0.0
        b = np.array(emb_list, dtype=np.float32)
        denom = (np.linalg.norm(q) * np.linalg.norm(b))
        if denom == 0:
            return 0.0
        return float(np.dot(q, b) / denom)

    # ─────────────────────────────────────────────────────
    # 재랭킹(저장 없음) : 리스트 응답용
    # ─────────────────────────────────────────────────────
    def rerank_candidates(
        self,
        candidates: List[Dict[str, Any]],
        target_rules: Dict[str, Any],
        intent: Dict[str, Any],
        top_n: int = 10,
    ) -> List[Dict[str, Any]]:
        """
        candidates: Agent2 결과(표준 포맷 dict 리스트)
        target_rules: Agent1가 만든 하드 필터/가이드
        intent: {query, purpose, ...}
        return: API 친화적 dict 리스트(상위 top_n)
        """
        query_text = intent.get("query", "") or ""
        query_vec = self.embedding.get_embedding(query_text)

        items: List[Dict[str, Any]] = []
        purposes = intent.get("purpose", []) or []

        for cand in candidates:
            p: ProductMeta = cand.get("product")
            if not p:
                continue

            # 1) 유사도: 후보에 사전계산 sim이 있으면 사용, 없으면 재계산
            sim = float(cand.get("sim") or 0.0)
            if sim == 0.0:
                emb = getattr(getattr(p, "embedding", None), "embedding", None)
                if emb:
                    sim = self._cosine(query_vec, emb)

            # 2) 영양/목적 점수
            facts = getattr(getattr(p, "nutrition", None), "facts", {}) or {}
            nutrition_score = self.scoring.compute_nutrition_score(target_rules or {}, facts)
            # 목적 적합도는 상품 keywords 또는 health_tags를 재료로 계산
            product_keywords = []
            if hasattr(p, "keywords") and p.keywords:
                product_keywords = [str(k) for k in p.keywords]
            health_tags = cand.get("health_tags") or product_keywords
            purpose_score = self.scoring.compute_purpose_score(purposes, health_tags)

            # 3) 최종 점수
            final_score = self.scoring.score_item(sim, nutrition_score, purpose_score)

            items.append({
                "product": p,                                # 내부에서만 사용
                "product_id": getattr(p, "external_id", None),
                "name": getattr(p, "name", ""),
                "category": getattr(p, "category", ""),
                "price": getattr(p, "price", 0),
                "image_url": getattr(p, "image_url", ""),
                "detail_url": getattr(p, "detail_url", ""),
                "score": final_score,
                "why": f"sim={sim:.2f}, nutrition={nutrition_score:.2f}, purpose={purpose_score:.2f}",
                "nutrition": facts,
                "purpose": purposes,
                "health_tags": health_tags,
            })

        # 정렬 및 top-n
        items.sort(key=lambda x: x["score"], reverse=True)
        top_items = items[:max(1, min(int(top_n or 10), 50))]

        # 외부 응답용(dict에서 model 제거)
        response: List[Dict[str, Any]] = [
            {k: v for k, v in it.items() if k != "product"} for it in top_items
        ]
        return response

    # ─────────────────────────────────────────────────────
    # 재랭킹 + DB 저장 : 히스토리/분석용
    # ─────────────────────────────────────────────────────
    def rerank_and_persist(
        self,
        session: Session,
        candidates: List[Dict[str, Any]],
        target_rules: Dict[str, Any],
        intent: Dict[str, Any],
        top_n: int = 10,
    ) -> List[Dict[str, Any]]:
        """
        세션 기준으로 상위 N개를 저장(RecommendResult)하고 응답 dict를 반환한다.
        """
        # 1) 먼저 재랭킹 결과 산출
        ranked = self.rerank_candidates(candidates, target_rules, intent, top_n=top_n)

        # 2) DB 저장(세션, 상품, 목적, 점수/이유)
        #    - 같은 (session, product) 중복 저장을 피하려면 모델 unique_together 또는 ignore_conflicts 사용
        #    - 여기서는 product id 매칭을 위해 원본 candidates에서 product 인스턴스를 찾아 매핑
        #      (간단히 external_id → ProductMeta 캐시를 만든다)
        by_external: Dict[str, ProductMeta] = {}
        for cand in candidates:
            p = cand.get("product")
            if p and getattr(p, "external_id", None):
                by_external[p.external_id] = p

        results = []
        for it in ranked:
            ext_id = it.get("product_id")
            p = by_external.get(ext_id)
            if not p:
                continue
            results.append(
                RecommendResult(
                    session=session,
                    product=p,
                    purpose=it.get("purpose", []),
                    score=it.get("score", 0.0),
                    why=it.get("why", ""),
                )
            )

        if results:
            with transaction.atomic():
                # 모델에 unique 제약이 없다면 중복 저장될 수 있음. 필요 시 unique 설정 또는 delete/insert 전략 사용.
                RecommendResult.objects.bulk_create(results, ignore_conflicts=True)

        return ranked
