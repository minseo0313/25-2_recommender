# 사용자 온보딩 정보를 입력으로 받아 "쿼리/필터 생성" => "후보 생성" => "재랭킹" 순서로 실행한 뒤 최종 추천 결과를 반환 

from .agent1_query import QueryAgent
from .agent2_candidate import CandidateAgent
from .agent3_rerank import RerankAgent

class OrchestratorAgent:

    def __init__(self):

        self.query_agent = QueryAgent()
        self.candidate_agent = CandidateAgent()
        self.rerank_agent = RerankAgent()
    


    # 추천 파이프라인 메서드 
    def process_recommendation_request(self, user_query):
        
        # Agent 1: LLM을 활용해 (온보딩 정보 기반 쿼리문 생성  + 구매 목적 기반 핵심 필터 기준(영양 타깃)) 정의  
        processed_query = self.query_agent.process_query(user_query)
        
        # Agent 2: 유사도 검색(Top-K) + 카테고리/가격 필터링 + 영양 정보 매칭(퍼지매칭) + 1차 영양 하드 필터  
        candidates = self.candidate_agent.generate_candidates(processed_query)
        
        # Agent 3: LLM 유효성 검증 + 재랭킹 스코어 계산 + 최종 Top-N 선정  
        final_recommendations = self.rerank_agent.rerank_candidates(candidates)
        
        return final_recommendations