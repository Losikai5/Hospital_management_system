import math
from io import StringIO
from types import SimpleNamespace
from unittest.mock import patch

from django.core.management import call_command
from django.core.management.base import CommandError
from django.db import connection
from django.db.migrations.executor import MigrationExecutor
from django.test import SimpleTestCase, TransactionTestCase, override_settings

from ai.embeddings import (
    EmbeddingError, GeminiEmbeddingService, format_permission_text,
)
from apps.users.models import Permission, PermissionEmbedding


CONFIG = dict(
    GEMINI_API_KEY="test-key-not-real",
    GEMINI_EMBEDDING_MODEL="gemini-embedding-001",
    GEMINI_EMBEDDING_DIMENSIONS=768,
)


@override_settings(**CONFIG)
class GeminiEmbeddingServiceTests(SimpleTestCase):
    def test_format_preserves_scope(self):
        permission = Permission(code="can_view_appointments", name="View Appointments", description="Assigned appointments")
        self.assertEqual(format_permission_text(permission), "Permission Code: can_view_appointments\nPermission Name: View Appointments\nDescription: Assigned appointments")
        original = format_permission_text(permission)
        permission.code = "can_view_all_appointments"
        self.assertNotEqual(format_permission_text(permission), original)

    def test_model_dimensions_tasks_and_normalization(self):
        for method, task in (("embed_permission", "RETRIEVAL_DOCUMENT"), ("embed_query", "RETRIEVAL_QUERY")):
            with self.subTest(task=task), patch("ai.embeddings.genai.Client") as factory:
                client = factory.return_value.__enter__.return_value
                client.models.embed_content.return_value = SimpleNamespace(embeddings=[SimpleNamespace(values=[2.0] * 768)])
                vector = getattr(GeminiEmbeddingService(), method)("permission text")
                kwargs = client.models.embed_content.call_args.kwargs
                self.assertEqual(kwargs["model"], "gemini-embedding-001")
                self.assertEqual(kwargs["contents"], "permission text")
                self.assertEqual(kwargs["config"].task_type, task)
                self.assertEqual(kwargs["config"].output_dimensionality, 768)
                self.assertEqual(factory.call_args.kwargs["api_key"], "test-key-not-real")
                self.assertFalse(factory.call_args.kwargs["vertexai"])
                self.assertEqual(len(vector), 768)
                self.assertAlmostEqual(math.hypot(*vector), 1)

    def test_invalid_responses_are_rejected(self):
        for values in (None, [], [1.0] * 767, [1.0] * 769, [float("nan")] * 768, [float("inf")] * 768, [0.0] * 768, [True] * 768, ["1"] * 768):
            with self.subTest(values_type=type(values)), patch("ai.embeddings.genai.Client") as factory:
                factory.return_value.__enter__.return_value.models.embed_content.return_value = SimpleNamespace(embeddings=[SimpleNamespace(values=values)])
                with self.assertRaises(EmbeddingError):
                    GeminiEmbeddingService().embed_query("question")

    def test_missing_and_multiple_embeddings_are_rejected(self):
        for embeddings in (None, [], [SimpleNamespace(values=[1.0] * 768)] * 2):
            with patch("ai.embeddings.genai.Client") as factory:
                factory.return_value.__enter__.return_value.models.embed_content.return_value = SimpleNamespace(embeddings=embeddings)
                with self.assertRaises(EmbeddingError):
                    GeminiEmbeddingService().embed_permission("permission")

    def test_api_failure_is_safe(self):
        with patch("ai.embeddings.genai.Client", side_effect=RuntimeError("secret provider payload")):
            with self.assertRaises(EmbeddingError) as error:
                GeminiEmbeddingService().embed_permission("text")
            self.assertNotIn("secret", str(error.exception))

    @override_settings(GEMINI_API_KEY="")
    def test_missing_key_does_not_call_provider(self):
        with patch("ai.embeddings.genai.Client") as client:
            with self.assertRaises(EmbeddingError):
                GeminiEmbeddingService().embed_query("text")
            client.assert_not_called()

    @override_settings(GEMINI_EMBEDDING_DIMENSIONS=1536)
    def test_incompatible_configuration_fails(self):
        with self.assertRaises(EmbeddingError):
            GeminiEmbeddingService()

    def test_empty_input_fails(self):
        with patch("ai.embeddings.genai.Client") as client:
            for text in (None, "", "  ", 5):
                with self.assertRaises(EmbeddingError):
                    GeminiEmbeddingService().embed_query(text)
            client.assert_not_called()


