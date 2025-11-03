# 요청(request) 데이터 검증 및 응답(response) 데이터 구조 정의

from rest_framework import serializers


# ─────────────────────────────────────────────────────────
# 사전 정의: 카테고리/세부카테고리/목적/건강키워드
# ─────────────────────────────────────────────────────────
CATEGORIES = {
    "음료": ["탄산/제로", "유제품/요거트", "과채주스", "탄산수", "차/티"],
    "간식 & 디저트": ["쿠키/비스킷", "초콜릿", "젤리/케이크", "씨리얼바"],
    "식사 대체 & 간편식": ["프로틴 쉐이크", "닭가슴살", "샐러드", "즉석밥/죽"],
    "조리 재료": ["저염 소스", "올리브오일", "통밀/귀리", "저당 설탕"],
}
ALL_CATEGORIES = set(CATEGORIES.keys())
ALL_SUBCATEGORIES = {s for v in CATEGORIES.values() for s in v}

PURPOSE_CHOICES = {
    "체중 관리", "다이어트", "운동 후 회복", "근육/단백질 보충", "건강 간식",
    "소화 도움", "포만감 유지", "야식 대체"
}
HEALTH_KEYWORDS = {
    "제로", "무가당", "저당", "고단백", "저칼로리", "저염", "고식이섬유", "유당무첨가"
}


# ─────────────────────────────────────────────────────────
# 공통: 가격 범위(엄격 검증)
# ─────────────────────────────────────────────────────────
class PriceRangeSerializer(serializers.Serializer):
    min = serializers.IntegerField(min_value=0, help_text="최소 금액(0 이상)")
    max = serializers.IntegerField(min_value=0, help_text="최대 금액(0 이상)")

    def validate(self, attrs):
        if attrs["min"] > attrs["max"]:
            raise serializers.ValidationError("최소 금액(min)은 최대 금액(max)보다 클 수 없습니다.")
        return attrs


# ─────────────────────────────────────────────────────────
# [온보딩 입력] UI 제약에 맞춘 요청 스키마
# ─────────────────────────────────────────────────────────
class RecommendationOnboardingSerializer(serializers.Serializer):
    # 프론트에서 보낼 수도, 안 보낼 수도 있음
    session_key = serializers.CharField(max_length=255, required=False, allow_blank=True)

    # 건강 키워드(최대 3) - UI의 ‘키워드’ 화면
    keywords = serializers.ListField(
        child=serializers.CharField(max_length=50),
        max_length=3, required=False, allow_empty=True,
        help_text="건강 키워드(최대 3개, 예: 제로/무가당/저당/고단백/저칼로리)"
    )

    # 가격대 - UI의 슬라이더(min/max)
    price_range = PriceRangeSerializer(required=False, help_text="가격 범위 {min,max}")

    # 카테고리(필수 1개) - UI의 ‘식품 카테고리’ 화면
    category = serializers.CharField(
        max_length=50, required=True, allow_blank=False,
        help_text=f"카테고리(필수): {sorted(ALL_CATEGORIES)} 중 택1"
    )

    # 세부 카테고리(선택, 최대 3개) - UI의 ‘세부 카테고리’ 화면
    subcategories = serializers.ListField(
        child=serializers.CharField(max_length=50),
        max_length=3, required=False, allow_empty=True,
        help_text="세부 카테고리(선택, 최대 3개)"
    )

    # 구매 목적(최대 3개) + 자유 입력 1개
    purpose = serializers.ListField(
        child=serializers.CharField(max_length=50),
        max_length=3, required=False, allow_empty=True,
        help_text=f"구매 목적(선택, 최대 3개, 예: {sorted(list(PURPOSE_CHOICES))[:5]} …)"
    )
    free_purpose = serializers.CharField(
        max_length=50, required=False, allow_blank=True,
        help_text="구매 목적 자유 입력(선택, 1개)"
    )

    # 유틸: 공백 제거 + 중복 제거 + 상한 제한
    def _clean_list(self, values, limit):
        cleaned = []
        for v in (values or []):
            s = v.strip()
            if s and s not in cleaned:
                cleaned.append(s)
            if len(cleaned) >= limit:
                break
        return cleaned

    def validate_keywords(self, value):
        value = self._clean_list(value, 3)
        # 선택지가 있으면 필터링(없애고 싶으면 이 블록 제거)
        return [v for v in value if v in HEALTH_KEYWORDS]

    def validate_category(self, value):
        if value not in ALL_CATEGORIES:
            raise serializers.ValidationError("유효하지 않은 카테고리입니다.")
        return value

    def validate_subcategories(self, value):
        value = self._clean_list(value, 3)
        # 전체 세부 카테고리 집합에 속하는지
        wrong = [v for v in value if v not in ALL_SUBCATEGORIES]
        if wrong:
            raise serializers.ValidationError(f"유효하지 않은 세부 카테고리: {wrong}")
        return value

    def validate_purpose(self, value):
        value = self._clean_list(value, 3)
        # 선택지 기반(자유 입력은 free_purpose로 처리)
        return [v for v in value if v in PURPOSE_CHOICES]

    def validate(self, attrs):
        # 세부카테고리가 부모 카테고리에 속하는지 교차 검증
        category = attrs.get("category")
        subs = attrs.get("subcategories") or []
        if subs:
            valid_set = set(CATEGORIES.get(category, []))
            wrong = [s for s in subs if s not in valid_set]
            if wrong:
                raise serializers.ValidationError(
                    {"subcategories": f"선택한 카테고리에 없는 세부 카테고리입니다: {wrong}"}
                )

        # 자유 목적 합치기(중복 제거, 최종 3개 유지)
        purposes = attrs.get("purpose") or []
        free = (attrs.get("free_purpose") or "").strip()
        if free:
            if free not in purposes:
                purposes.append(free)
        attrs["purpose"] = purposes[:3]
        return attrs


