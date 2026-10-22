"""Embedding dense e5-small — model dimuat sekali, awalan query/passage."""
from functools import lru_cache

from sentence_transformers import SentenceTransformer

from app.core.config import settings

QUERY_PREFIX = "query: "
PASSAGE_PREFIX = "passage: "


@lru_cache(maxsize=1)
def get_model() -> SentenceTransformer:
    """Muat model embedding sekali (mahal). Cache menghindari load berulang."""
    return SentenceTransformer(settings.embedding_model)


def embed_query(text: str) -> list[float]:
    """Encode satu kueri → vektor 384-dimensi (ternormalisasi)."""
    return get_model().encode(QUERY_PREFIX + text, normalize_embeddings=True).tolist()


def embed_passages(texts: list[str]) -> list[list[float]]:
    """Encode banyak potongan dokumen sekaligus (lebih cepat dari satu-satu)."""
    vecs = get_model().encode(
        [PASSAGE_PREFIX + t for t in texts], normalize_embeddings=True
    )
    return [v.tolist() for v in vecs]