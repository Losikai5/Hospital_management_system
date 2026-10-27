from io import StringIO
from types import SimpleNamespace
from unittest.mock import patch

from django.core.management import call_command
from django.core.management.base import CommandError
from django.db import DatabaseError
from django.test import SimpleTestCase, TestCase, override_settings

from ai.embeddings import EmbeddingError, format_permission_text
from ai.permission_search import PermissionSearchError, search_permissions
from apps.users.models import Permission, PermissionEmbedding


CONFIG = dict(
    GEMINI_API_KEY="test-only",
    GEMINI_EMBEDDING_MODEL="gemini-embedding-001",
    GEMINI_EMBEDDING_DIMENSIONS=768,
    PERMISSION_SEARCH_MIN_SIMILARITY=0.5,
)


def vector(x=1.0, y=0.0):
    return [x, y] + [0.0] * 766


@override_settings(**CONFIG)
class PermissionSearchValidationTests(SimpleTestCase):
    def test_invalid_inputs_fail_before_api_or_database(self):
        for question in (None, "", " \n ", [], 1):
            with self.assertRaises(ValueError):
                search_permissions(question)
        for limit in (0, -1, 101, 1.5, True, "5"):
            with self.assertRaises(ValueError):
                search_permissions("question", limit=limit)
        for cutoff in (-0.1, 1.1, float("nan"), float("inf"), True, "0.5"):
            with self.assertRaises(ValueError):
                search_permissions("question", min_similarity=cutoff)

    def test_storage_error_is_sanitized(self):
        with patch("django.db.models.query.QuerySet.exists", side_effect=DatabaseError("private connection details")):
            with self.assertRaises(PermissionSearchError) as error:
                search_permissions("question")
        self.assertNotIn("private", str(error.exception))


