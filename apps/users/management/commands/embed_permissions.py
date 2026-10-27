from django.core.exceptions import ValidationError
from django.core.management.base import BaseCommand, CommandError
from django.db import DatabaseError, transaction

from ai.embeddings import (
    EmbeddingError,
    GeminiEmbeddingService,
    format_permission_text,
    validate_embedding,
)
from apps.users.models import Permission, PermissionEmbedding


class Command(BaseCommand):
    help = "Generate and store Gemini embeddings for existing permission records."

    def add_arguments(self, parser):
        parser.add_argument("--force", action="store_true", help="Regenerate unchanged embeddings.")
        parser.add_argument("--permission", help="Process only this permission code.")

    @staticmethod
    def is_current(existing, text, service):
        if existing is None or (
            existing.source_text != text
            or existing.model_name != service.model_name
            or existing.dimensions != service.dimensions
        ):
            return False
        try:
            validate_embedding(existing.embedding, service.dimensions)
        except EmbeddingError:
            return False
        return True

    def handle(self, *args, **options):
        permissions = Permission.objects.order_by("code")
        if options["permission"]:
            permissions = permissions.filter(code=options["permission"])
            if not permissions.exists():
                raise CommandError("Unknown permission code.")
        try:
            service = GeminiEmbeddingService()
        except EmbeddingError as error:
            raise CommandError(str(error)) from None

        self.stdout.write("Starting permission embedding...\n")
        counts = dict(Created=0, Updated=0, Skipped=0, Failed=0)
        permissions = list(permissions.select_related("embedding"))
        for index, permission in enumerate(permissions, start=1):
            text = format_permission_text(permission)
            existing = getattr(permission, "embedding", None)
            prefix = f"[{index}/{len(permissions)}]"
            if not options["force"] and self.is_current(existing, text, service):
                counts["Skipped"] += 1
                self.stdout.write(f"{prefix} Skipped: {permission.code}")
                continue
            try:
                # Never hold a database transaction open across the API call.
                vector = validate_embedding(service.embed_permission(text), service.dimensions)
                with transaction.atomic():
                    # Serialize concurrent embedding writers on the parent row.
                    current = Permission.objects.select_for_update().get(pk=permission.pk)
                    if format_permission_text(current) != text:
                        raise EmbeddingError("Permission changed during generation; rerun the command.")
                    record = PermissionEmbedding.objects.filter(permission=current).first()
                    created = record is None
                    if record is None:
                        record = PermissionEmbedding(permission=current)
                    record.embedding = vector
                    record.source_text = text
                    record.model_name = service.model_name
                    record.dimensions = service.dimensions
                    record.full_clean()
                    record.save()
                counts["Created" if created else "Updated"] += 1
                self.stdout.write(f"{prefix} Embedded: {permission.code}")
            except EmbeddingError as error:
                counts["Failed"] += 1
                self.stderr.write(f"{prefix} Failed: {permission.code}: {error}")
            except (DatabaseError, ValidationError, Permission.DoesNotExist):
                counts["Failed"] += 1
                self.stderr.write(f"{prefix} Failed: {permission.code}: Could not store embedding; existing data preserved.")

        self.stdout.write("\nCompleted.\n")
        for label, count in counts.items():
            self.stdout.write(f"{label}: {count}")
        if counts["Failed"]:
            raise CommandError("Some permissions failed. Resolve the reported errors and rerun the command.")