# ─────────────────────────────────────────────────────────
# [추천 리스트 아이템] UI에 필요한 필드만 압축
# (이미지/이름/가격/카테고리/섭취목적/건강 키워드/외부링크)
# ─────────────────────────────────────────────────────────
class RecommendationListItemSerializer(serializers.Serializer):
    product_id = serializers.CharField(help_text="상품 고유 ID")
    name = serializers.CharField(help_text="제품명")
    price = serializers.IntegerField(help_text="가격")
    category = serializers.CharField(help_text="카테고리")

    purpose = serializers.ListField(
        child=serializers.CharField(), required=False, help_text="섭취 목적 태그"
    )
    health_tags = serializers.ListField(
        child=serializers.CharField(), required=False, help_text="건강 키워드(무가당/제로 등)"
    )

    image_url = serializers.URLField(required=False, allow_blank=True, help_text="대표 이미지")
    detail_url = serializers.URLField(required=False, allow_blank=True, help_text="외부 상세/구매 링크")


class RecommendationListResponseSerializer(serializers.Serializer):
    session_id = serializers.IntegerField(help_text="세션 ID")
    top_n = serializers.IntegerField(help_text="리스트 아이템 수")
    items = RecommendationListItemSerializer(many=True, help_text="추천 아이템들")


# ─────────────────────────────────────────────────────────
# [상세 보기] 이미지/이름(+외부 링크)/가격/설명/주요특징/영양성분
# ─────────────────────────────────────────────────────────
class ProductDetailResponseSerializer(serializers.Serializer):
    product_id = serializers.CharField(help_text="상품 고유 ID")
    name = serializers.CharField(help_text="제품명")
    price = serializers.IntegerField(help_text="가격")
    image_url = serializers.URLField(required=False, allow_blank=True, help_text="대표 이미지")
    external_url = serializers.URLField(required=False, allow_blank=True, help_text="외부 상세/구매 링크")

    description = serializers.CharField(required=False, allow_blank=True, help_text="상품 설명(원문)")
    features = serializers.ListField(
        child=serializers.CharField(), required=False, help_text="주요 특징(예: 단백질 15g/무설탕/저칼로리)"
    )
    nutrition = serializers.DictField(
        required=False,
        help_text="영양 성분표(단백질/지방/탄수화물/당류/식이섬유/칼슘/철/칼륨/나트륨 등)"
    )