@override_settings(**CONFIG)
class PermissionSearchTests(TestCase):
    def setUp(self):
        self.sdk_patch = patch("ai.embeddings.genai.Client")
        self.factory = self.sdk_patch.start()
        self.addCleanup(self.sdk_patch.stop)
        self.api = self.factory.return_value.__enter__.return_value.models.embed_content
        self.api.return_value = SimpleNamespace(embeddings=[SimpleNamespace(values=vector())])

    def add_permission(self, code, values=None, active=True, **metadata):
        permission = Permission.objects.create(
            code=code, name=code.replace("_", " "), description=f"Scope for {code}", is_active=active,
        )
        if values is not None:
            fields = dict(
                permission=permission, embedding=values, dimensions=768,
                model_name="gemini-embedding-001", source_text=format_permission_text(permission),
            )
            fields.update(metadata)
            PermissionEmbedding.objects.create(**fields)
        return permission

    def test_actual_cosine_ranking_and_query_configuration(self):
        self.add_permission("can_view_all_appointments", vector(0.8, 0.6))
        self.add_permission("can_view_appointments", vector())
        results = search_permissions(" Show my appointments ")
        self.assertEqual([r["permission_code"] for r in results], ["can_view_appointments", "can_view_all_appointments"])
        self.assertAlmostEqual(results[0]["similarity"], 1)
        self.assertAlmostEqual(results[1]["similarity"], 0.8, places=5)
        self.assertEqual(set(results[0]), {"permission_code", "permission_name", "description", "similarity"})
        kwargs = self.api.call_args.kwargs
        self.assertEqual(kwargs["model"], "gemini-embedding-001")
        self.assertEqual(kwargs["contents"], "Show my appointments")
        self.assertEqual(kwargs["config"].task_type, "RETRIEVAL_QUERY")
        self.assertEqual(kwargs["config"].output_dimensionality, 768)

    def test_ranking_changes_with_query_vector_not_hardcoded_scope(self):
        self.add_permission("can_view_appointments", vector())
        self.add_permission("can_view_all_appointments", vector(0, 1))
        self.api.return_value = SimpleNamespace(embeddings=[SimpleNamespace(values=vector(0, 1))])
        results = search_permissions("Show all hospital appointments")
        self.assertEqual([r["permission_code"] for r in results], ["can_view_all_appointments"])

    def test_inactive_permissions_excluded(self):
        self.add_permission("inactive", vector(), active=False)
        self.add_permission("active", vector(0.8, 0.6))
        self.assertEqual([r["permission_code"] for r in search_permissions("question")], ["active"])

    def test_default_and_custom_limits_with_deterministic_ties(self):
        for i in range(7):
            self.add_permission(f"permission_{i}", vector())
        self.assertEqual(len(search_permissions("question")), 5)
        self.assertEqual([r["permission_code"] for r in search_permissions("question", limit=2)], ["permission_0", "permission_1"])
        self.assertEqual(len(search_permissions("question", limit=10)), 7)

    def test_missing_embeddings_return_empty_without_api_call(self):
        self.add_permission("missing")
        self.assertEqual(search_permissions("question"), [])
        self.factory.assert_not_called()

    def test_empty_catalog(self):
        self.assertEqual(search_permissions("question"), [])
        self.factory.assert_not_called()

    def test_missing_embedding_does_not_hide_available_candidates(self):
        self.add_permission("missing")
        self.add_permission("available", vector())
        self.assertEqual([r["permission_code"] for r in search_permissions("question")], ["available"])

    def test_incompatible_and_stale_embeddings_excluded_before_limit(self):
        self.add_permission("wrong_model", vector(), model_name="other-model")
        self.add_permission("wrong_dimensions", vector(), dimensions=3072)
        stale = self.add_permission("stale", vector())
        stale.description = "New scope"
        stale.save()
        self.add_permission("current", vector(0.8, 0.6))
        self.assertEqual([r["permission_code"] for r in search_permissions("question", limit=1)], ["current"])

    def test_custom_cutoff_and_no_unsuitable_fallback(self):
        self.add_permission("orthogonal", vector(0, 1))
        self.add_permission("moderate", vector(0.6, 0.8))
        self.assertEqual(search_permissions("question", min_similarity=0.9), [])
        self.assertEqual([r["permission_code"] for r in search_permissions("question")], ["moderate"])
        with override_settings(PERMISSION_SEARCH_MIN_SIMILARITY=0.9):
            self.assertEqual(search_permissions("question"), [])

    def test_zero_vector_does_not_become_a_match(self):
        self.add_permission("zero", vector(0, 0))
        self.assertEqual(search_permissions("question"), [])

    def test_api_failure_propagates_safely(self):
        self.add_permission("current", vector())
        self.api.side_effect = RuntimeError("secret response")
        with self.assertRaises(EmbeddingError) as error:
            search_permissions("question")
        self.assertNotIn("secret", str(error.exception))

    def test_wrong_query_dimensions_rejected(self):
        self.add_permission("current", vector())
        self.api.return_value = SimpleNamespace(embeddings=[SimpleNamespace(values=[1.0] * 767)])
        with self.assertRaises(EmbeddingError):
            search_permissions("question")

    def test_command_displays_actual_scores_and_limit(self):
        self.add_permission("own", vector())
        self.add_permission("all", vector(0.8, 0.6))
        output = StringIO()
        call_command("search_permissions", "Show my appointments", limit=1, stdout=output)
        self.assertIn("1. own", output.getvalue())
        self.assertIn("similarity: 1.000000", output.getvalue())
        self.assertNotIn("2. all", output.getvalue())
        self.assertIn("not authorization decisions", output.getvalue())

    def test_command_no_results_and_errors(self):
        output = StringIO()
        call_command("search_permissions", "question", stdout=output)
        self.assertIn("No suitable candidates", output.getvalue())
        with self.assertRaises(CommandError):
            call_command("search_permissions", "question", limit=0, stdout=StringIO())
        self.add_permission("current", vector())
        self.api.side_effect = RuntimeError("secret")
        with self.assertRaises(CommandError) as error:
            call_command("search_permissions", "question", stdout=StringIO())
        self.assertNotIn("secret", str(error.exception))

    def test_retrieval_does_not_write_or_authorize(self):
        self.add_permission("own", vector())
        with patch.object(PermissionEmbedding, "save", side_effect=AssertionError("write")), patch("apps.users.models.CustomUser.has_permission", side_effect=AssertionError("authorization")), patch("ai.service.execute_sql", side_effect=AssertionError("SQL execution")):
            self.assertEqual(len(search_permissions("question")), 1)
