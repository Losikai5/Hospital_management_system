# Gemini permission embeddings

Implemented 27 October 2026. This stage generates and stores permission embeddings only. It does not search them, authorize users, or connect them to LangGraph. Existing AI SQL blocking remains in place.

## Files

| File | Purpose |
| --- | --- |
| `ai/embeddings.py` | Official Google Gen AI SDK integration, permission text formatting, response validation and normalization |
| `apps/users/management/commands/embed_permissions.py` | Repeatable generation command with skip/update/failure handling |
| `apps/users/models.py` | Reuses `PermissionEmbedding`; changes its JSON field to `VectorField(dimensions=768)` and updates model validation |
| `apps/users/migrations/0013_permissionembedding_vector.py` | Converts existing JSON vectors through their text representation to PostgreSQL `vector(768)` |
| `apps/users/test_embeddings.py` | Mocked SDK tests, real PostgreSQL command tests and reversible migration test |
| `config/settings.py` | Gemini key, model and dimensions configuration |
| `.env.example` | Documents Gemini environment variables |
| `requirements.txt` | Pins `google-genai==2.33.0` and `pgvector==0.5.1` |
| `GEMINI_PERMISSION_EMBEDDINGS.md` | Setup, operation, validation and limitations |

The existing `0012_permissionembedding` migration still creates the original model. Migration 0013 alters it; it creates no duplicate model or permission records. The one-to-one permission relationship allows one current embedding per permission, which is stricter than one per permission/model. Changing model configuration replaces that permission's vector.

## Installation and configuration

Use the project virtual environment:

```bash
venv/bin/python -m pip install -r requirements.txt
```

For an existing environment needing only these additions:

```bash
venv/bin/python -m pip install google-genai==2.33.0 pgvector==0.5.1
```

Set these values in `.env` or your deployment environment:

```dotenv
GEMINI_API_KEY=your-api-key
GEMINI_EMBEDDING_MODEL=gemini-embedding-001
GEMINI_EMBEDDING_DIMENSIONS=768
```

The implementation also accepts the previously configured `EMBEDDING_DIMENSION` as a fallback. `GEMINI_EMBEDDING_DIMENSIONS` takes precedence. No real `.env` values were changed. Never commit the real key.

The dimension count must remain 768 for this schema. Other values are rejected before making API requests. A future dimension change needs a deliberate field migration and full re-embedding. Model name changes are detected and regenerate stored embeddings.

## Migration

```bash
venv/bin/python manage.py migrate users
```

Migration 0013 ensures the vector extension exists, then performs a transactional conversion from JSON to `vector(768)`. Existing well-formed 768-element arrays are preserved, along with source text and model metadata. Invalid existing vectors cause migration failure rather than silent deletion or truncation; correct such rows before retrying. Reversing the migration converts vectors back to JSON and leaves the shared extension installed.

The pgvector server extension must be installed on PostgreSQL. If it is already enabled, the extension operation is a no-op. Otherwise the migration user needs permission to enable it. No application-database migrations were applied during implementation.

The repository also has a pre-existing empty `UserPermission` model without a migration. That unrelated drift was not included or fixed here. It may still appear in `makemigrations --check`; the `PermissionEmbedding` model and migrations match.

## Service behavior

`GeminiEmbeddingService.embed_permission(text)` uses `RETRIEVAL_DOCUMENT` and `embed_query(text)` uses `RETRIEVAL_QUERY`. Module-level functions with the same names are also available. Both call `client.models.embed_content()` with the configured model and `EmbedContentConfig(output_dimensionality=768)`.

The client is created only when an embedding is needed, using the explicit API key and Developer API mode. Requests have a 30-second SDK timeout. Responses must contain one embedding with exactly 768 finite numeric values and a nonzero finite norm. The service normalizes the returned vector to unit length, as needed for reduced-dimensional `gemini-embedding-001` vectors. Provider failures produce sanitized `EmbeddingError` messages; raw responses, credentials and input text are not logged.

`format_permission_text()` combines the exact code, name and description, preserving the distinction between self/assigned and all-record permissions. Only catalog text is sent by the command. No patient records are read or sent.

References: [Google Gen AI Python SDK](https://github.com/googleapis/python-genai), [Gemini embedding documentation](https://ai.google.dev/gemini-api/docs/embeddings), [pgvector Django integration](https://github.com/pgvector/pgvector-python).

## Running the command

```bash
venv/bin/python manage.py embed_permissions
venv/bin/python manage.py embed_permissions --permission can_view_appointments
venv/bin/python manage.py embed_permissions --force
```

The command processes existing permissions, including inactive catalog entries; it does not assign any permissions. Future retrieval must filter active permissions independently. Unknown codes fail before an API request.

A valid stored vector with unchanged source text, model name and dimension metadata is skipped. Changes regenerate it; `--force` always regenerates. Progress and Created/Updated/Skipped/Failed counts reflect actual processed records. Unchanged records can be skipped even without an API key.

The external request happens outside a database transaction. After success, the command locks the permission row, verifies its text has not changed during the API call, validates the new record and saves it in a short transaction. API/validation/storage failures leave an existing embedding unchanged, continue to other permissions and produce a nonzero exit status after the summary. Re-running retries failed entries and skips successful unchanged ones. Concurrent commands serialize writes on the parent permission row; they may make redundant API calls, but cannot create duplicate embedding rows. Different concurrently running model configurations should be avoided; the last successful writer wins.

These commands will call Gemini and may consume quota. They were not run against the application's live catalog during implementation.

## Verification

After migration and generation, use Django shell:

```bash
venv/bin/python manage.py shell
```

```python
from apps.users.models import Permission, PermissionEmbedding

print("Permissions:", Permission.objects.count())
print("Embeddings:", PermissionEmbedding.objects.count())
print("Missing:", Permission.objects.filter(embedding__isnull=True).count())

record = PermissionEmbedding.objects.get(permission__code="can_view_appointments")
record.full_clean()
print(record.permission.code, record.model_name, record.dimensions, len(record.embedding))
```

The length and dimension metadata should both be 768. Re-running the generation command without changes should report skipped records with no Gemini calls. This verifies storage/configuration, not semantic search accuracy or authorization.

## Automated tests

```bash
venv/bin/python manage.py test apps.users.test_embeddings ai
```

Run against a test PostgreSQL server with pgvector installed and an account permitted to create a test database. All SDK calls are mocked; tests need no real Gemini key or paid calls. Database tests intentionally use PostgreSQL rather than SQLite to exercise actual vector storage and migrations.

Validation during implementation used a separate PostgreSQL 18 cluster under `/tmp` and a test-only settings override. The application database was not used. Coverage includes text formatting, model/task/dimension selection, normalization, invalid response handling, creation, changed source/configuration, unchanged skips, forced regeneration, filtering/unknown codes, failure preservation, partial failure counts, concurrent source changes, physical vector column type and JSON/vector migration round-trip. Existing AI security tests are included.

## Remaining boundaries

- Gemini key validity, billing/quota, model availability for this account and live API connectivity are not verified by mocked tests.
- No semantic search, vector index, LangGraph integration or authorization behavior was introduced. Similarity must never grant access.
- The command is sequential and has no application-level resume queue or rate-limit scheduler. Safe reruns provide recovery; the SDK may apply its own retry behavior.
- Model `clean()` validation follows Django conventions; arbitrary direct ORM saves do not automatically call it. This command explicitly calls `full_clean()`, and PostgreSQL enforces the vector field's dimensions.
- Existing unrelated dependency/deployment gaps from the architecture audit remain outside this change.
