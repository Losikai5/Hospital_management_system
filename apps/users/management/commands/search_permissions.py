from django.core.management.base import BaseCommand, CommandError

from ai.embeddings import EmbeddingError
from ai.permission_search import PermissionSearchError, search_permissions


class Command(BaseCommand):
    help = "Retrieve semantic permission candidates; this does not authorize any operation."

    def add_arguments(self, parser):
        parser.add_argument("question", help="Natural-language request.")
        parser.add_argument("--limit", type=int, default=5)
        parser.add_argument("--min-similarity", type=float, default=None)

    def handle(self, *args, **options):
        try:
            candidates = search_permissions(
                options["question"], limit=options["limit"],
                min_similarity=options["min_similarity"],
            )
        except (ValueError, EmbeddingError, PermissionSearchError) as error:
            raise CommandError(str(error)) from None
        self.stdout.write(f"Query: {options['question']}\n")
        self.stdout.write("Relevant permission candidates (not authorization decisions):\n")
        if not candidates:
            self.stdout.write("No suitable candidates found. Check active, current embeddings and the similarity cutoff.")
            return
        for rank, candidate in enumerate(candidates, start=1):
            self.stdout.write(
                f"{rank}. {candidate['permission_code']} — {candidate['permission_name']} "
                f"(similarity: {candidate['similarity']:.6f})\n"
                f"   {candidate['description']}"
            )
