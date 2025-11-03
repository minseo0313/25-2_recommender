# API Views

from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.shortcuts import get_object_or_404

from .serializers import (
    RecommendationOnboardingSerializer,
    RecommendationListResponseSerializer,
)
from ..agents.orchestrator import OrchestratorAgent
from ..models import Session


# ─────────────────────────────────────────────────────────
# [POST] /api/onboarding/
# 사용자의 온보딩 데이터를 받아 세션 생성/갱신 후,
# Agent1으로 쿼리/타겟규칙을 생성하고 요약 배지와 함께 반환
# ─────────────────────────────────────────────────────────
@api_view(['POST'])
def onboarding(request):

    # 1) 요청 데이터 검증
    serializer = RecommendationOnboardingSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    data = serializer.validated_data

    # 2) 세션 생성/갱신 (session_key가 오면 upsert)
    session_key = data.get('session_key')
    if session_key:
        session, _ = Session.objects.get_or_create(
            session_key=session_key,
            defaults={'onboarding': data},
        )
    else:
        session = Session.objects.create(onboarding=data)

    # 온보딩 최신 상태로 저장
    session.onboarding = data
    session.save()

    # 3) Agent1 호출(쿼리/타겟규칙/의도 생성)
    orchestrator = OrchestratorAgent()
    agent1_result = orchestrator.query_agent.process_query(data)

    session.target_rules = agent1_result.get('target_rules', {})
    session.intent = agent1_result.get('intent', {})
    session.save()

    # 4) 요약 배지(확인 화면용)
    summary_badges = {
        "keywords": data.get("keywords", []),
        "price_range": data.get("price_range", {}),
        "category": data.get("category"),
        "subcategories": data.get("subcategories", []),
        "purpose": data.get("purpose", []),
    }

    # 5) 응답
    return Response(
        {
            "session_id": session.id,
            "generated_query": agent1_result.get("query", ""),
            "target_rules": session.target_rules,
            "summary_badges": summary_badges,
        },
        status=status.HTTP_200_OK,
    )


# ─────────────────────────────────────────────────────────
# [GET] /api/recommendations/<session_id>/?top_n=10
# 세션 기준으로 에이전트 파이프라인(Agent1→2→3)을 실행해
# 추천 리스트(리스트용 필드만)를 반환
# ─────────────────────────────────────────────────────────
@api_view(['GET'])
def recommendations(request, session_id):
    
    # 1) 세션 확인 (없으면 404)
    session = get_object_or_404(Session, id=session_id)

    # 2) Orchestrator 생성 및 파이프라인 실행
    orchestrator = OrchestratorAgent()

    # Agent1: 온보딩 기반 쿼리/규칙 보강
    agent1_result = orchestrator.query_agent.process_query(session.onboarding)

    # Agent2: 후보 생성(벡터 검색/필터 등)
    candidates = orchestrator.candidate_agent.generate_candidates(agent1_result, top_k=200)

    # 3) top_n 파라미터 처리 (기본 10, 1~50 제한)
    top_n = request.GET.get('top_n', 10)
    try:
        top_n = int(top_n)
        top_n = min(max(top_n, 1), 50)
    except (ValueError, TypeError):
        top_n = 10

    # Agent3: 재랭킹
    target_rules = agent1_result.get('target_rules', {})
    intent = agent1_result.get('intent', {})
    final_recommendations = orchestrator.rerank_agent.rerank_and_persist(session, candidates, target_rules, intent, top_n=top_n)

    # 4) 응답 아이템 포맷(리스트 화면에 필요한 필드만)
    items = []
    for rec in final_recommendations:
        # rec은 이미 dict 형태로 반환됨 (product_id, name, price 등이 직접 포함)
        if not rec:
            continue

        items.append({
            "product_id": rec.get("product_id", ""),
            "name": rec.get("name", ""),
            "price": rec.get("price", 0),
            "category": rec.get("category", ""),
            "purpose": rec.get("purpose", []),      # 섭취 목적 태그
            "health_tags": rec.get("health_tags", []),  # 건강 키워드(무가당/제로 등)
            "image_url": rec.get("image_url", ""),
            "detail_url": rec.get("detail_url", ""),
        })

    response_data = {
        "session_id": session.id,
        "top_n": len(items),
        "items": items,
    }

    # 5) 직렬화 검증 후 반환
    response_serializer = RecommendationListResponseSerializer(data=response_data)
    response_serializer.is_valid(raise_exception=True)
    return Response(response_serializer.data, status=status.HTTP_200_OK)
