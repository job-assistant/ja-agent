import numpy as np
from typing import List, Optional, Union
from sentence_transformers import SentenceTransformer
import logging
import torch

from app.core.config import settings


class BGEEmbedder:
    """BGE-M3 임베더"""

    def __init__(self, model_name: str = None, device: Optional[str] = None):
        self.model_name = model_name or settings.EMBEDDING_MODEL
        self.model: Optional[SentenceTransformer] = None
        self.device = device or ("cuda" if torch.cuda.is_available() else "cpu")
        self.logger = logging.getLogger(__name__)

    def _load_model(self):
        if self.model is None:
            try:
                self.logger.info(f"{self.model_name} 모델 로딩 중... (device: {self.device})")
                self.model = SentenceTransformer(
                    self.model_name,
                    device=self.device,
                    trust_remote_code=True
                )
                self.logger.info(f"{self.model_name} 모델 로딩 완료")
            except Exception as e:
                self.logger.error(f"모델 로딩 실패: {e}")
                raise

    def get_embeddings(self, texts: Union[str, List[str]]) -> Union[np.ndarray, List[np.ndarray]]:
        self._load_model()
        try:
            if isinstance(texts, str):
                embeddings = self.model.encode([texts], normalize_embeddings=True)
                return embeddings[0]
            embeddings = self.model.encode(texts, normalize_embeddings=True)
            return embeddings
        except Exception as e:
            self.logger.error(f"임베딩 생성 실패: {e}")
            raise

    def encode_query(self, query: str) -> np.ndarray:
        return self.get_embeddings(f"query: {query}")

    def encode_passage(self, text: str) -> np.ndarray:
        return self.get_embeddings(f"passage: {text}")

    def encode_passages(self, texts: List[str], batch_size: int = 32) -> List[np.ndarray]:
        prefixed_texts = [f"passage: {text}" for text in texts]
        self._load_model()
        all_embeddings = []
        for i in range(0, len(prefixed_texts), batch_size):
            batch = prefixed_texts[i:i + batch_size]
            try:
                batch_embeddings = self.model.encode(
                    batch, normalize_embeddings=True, batch_size=batch_size
                )
                all_embeddings.extend(batch_embeddings)
                processed = min(i + batch_size, len(prefixed_texts))
                self.logger.info(f"임베딩 진행률: {processed}/{len(prefixed_texts)} ({processed/len(prefixed_texts)*100:.1f}%)")
            except Exception as e:
                self.logger.error(f"배치 {i//batch_size + 1} 처리 실패: {e}")
                all_embeddings.extend([None] * len(batch))
        return all_embeddings

    def get_embedding_dimension(self) -> int:
        self._load_model()
        return self.model.get_sentence_embedding_dimension()

    def unload_model(self):
        if self.model is not None:
            del self.model
            self.model = None
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
            self.logger.info("BGE-M3 모델이 메모리에서 해제되었습니다.")