# 임베딩 서비스 (간이 해시 임베딩; 추후 실제 모델로 교체 가능)
from __future__ import annotations
from typing import List
import numpy as np
import hashlib

EMBED_DIM = 768  # ProductEmbedding.dimensions 와 동일해야 함

class EmbeddingService:
    """
    get_embedding(text) -> 고정 차원(768)의 numpy 벡터를 반환.
    현재는 의존성 없이 동작하도록 해시기반 임베딩을 사용.
    추후 sentence-transformers / OpenAI 등으로 교체해도 인터페이스 동일.
    """

    def __init__(self, dim: int = EMBED_DIM):
        self.dim = dim

    def _hash_token(self, token: str) -> np.ndarray:
        h = hashlib.sha256(token.encode("utf-8")).digest()
        # 32바이트를 dim 길이로 반복/잘라서 분산
        arr = np.frombuffer((h * ((self.dim // len(h)) + 1))[: self.dim], dtype=np.uint8).astype(np.float32)
        # 0~255 -> -0.5 ~ 0.5 스케일
        arr = (arr / 255.0) - 0.5
        return arr

    def get_embedding(self, text: str) -> np.ndarray:
        if not text:
            return np.zeros(self.dim, dtype=np.float32)
        tokens = [t for t in text.replace("/", " ").replace(",", " ").split() if t.strip()]
        if not tokens:
            return np.zeros(self.dim, dtype=np.float32)
        vecs = [self._hash_token(t.lower()) for t in tokens]
        v = np.mean(vecs, axis=0)
        # L2 정규화
        n = np.linalg.norm(v)
        return v / n if n else v
