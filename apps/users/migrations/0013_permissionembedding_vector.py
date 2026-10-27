"""Preserve existing JSON vectors while converting to pgvector storage."""
from django.db import migrations
from pgvector.django import VectorField


class Migration(migrations.Migration):
    dependencies = [("users", "0012_permissionembedding")]

    operations = [
        # pgvector may already serve unrelated tables. Never drop the shared
        # extension when rolling this field conversion back.
        migrations.RunSQL(
            "CREATE EXTENSION IF NOT EXISTS vector",
            reverse_sql=migrations.RunSQL.noop,
        ),
        migrations.SeparateDatabaseAndState(
            database_operations=[
                migrations.RunSQL(
                    sql=(
                        "ALTER TABLE users_permissionembedding "
                        "ALTER COLUMN embedding TYPE vector(768) "
                        "USING embedding::text::vector(768)"
                    ),
                    reverse_sql=(
                        "ALTER TABLE users_permissionembedding "
                        "ALTER COLUMN embedding TYPE jsonb "
                        "USING embedding::text::jsonb"
                    ),
                ),
            ],
            state_operations=[
                migrations.AlterField(
                    model_name="permissionembedding",
                    name="embedding",
                    field=VectorField(dimensions=768),
                ),
            ],
        ),
    ]
