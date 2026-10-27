"""Retrieve permission candidates only; never determine or grant authorization."""

import math
from numbers import Real
from typing import TypedDict

from django.conf import settings
from django.db import DatabaseError
from django.db.models import F, Value
from django.db.models.functions import Concat
from pgvector.django import CosineDistance

from ai.embeddings import GeminiEmbeddingService, validate_embedding
from apps.users.models import PermissionEmbedding


class PermissionCandidate(TypedDict):
    permission_code: str
    permission_name: str
    description: str
    similarity: float


class PermissionSearchError(Exception):
    """Safe storage error for callers; provider failures use EmbeddingError."""


def search_permissions(
    question: str, limit: int = 5, *, min_similarity: float | None = None
) -> list[PermissionCandidate]:
    """Rank active, current catalog entries. Scores do not prove relevance/scope.

    No fallback is returned when the similarity cutoff rejects every candidate.
    Missing embeddings are ignored; callers must not infer requirement completeness.
    """
    if not isinstance(question, str) or not question.strip():
        raise ValueError("Question must be a non-empty string.")
    if isinstance(limit, bool) or not isinstance(limit, int) or not 1 <= limit <= 100:
        raise ValueError("Limit must be an integer between 1 and 100.")
    if min_similarity is None:
        min_similarity = settings.PERMISSION_SEARCH_MIN_SIMILARITY
    if (
        isinstance(min_similarity, bool)
        or not isinstance(min_similarity, Real)
        or not math.isfinite(min_similarity)
        or not 0 <= min_similarity <= 1
    ):
        raise ValueError("Minimum similarity must be a finite number between 0 and 1.")

    service = GeminiEmbeddingService()
    # Exact same format as format_permission_text(), evaluated in SQL so stale
    # entries cannot consume the result limit or silently describe a new scope.
    current_text = Concat(
        Value("Permission Code: "), F("permission__code"),
        Value("\nPermission Name: "), F("permission__name"),
        Value("\nDescription: "), F("permission__description"),
    )
    candidates = PermissionEmbedding.objects.filter(
        permission__is_active=True,
        model_name=service.model_name,
        dimensions=service.dimensions,
        source_text=current_text,
    )
    try:
        if not candidates.exists():
            return []
    except DatabaseError:
        raise PermissionSearchError("Permission search storage is unavailable; check PostgreSQL and embedding migrations.") from None

    # Reuse the existing RETRIEVAL_QUERY / 768-dimensional Gemini path.
    vector = validate_embedding(service.embed_query(question.strip()), service.dimensions)
    try:
        rows = list(
            candidates.annotate(distance=CosineDistance("embedding", vector))
            .filter(distance__lte=1.0 - min_similarity)
            .order_by("distance", "permission__code")
            .values("permission__code", "permission__name", "permission__description", "distance")[:limit]
        )
    except DatabaseError:
        raise PermissionSearchError("Permission similarity search failed; check PostgreSQL and pgvector availability.") from None
    return [
        {
            "permission_code": row["permission__code"],
            "permission_name": row["permission__name"],
            "description": row["permission__description"],
            "similarity": max(-1.0, min(1.0, 1.0 - float(row["distance"]))),
        }
        for row in rows
        if row["distance"] is not None and math.isfinite(row["distance"])
    ]
