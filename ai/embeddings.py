"""Gemini embeddings for permission discovery, never authorization decisions."""

import math
from numbers import Real

from django.conf import settings
from google import genai
from google.genai import types

EMBEDDING_DIMENSIONS = 768


class EmbeddingError(Exception):
    """Safe, user-facing embedding failure without provider response details."""


def format_permission_text(permission):
    return (
        f"Permission Code: {permission.code}\n"
        f"Permission Name: {permission.name}\n"
        f"Description: {permission.description}"
    )


def validate_embedding(values, dimensions=EMBEDDING_DIMENSIONS):
    """Return finite floats; accept pgvector's numpy arrays as well as lists."""
    if hasattr(values, "tolist"):
        values = values.tolist()
    if not isinstance(values, (list, tuple)) or len(values) != dimensions:
        raise EmbeddingError(f"Expected exactly {dimensions} embedding dimensions.")
    if any(isinstance(v, bool) or not isinstance(v, Real) for v in values):
        raise EmbeddingError("Embedding values must be finite numbers.")
    try:
        vector = [float(v) for v in values]
    except (ValueError, OverflowError):
        raise EmbeddingError("Embedding values must be finite numbers.") from None
    if not all(math.isfinite(v) for v in vector):
        raise EmbeddingError("Embedding values must be finite numbers.")
    norm = math.hypot(*vector)
    if not math.isfinite(norm) or norm == 0:
        raise EmbeddingError("Embedding must have a finite, non-zero norm.")
    return vector


class GeminiEmbeddingService:
    def __init__(self):
        self.model_name = settings.GEMINI_EMBEDDING_MODEL
        self.dimensions = settings.GEMINI_EMBEDDING_DIMENSIONS
        if self.dimensions != EMBEDDING_DIMENSIONS:
            raise EmbeddingError("GEMINI_EMBEDDING_DIMENSIONS must be 768 for the current database schema.")
        if not isinstance(self.model_name, str) or not self.model_name.strip():
            raise EmbeddingError("GEMINI_EMBEDDING_MODEL must be configured.")

    def _embed(self, text, task_type):
        if not isinstance(text, str) or not text.strip():
            raise EmbeddingError("Embedding text must be a non-empty string.")
        if not settings.GEMINI_API_KEY:
            raise EmbeddingError("GEMINI_API_KEY is not configured.")
        try:
            # Explicit Developer API mode avoids ambient Vertex configuration.
            # The SDK timeout is milliseconds; close connections after each call.
            with genai.Client(
                api_key=settings.GEMINI_API_KEY,
                vertexai=False,
                http_options=types.HttpOptions(timeout=30000),
            ) as client:
                response = client.models.embed_content(
                    model=self.model_name,
                    contents=text,
                    config=types.EmbedContentConfig(
                        task_type=task_type,
                        output_dimensionality=self.dimensions,
                    ),
                )
        except Exception:
            # Provider exceptions can include request text or credentials.
            raise EmbeddingError("Gemini embedding request failed; check service availability and API configuration.") from None
        embeddings = getattr(response, "embeddings", None)
        if not embeddings or len(embeddings) != 1:
            raise EmbeddingError("Gemini returned an incomplete embedding response.")
        vector = validate_embedding(getattr(embeddings[0], "values", None), self.dimensions)
        # gemini-embedding-001 needs normalization for reduced output dimensions.
        norm = math.hypot(*vector)
        return [value / norm for value in vector]

    def embed_permission(self, text: str) -> list[float]:
        return self._embed(text, "RETRIEVAL_DOCUMENT")

    def embed_query(self, text: str) -> list[float]:
        return self._embed(text, "RETRIEVAL_QUERY")


def embed_permission(text: str) -> list[float]:
    return GeminiEmbeddingService().embed_permission(text)


def embed_query(text: str) -> list[float]:
    return GeminiEmbeddingService().embed_query(text)