@override_settings(**CONFIG)
class EmbedPermissionsCommandTests(TransactionTestCase):
    def setUp(self):
        self.permission = Permission.objects.create(code="can_view_appointments", name="View Appointments", description="Assigned appointments")
        self.vector = [1 / math.sqrt(768)] * 768
        self.output = StringIO()
        self.errors = StringIO()
        self.client_patch = patch("ai.embeddings.genai.Client")
        self.factory = self.client_patch.start()
        self.addCleanup(self.client_patch.stop)
        self.api = self.factory.return_value.__enter__.return_value.models.embed_content
        self.api.return_value = SimpleNamespace(embeddings=[SimpleNamespace(values=[1.0] * 768)])

    def run_command(self, **kwargs):
        call_command("embed_permissions", stdout=self.output, stderr=self.errors, **kwargs)

    def existing(self, **kwargs):
        fields = dict(permission=self.permission, embedding=self.vector, dimensions=768, model_name="gemini-embedding-001", source_text=format_permission_text(self.permission))
        fields.update(kwargs)
        return PermissionEmbedding.objects.create(**fields)

    def test_creates_valid_vector_outside_api_transaction(self):
        def response(**kwargs):
            self.assertFalse(connection.in_atomic_block)
            return SimpleNamespace(embeddings=[SimpleNamespace(values=[1.0] * 768)])
        self.api.side_effect = response
        self.run_command()
        row = PermissionEmbedding.objects.get(permission=self.permission)
        row.full_clean()
        self.assertEqual(len(row.embedding), 768)
        self.assertEqual(row.model_name, "gemini-embedding-001")
        self.assertEqual(row.source_text, format_permission_text(self.permission))
        self.assertAlmostEqual(math.hypot(*row.embedding), 1, places=5)
        self.assertIn("Created: 1", self.output.getvalue())
        self.assertIn("Failed: 0", self.output.getvalue())

    def test_skips_unchanged_without_api_key(self):
        self.existing()
        with override_settings(GEMINI_API_KEY=""):
            self.run_command()
        self.factory.assert_not_called()
        self.assertIn("Skipped: 1", self.output.getvalue())

    def test_updates_changed_source(self):
        row = self.existing()
        self.permission.description = "Updated scope"
        self.permission.save()
        self.run_command()
        row.refresh_from_db()
        self.assertIn("Updated scope", row.source_text)
        self.assertEqual(PermissionEmbedding.objects.count(), 1)
        self.assertIn("Updated: 1", self.output.getvalue())

    def test_updates_changed_model_and_dimensions_metadata(self):
        row = self.existing(model_name="older-model", dimensions=3072)
        self.run_command()
        row.refresh_from_db()
        self.assertEqual(row.model_name, "gemini-embedding-001")
        self.assertEqual(row.dimensions, 768)
        self.api.assert_called_once()

    def test_force_regenerates(self):
        self.existing()
        self.run_command(force=True)
        self.api.assert_called_once()
        self.assertIn("Updated: 1", self.output.getvalue())

    def test_permission_filter(self):
        Permission.objects.create(code="can_view_all_appointments", name="All", description="All appointments")
        self.run_command(permission=self.permission.code)
        self.assertEqual(PermissionEmbedding.objects.count(), 1)
        self.api.assert_called_once()

    def test_unknown_permission_is_clear_error(self):
        with self.assertRaisesMessage(CommandError, "Unknown permission code"):
            self.run_command(permission="unknown")
        self.factory.assert_not_called()

    def test_failure_preserves_old_vector_and_metadata(self):
        row = self.existing()
        before = PermissionEmbedding.objects.values().get(pk=row.pk)
        self.api.side_effect = RuntimeError("secret payload")
        with self.assertRaises(CommandError):
            self.run_command(force=True)
        self.assertEqual(PermissionEmbedding.objects.values().get(pk=row.pk), before)
        self.assertIn("Failed: 1", self.output.getvalue())
        self.assertNotIn("secret", self.errors.getvalue())

    def test_invalid_vector_never_saved(self):
        self.api.return_value = SimpleNamespace(embeddings=[SimpleNamespace(values=[1.0])])
        with self.assertRaises(CommandError):
            self.run_command()
        self.assertFalse(PermissionEmbedding.objects.exists())

    def test_continues_after_failure_and_counts_results(self):
        Permission.objects.create(code="zzz", name="Another", description="Other scope")
        self.api.side_effect = [RuntimeError("failed"), SimpleNamespace(embeddings=[SimpleNamespace(values=[1.0] * 768)])]
        with self.assertRaises(CommandError):
            self.run_command()
        self.assertEqual(PermissionEmbedding.objects.get().permission.code, "zzz")
        self.assertIn("Failed: 1", self.output.getvalue())
        self.assertIn("Created: 1", self.output.getvalue())

    def test_permission_change_during_api_call_preserves_old_embedding(self):
        row = self.existing()
        before = row.source_text
        def changed(**kwargs):
            Permission.objects.filter(pk=self.permission.pk).update(description="Changed concurrently")
            return SimpleNamespace(embeddings=[SimpleNamespace(values=[1.0] * 768)])
        self.api.side_effect = changed
        with self.assertRaises(CommandError):
            self.run_command(force=True)
        row.refresh_from_db()
        self.assertEqual(row.source_text, before)
        self.assertIn("Permission changed", self.errors.getvalue())

    def test_empty_catalog(self):
        self.permission.delete()
        self.run_command()
        self.factory.assert_not_called()
        self.assertIn("Created: 0", self.output.getvalue())

    def test_database_field_is_vector_768(self):
        with connection.cursor() as cursor:
            cursor.execute("SELECT format_type(atttypid, atttypmod) FROM pg_attribute WHERE attrelid = 'users_permissionembedding'::regclass AND attname = 'embedding'")
            self.assertEqual(cursor.fetchone()[0], "vector(768)")


class PermissionEmbeddingMigrationTests(TransactionTestCase):
    def test_json_vector_round_trip(self):
        old = [("users", "0012_permissionembedding")]
        new = [("users", "0013_permissionembedding_vector")]
        executor = MigrationExecutor(connection)
        executor.migrate(old)
        try:
            apps = executor.loader.project_state(old).apps
            permission = apps.get_model("users", "Permission").objects.create(code="migration_test", name="Migration", description="Scope")
            legacy = apps.get_model("users", "PermissionEmbedding").objects.create(permission=permission, embedding=[0.5] * 768, dimensions=768, model_name="gemini-embedding-001", source_text="original")
            MigrationExecutor(connection).migrate(new)
            row = PermissionEmbedding.objects.get(pk=legacy.pk)
            self.assertEqual(list(row.embedding), [0.5] * 768)
            self.assertEqual(row.source_text, "original")
            MigrationExecutor(connection).migrate(old)
            old_row = apps.get_model("users", "PermissionEmbedding").objects.get(pk=legacy.pk)
            self.assertEqual(old_row.embedding, [0.5] * 768)
        finally:
            MigrationExecutor(connection).migrate(new)
