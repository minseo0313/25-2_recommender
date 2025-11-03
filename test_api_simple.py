#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import requests
import json

def test_onboarding():
    """온보딩 API 테스트"""
    url = "http://127.0.0.1:8000/api/onboarding/"
    
    # 유효한 카테고리 중 하나 사용
    data = {
        "keywords": ["protein", "low sugar"],
        "category": "음료"  # 정의된 카테고리 중 하나
    }
    
    try:
        response = requests.post(url, json=data)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"Session ID: {result.get('session_id')}")
            return result.get('session_id')
        else:
            return None
            
    except Exception as e:
        print(f"Error: {e}")
        return None

def test_recommendations(session_id):
    """추천 API 테스트"""
    if not session_id:
        print("No session ID to test recommendations")
        return
        
    url = f"http://127.0.0.1:8000/api/recommendations/{session_id}/"
    
    try:
        response = requests.get(url)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    print("=== Django 서버 API 테스트 ===")
    
    print("\n1. 온보딩 API 테스트")
    session_id = test_onboarding()
    
    if session_id:
        print(f"\n2. 추천 API 테스트 (Session ID: {session_id})")
        test_recommendations(session_id)
    else:
        print("\n온보딩 API 실패로 추천 API 테스트를 건너뜁니다.")

