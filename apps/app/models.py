# apps/app/models.py
from django.db import models
from django.contrib.postgres.fields import ArrayField
from pgvector.django import VectorField

# ── 세션(온보딩 입력, 타깃 규칙, 의도) ─────────────────────────────
class Session(models.Model):
    session_key = models.CharField(max_length=255, unique=True, null=True, blank=True)
    onboarding   = models.JSONField(default=dict, blank=True)
    target_rules = models.JSONField(default=dict, blank=True)
    intent       = models.JSONField(default=dict, blank=True)
    created_at   = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Session({self.id}, key={self.session_key})"

# ── 상품 메타(카탈로그) ───────────────────────────────────────────
class ProductMeta(models.Model):
    external_id = models.CharField(max_length=255, unique=True)  # 외부 상품ID
    name        = models.CharField(max_length=255)
    keywords    = ArrayField(models.TextField(), default=list, blank=True)
    category    = models.CharField(max_length=100, db_index=True)
    price       = models.IntegerField(db_index=True)
    image_url   = models.TextField(blank=True, default="")
    description = models.TextField(blank=True, default="")
    detail_url  = models.TextField(blank=True, default="")
    created_at  = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name}"

# ── 영양 정보(1:1) ────────────────────────────────────────────────
class ProductNutrition(models.Model):
    product = models.OneToOneField(ProductMeta, on_delete=models.CASCADE, related_name="nutrition")
    facts   = models.JSONField(default=dict)  # 예: {"sugar_g": 3.2, "protein_g": 10, ...}

# ── 텍스트 임베딩(1:1, pgvector) ─────────────────────────────────
class ProductEmbedding(models.Model):
    product   = models.OneToOneField(ProductMeta, on_delete=models.CASCADE, related_name="embedding")
    embedding = VectorField(dimensions=768)  # pgvector 필드

# ── 추천 결과(세션별 기록) ────────────────────────────────────────
class RecommendResult(models.Model):
    session = models.ForeignKey(Session, on_delete=models.CASCADE, related_name="results")
    product = models.ForeignKey(ProductMeta, on_delete=models.CASCADE)
    purpose = ArrayField(models.TextField(), default=list, blank=True)
    score   = models.FloatField()
    why     = models.TextField(blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=["session", "-score"]),
            models.Index(fields=["product"]),
        ]