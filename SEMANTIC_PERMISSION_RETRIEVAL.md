# Semantic permission retrieval

This stage retrieves candidates only. It does not authorize users, execute hospital operations, change grants, enable AI SQL, or connect retrieval to LangGraph.

## Files

- `ai/permission_search.py`: reusable `search_permissions()` service and structured result type.
- `apps/users/management/commands/search_permissions.py`: manual retrieval command.
- `apps/users/test_permission_search.py`: validation, mocked Gemini and real pgvector integration tests.
- `config/settings.py`: configurable minimum cosine similarity.
- `.env.example`: documents the cutoff.
- `SEMANTIC_PERMISSION_RETRIEVAL.md`: usage, testing and limitations.

The existing `ai/embeddings.py`, `embed_permissions` command, permission models and vector migrations were inspected and reused. Their tests were rerun alongside retrieval tests. No new models, migrations or dependencies are required for this stage.

## Usage

```python
from ai.permission_search import search_permissions

candidates = search_permissions("Show me my appointments", limit=5)
# Each result contains permission_code, permission_name, description, similarity.
```

```bash
venv/bin/python manage.py search_permissions "Show me my appointments"
venv/bin/python manage.py search_permissions "Show all hospital appointments" --limit 5
venv/bin/python manage.py search_permissions "Cancel my appointment" --limit 3 --min-similarity 0.6
```

The CLI prints the query, codes, names, descriptions and calculated similarity scores. Do not put patient records or secrets in command arguments; shell history may retain them, and the supplied query is sent to Gemini. No live calls were made during implementation.

## Retrieval behavior

1. Validate a nonempty string, a result limit of 1–100 (default 5), and a finite similarity cutoff between 0 and 1.
2. Select embeddings belonging to active permissions, matching the configured embedding model and 768-dimensional metadata. Require `source_text` to match the permission's current code, name and description using the same format as the embedding command. Stale or incompatible vectors are excluded before limiting results.
3. If there are no eligible embeddings, return an empty list without an API call. Permissions lacking embeddings are not invented or substituted.
4. Reuse `GeminiEmbeddingService.embed_query()`, which calls the Google Gen AI SDK with `RETRIEVAL_QUERY` and `output_dimensionality=768`, validates the vector and normalizes it.
5. Annotate the Django queryset with `CosineDistance("embedding", vector)`. Filter by `distance <= 1 - min_similarity`, order ascending by distance and then permission code for deterministic ties, and apply the limit in PostgreSQL.
6. Return `similarity = 1 - distance` from the actual pgvector result, clamped for floating-point rounding. Nonfinite distances do not become candidates. Higher similarity ranks first; this is not a probability or an authorization score.

No own/all-scope remapping is performed. Both scope codes may appear, each with its actual catalog description and independent score. The approved operation and backend scope policy must eventually determine which permissions are required.

## Configuration and prerequisites

The previous embedding-stage requirements remain:

```dotenv
GEMINI_API_KEY=your-api-key
GEMINI_EMBEDDING_MODEL=gemini-embedding-001
GEMINI_EMBEDDING_DIMENSIONS=768
PERMISSION_SEARCH_MIN_SIMILARITY=0.5
```

The optional Python `min_similarity` argument or CLI `--min-similarity` overrides the configured cutoff for that search. The initial 0.5 cutoff is a tunable heuristic, not a measured relevance guarantee. Calibrate it against labeled hospital questions before integrating with an assistant. Low thresholds can admit unrelated candidates; high thresholds can omit necessary candidates. There is no unconditional nearest-neighbor fallback below the cutoff.

If the embedding-stage setup has not been applied to the application database:

```bash
venv/bin/python -m pip install -r requirements.txt
venv/bin/python manage.py migrate users
venv/bin/python manage.py embed_permissions
```

These prerequisite commands are from the previous stage, not automatic actions performed by retrieval. PostgreSQL must have pgvector installed, migration 0013 must be applied and current permission embeddings must exist. Re-run `embed_permissions` after editing permission text or changing the model. Retrieval itself performs no writes. A missing table/extension or another storage failure raises a sanitized `PermissionSearchError`; Gemini failures propagate as sanitized `EmbeddingError`. Invalid arguments raise `ValueError`. The CLI converts these to `CommandError` with nonzero exit status.

## Tests

```bash
venv/bin/python manage.py test apps.users.test_permission_search apps.users.test_embeddings ai
```

Use a PostgreSQL test database with pgvector and test-database creation rights. During implementation, tests used a separate local PostgreSQL 18 cluster under `/tmp`; the application database was not queried or migrated. Gemini is mocked. Synthetic 768-dimensional vectors verify real PostgreSQL cosine ordering and computed scores, not semantic performance of the Gemini model.

Coverage includes input validation, task/model/dimension configuration, actual vector ordering, reversed ranking when the query vector changes, active filtering, stale and incompatible embedding exclusion, default/custom limits, deterministic ties, missing embeddings, no-match cutoff behavior, zero-vector handling, API errors, distinct own/all scopes, CLI output and absence of writes/authorization calls. Previous embedding storage/migration and AI security tests are included.

## Boundaries for the next stage

The service interface is ready for future LangGraph integration as a candidate retriever. It does not establish that every required permission has been retrieved. A missing candidate, empty result or stale catalog must not become permission to execute an operation.

Authorization and scope validation must remain server-defined, use current HMS permission rules, and run independently of similarity. The existing public/authenticated graph routing and disabled raw SQL executor are unchanged.

Remaining limitations: no live API/account validation or labeled semantic-quality evaluation; initial cutoff is uncalibrated; no approximate vector index (exact search is appropriate for the small current catalog); no multi-operation requirement planner; no user-grant filtering or authorization decision. Missing/incompatible/stale embeddings all produce fewer or no results, so catalog coverage must be checked separately. Queries consume Gemini quota when eligible embeddings exist. The pre-existing unrelated `UserPermission` migration drift and deployment issues are not addressed by this stage.
