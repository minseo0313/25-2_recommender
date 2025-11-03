# apps/app/agents/agent1_query.py

from __future__ import annotations

import json
import os
from typing import Any, Dict, List, Optional, Tuple

from pydantic import BaseModel, Field, ValidationError

# OpenAI SDK 
try:
    from openai import OpenAI
except Exception:
    OpenAI = None        # 런타임에서 ImportError 방지

# ─────────────────────────────────────────────────────────────────────────────
# OpenAI 클라이언트 (OPEN_API_KEY)
# ─────────────────────────────────────────────────────────────────────────────
if OpenAI is None:
    print("OpenAI SDK가 설치되어 있지 않습니다.")
    client = None
else:
    client = OpenAI(api_key=os.getenv("OPEN_API_KEY"))

# ─────────────────────────────────────────────────────────────────────────────
# 출력 스키마 (LLM 가이드 + 런타임 검증)
# ─────────────────────────────────────────────────────────────────────────────
class ProcessedQueryOut(BaseModel):
    search_query: str = Field(
        ..., 
        description="자연어 검색문"
    )

    filters: Dict[str, Any] = Field(
        ...,
        description="카테고리/가격/영양타깃 포함. {category, price_min, price_max, nutrition_target}"
    )

    query_embedding: List[float] = Field (
        ..., 
        description= "임베딩 벡터"
    )


# ─────────────────────────────────────────────────────────────────────────────
# LLM 프롬프트 (쿼리 생성 + 영양 타깃 정의)
# ─────────────────────────────────────────────────────────────────────────────
LLM_SYSTEM_PROMPT = """\
당신은 식품 추천 시스템의 '쿼리 설계자'다.
사용자가 온보딩에서 입력한 정보를 바탕으로 다음을 만들어라:

1) search_query: 한국어 짧은 검색문. (예: "저당 고단백 단백질바 5000원 이하")
2) filter: 아래 키만 사용해라.
    - category: 사용자가 지정했거나 합리적으로 해석 가능한 상위 카테고리(없으면 생략)
    - price_min: 숫자(float) (없으면 생략)
    - price_max: 숫자(float) (없으면 생략)
    - nutrition_target: 구매 목적을 반영한 하드 필터 규칙(dict)
        * 예시 규칙(가이드, 상황에 맞게 조정 가능):
            - 운동/회복: sugar_max <= 5, protein_min >= 10
            - 체중감량: sugar_max <= 3, protein_min >= 12, calories_max <= 200
            - 간단간식: sugar_max <= 10, protein_min >= 5
            - 고단백: protein_min >= 15
        * 숫자 값만 사용(단위 표기 금지) 키 예: sugar_max, protein_min, calories_max, fat_max, saturated_fat_max, sodium_max

주의: 
- 존재하지 않는 값 임의 생성 금지(특히 가격). 사용자 입력 없으면 해당 키 생략.
- 불필요한 설명 없이 JSON 객체만 반환.
"""

LLM_USER_PROMPT_TEMPLATE = """\
[Onboarding]
{user_query_json}

위 지침을 따르는 JSON만 반환하라.
키는 search_query, filters 두 개만 존재해야 한다.
"""

# ─────────────────────────────────────────────────────────────────────────────
# 폴백 규칙(LLM/네트워크 실패 시)
# ─────────────────────────────────────────────────────────────────────────────




# ─────────────────────────────────────────────────────────────────────────────
# 에이전트 구현
# ─────────────────────────────────────────────────────────────────────────────
DEFAULT_CHAT_MODEL = os.getenv("OPENAI_RESPONSES_MODEL", "gpt-4o-mini")
DEFAULT_EMBED_MODEL = os.getenv("OPENAI_EMBEDDINGS_MODEL", "text-embedding-3-small")






