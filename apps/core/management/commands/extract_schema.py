"""
Management command: extract_schema

Extracts the full database schema with rich field descriptions, relationship
details, constraints, indexes, and Go type mappings. The output is designed
to be fed to an AI model so it can generate correct Go / SQL code.
"""

from collections import OrderedDict

from django.apps import apps
from django.core.management.base import BaseCommand
from django.db import connection
from django.db.models import (
    AutoField,
    BigAutoField,
    BigIntegerField,
    BooleanField,
    CharField,
    DateField,
    DateTimeField,
    DecimalField,
    EmailField,
    FileField,
    FloatField,
    ForeignKey,
    GenericIPAddressField,
    ImageField,
    IntegerField,
    JSONField,
    ManyToManyField,
    OneToOneField,
    PositiveIntegerField,
    PositiveSmallIntegerField,
    SmallIntegerField,
    TextField,
    TimeField,
)

# ---------------------------------------------------------------------------
# Django field type  →  (PostgreSQL type, Go type)
# ---------------------------------------------------------------------------
DJANGO_TO_SQL_AND_GO = {
    "AutoField":          ("bigserial",    "int64"),
    "BigAutoField":       ("bigserial",    "int64"),
    "SmallAutoField":     ("serial",       "int32"),
    "IntegerField":       ("integer",      "int32"),
    "SmallIntegerField":  ("smallint",     "int16"),
    "BigIntegerField":    ("bigint",       "int64"),
    "PositiveIntegerField":      ("integer",      "uint32"),
    "PositiveSmallIntegerField": ("smallint",     "uint16"),
    "PositiveBigIntegerField":   ("bigint",       "uint64"),
    "FloatField":         ("double precision", "float64"),
    "DecimalField":       ("numeric",     "float64"),
    "CharField":          ("varchar",     "string"),
    "SlugField":          ("varchar",     "string"),
    "EmailField":         ("varchar",     "string"),
    "URLField":           ("varchar",     "string"),
    "UUIDField":          ("uuid",        "string"),
    "TextField":          ("text",        "string"),
    "BooleanField":       ("boolean",     "bool"),
    "NullBooleanField":   ("boolean",     "*bool"),
    "DateField":          ("date",        "time.Time"),
    "DateTimeField":      ("timestamptz", "time.Time"),
    "TimeField":          ("time",        "time.Time"),
    "JSONField":          ("jsonb",       "json.RawMessage"),
    "BinaryField":        ("bytea",       "[]byte"),
    "FileField":          ("varchar",     "string"),
    "ImageField":         ("varchar",     "string"),
    "IPAddressField":     ("inet",        "string"),
    "GenericIPAddressField": ("inet",     "string"),
    "ForeignKey":         ("bigint",      "int64"),
    "OneToOneField":      ("bigint",      "int64"),
}

GO_NULLABLE_POINTER = {
    "string":   "*string",
    "int16":    "*int16",
    "int32":    "*int32",
    "int64":    "*int64",
    "uint16":   "*uint16",
    "uint32":   "*uint32",
    "uint64":   "*uint64",
    "float64":  "*float64",
    "bool":     "*bool",
    "time.Time": "*time.Time",
}


def _pg_type(field):
    """Return the PostgreSQL column type string for a Django field."""
    if isinstance(field, ManyToManyField):
        return None  # M2M doesn't live on this table

    if isinstance(field, (ForeignKey, OneToOneField)):
        return "bigint"

    lookup = type(field).__name__
    entry = DJANGO_TO_SQL_AND_GO.get(lookup)
    if entry:
        return entry[0]

    # Fallback for unknown field types
    return "text"


def _go_type(field):
    """Return the Go type string for a Django field."""
    if isinstance(field, ManyToManyField):
        return None

    if isinstance(field, (ForeignKey, OneToOneField)):
        base = "int64"
    else:
        lookup = type(field).__name__
        entry = DJANGO_TO_SQL_AND_GO.get(lookup)
        base = entry[1] if entry else "string"

    # Wrap in pointer if nullable
    nullable = getattr(field, "null", False)
    if nullable:
        return GO_NULLABLE_POINTER.get(base, f"*{base}")
    return base


def _decimal_args(field):
    """Return (max_digits, decimal_places) for DecimalField, else None."""
    if isinstance(field, DecimalField):
        return field.max_digits, field.decimal_places
    return None


# ---------------------------------------------------------------------------
# Command
# ---------------------------------------------------------------------------
class Command(BaseCommand):
    help = (
        "Extract the full database schema with field descriptions, "
        "relationships, constraints, indexes, and Go type mappings."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--model",
            action="append",
            dest="models",
            help="Filter to specific app_label.ModelName (repeatable).",
        )
        parser.add_argument(
            "--format",
            choices=["text", "json"],
            default="json",
            dest="output_format",
            help="Output format (default: json).",
        )
        parser.add_argument(
            "--output",
            "-o",
            help="Save to a custom file path instead of the default core location.",
        )
        parser.add_argument(
            "--stdout",
            action="store_true",
            help="Print to the terminal instead of saving to a file.",
        )

    # ------------------------------------------------------------------
    def handle(self, *args, **options):
        import json
        from pathlib import Path

        fmt = options["output_format"]
        model_filters = options["models"]
        out = options["output"]
        to_stdout = options["stdout"]

        tables = self._collect_tables(model_filters)

        if fmt == "json":
            result = json.dumps(tables, indent=2, default=str)
        else:
            result = self._render_text(tables)

        if to_stdout:
            self.stdout.write(result)
            return

        # Default location: the core app directory
        if out:
            dest = Path(out)
        else:
            core_dir = Path(__file__).resolve().parent.parent.parent
            filename = "schema.json" if fmt == "json" else "schema.txt"
            dest = core_dir / filename

        dest.parent.mkdir(parents=True, exist_ok=True)
        with open(dest, "w") as f:
            f.write(result)
        self.stdout.write(self.style.SUCCESS(f"Schema saved to {dest}"))

    # ------------------------------------------------------------------
    # Data collection
    # ------------------------------------------------------------------
    @staticmethod
    def _validator_text(validator):
        """Render a validator as a short human-readable string."""
        from django.core.validators import (
            DecimalValidator,
            EmailValidator,
            MaxLengthValidator,
            MaxValueValidator,
            MinLengthValidator,
            MinValueValidator,
            RegexValidator,
        )

        if isinstance(validator, MinValueValidator):
            return f"min value: {validator.limit_value}"
        if isinstance(validator, MaxValueValidator):
            return f"max value: {validator.limit_value}"
        if isinstance(validator, MinLengthValidator):
            return f"min length: {validator.limit_value}"
        if isinstance(validator, MaxLengthValidator):
            return f"max length: {validator.limit_value}"
        if isinstance(validator, EmailValidator):
            return "email format"
        if isinstance(validator, RegexValidator):
            return f"regex: {validator.regex.pattern}"
        if isinstance(validator, DecimalValidator):
            return (
                f"decimal(max_digits={validator.max_digits}, "
                f"decimal_places={validator.decimal_places})"
            )
        return type(validator).__name__

    def _collect_tables(self, model_filters):
        """Build an OrderedDict of table metadata."""
        tables = OrderedDict()

        # Gather project-local models only (skip Django/third-party tables)
        all_models = sorted(apps.get_models(), key=lambda m: m._meta.label)
        all_models = [
            m for m in all_models
            if m._meta.app_config is not None
            and m._meta.app_config.module.__name__.startswith("apps.")
        ]

        for model in all_models:
            label = model._meta.label
            if model_filters and label not in model_filters:
                continue

            db_table = model._meta.db_table
            verbose = str(model._meta.verbose_name_plural or model._meta.verbose_name or "")
            abstract = model._meta.abstract
            managed = model._meta.managed

            if abstract or not managed:
                continue

            columns = self._get_columns(model)
            constraints = self._get_constraints(db_table)
            indexes = self._get_indexes(db_table)
            m2m_fields = self._get_m2m_fields(model)
            fks = self._get_foreign_keys(model)
            unique_together = [list(u) for u in model._meta.unique_together]
            ordering = list(model._meta.ordering) if model._meta.ordering else []

            tables[label] = {
                "db_table": db_table,
                "verbose_name": verbose,
                "columns": columns,
                "primary_key": [f.name for f in model._meta.local_fields if f.primary_key],
                "foreign_keys": fks,
                "m2m_fields": m2m_fields,
                "constraints": constraints,
                "indexes": indexes,
                "unique_together": unique_together,
                "ordering": ordering,
            }

        return tables

    def _get_columns(self, model):
        """Return a list of column dicts for the model's local fields."""
        columns = []
        for field in model._meta.local_fields:
            if isinstance(field, ManyToManyField):
                continue

            col = {
                "name": field.column,
                "field_name": field.name,
                "field_type": type(field).__name__,
                "pg_type": _pg_type(field),
                "go_type": _go_type(field),
                "primary_key": field.primary_key,
                "unique": field.unique,
                "nullable": getattr(field, "null", False),
                "has_default": field.has_default(),
            }

            # Default value
            if field.has_default():
                default = field.default
                if callable(default):
                    col["default"] = "<callable>"
                else:
                    col["default"] = default

            # Max length
            max_length = getattr(field, "max_length", None)
            if max_length:
                col["max_length"] = max_length
                if col["pg_type"] == "varchar":
                    col["pg_type"] = f"varchar({max_length})"

            # Decimal args
            dec = _decimal_args(field)
            if dec:
                col["max_digits"] = dec[0]
                col["decimal_places"] = dec[1]
                col["pg_type"] = f"numeric({dec[0]},{dec[1]})"

            # Choices
            choices = getattr(field, "choices", None)
            if choices:
                col["choices"] = [
                    {"value": c[0], "label": str(c[1])} for c in choices
                ]

            # Validators
            validators = getattr(field, "validators", [])
            if validators:
                col["validators"] = [self._validator_text(v) for v in validators]

            # Verbose name / help text
            verbose_name = getattr(field, "verbose_name", None)
            if verbose_name:
                col["verbose_name"] = str(verbose_name)

            help_text = getattr(field, "help_text", None)
            if help_text:
                col["help_text"] = str(help_text)

            # Upload path for File/Image fields
            upload_to = getattr(field, "upload_to", None)
            if upload_to:
                col["upload_to"] = upload_to

            # FK / OneToOne info
            if isinstance(field, (ForeignKey, OneToOneField)):
                col["references"] = field.related_model._meta.label
                col["on_delete"] = field.remote_field.on_delete.__name__
                col["related_name"] = field.remote_field.related_name

            # DB index
            if field.db_index and not field.unique:
                col["db_index"] = True

            columns.append(col)

        return columns

    def _get_m2m_fields(self, model):
        """Return info about ManyToMany fields."""
        result = []
        for field in model._meta.many_to_many:
            info = {
                "name": field.name,
                "field_type": "ManyToManyField",
                "through": field.remote_field.through._meta.label if hasattr(field.remote_field, "through") else None,
                "related_model": field.related_model._meta.label,
                "related_name": field.remote_field.related_name,
            }
            verbose_name = getattr(field, "verbose_name", None)
            if verbose_name:
                info["verbose_name"] = str(verbose_name)
            result.append(info)
        return result

    def _get_foreign_keys(self, model):
        """Return a concise list of FK relationships."""
        result = []
        for field in model._meta.local_fields:
            if isinstance(field, OneToOneField):
                result.append({
                    "column": field.column,
                    "references": field.related_model._meta.label,
                    "db_table": field.related_model._meta.db_table,
                    "on_delete": field.remote_field.on_delete.__name__,
                    "related_name": field.remote_field.related_name,
                    "type": "OneToOne",
                })
            elif isinstance(field, ForeignKey):
                result.append({
                    "column": field.column,
                    "references": field.related_model._meta.label,
                    "db_table": field.related_model._meta.db_table,
                    "on_delete": field.remote_field.on_delete.__name__,
                    "related_name": field.remote_field.related_name,
                })
        return result

    def _get_constraints(self, db_table):
        """Extract constraints from the database."""
        constraints = []
        with connection.cursor() as cursor:
            try:
                if hasattr(cursor, "constraints"):
                    raw = cursor.constraints(db_table)
                else:
                    raw = connection.introspection.get_constraints(cursor, db_table)
                for name, info in raw.items():
                    if info.get("unique") and not info.get("primary_key"):
                        constraints.append({
                            "name": name,
                            "type": "UNIQUE",
                            "columns": info["columns"],
                        })
                    if info.get("check"):
                        constraints.append({
                            "name": name,
                            "type": "CHECK",
                            "columns": info["columns"],
                        })
            except Exception:
                pass
        return constraints

    def _get_indexes(self, db_table):
        """Extract indexes from the database."""
        indexes = []
        with connection.cursor() as cursor:
            try:
                if hasattr(cursor, "constraints"):
                    raw = cursor.constraints(db_table)
                else:
                    raw = connection.introspection.get_constraints(cursor, db_table)
                for name, info in raw.items():
                    if info.get("index") and not info.get("primary_key") and not info.get("unique"):
                        indexes.append({
                            "name": name,
                            "columns": info["columns"],
                            "type": info.get("type", "btree"),
                        })
            except Exception:
                pass
        return indexes

    # ------------------------------------------------------------------
    # Text rendering
    # ------------------------------------------------------------------
    def _render_text(self, tables):
        lines = []
        sep = "=" * 80

        # Header
        lines.append(sep)
        lines.append("DATABASE SCHEMA REFERENCE")
        lines.append(f"Engine: PostgreSQL  |  Tables: {len(tables)}")
        lines.append(sep)
        lines.append("")
        lines.append(
            "This document describes every table, column, relationship, "
            "constraint, and index in the hospital management database. "
            "Each column includes the PostgreSQL type and the recommended "
            "Go type for use in Go structs and SQL queries."
        )
        lines.append("")
        lines.append("GO TYPE LEGEND:")
        lines.append("  int64 / *int64      – 64-bit signed integer (* = nullable)")
        lines.append("  uint32 / *uint32    – 32-bit unsigned integer")
        lines.append("  string / *string    – variable-length text")
        lines.append("  bool / *bool        – boolean")
        lines.append("  float64 / *float64  – 64-bit float (use for decimals)")
        lines.append("  time.Time / *time.Time – date/timestamp")
        lines.append("  json.RawMessage     – JSONB column")
        lines.append("  []byte              – binary data")
        lines.append("")
        lines.append(sep)

        for label, info in tables.items():
            lines.append("")
            lines.append(f"TABLE: {info['db_table']}")
            lines.append(f"Model: {label}")
            if info["verbose_name"]:
                lines.append(f"Description: {info['verbose_name']}")
            lines.append(f"Columns: {len(info['columns'])}")
            if info["ordering"]:
                lines.append(f"Default ordering: {info['ordering']}")
            lines.append("-" * 80)

            # Column table
            lines.append("")
            lines.append(
                f"  {'Column':<30} {'Pg Type':<25} {'Go Type':<20} {'Constraints'}"
            )
            lines.append(f"  {'-'*30} {'-'*25} {'-'*20} {'-'*30}")

            for col in info["columns"]:
                constraints = []
                if col["primary_key"]:
                    constraints.append("PK")
                if col["unique"]:
                    constraints.append("UNIQUE")
                if not col["nullable"]:
                    constraints.append("NOT NULL")
                if not col["has_default"] and not col["nullable"] and not col["primary_key"]:
                    constraints.append("REQUIRED")
                if col.get("db_index"):
                    constraints.append("INDEX")

                constraint_str = ", ".join(constraints)

                lines.append(
                    f"  {col['field_name']:<30} {col['pg_type']:<25} {col['go_type']:<20} {constraint_str}"
                )

            # Detailed column descriptions
            lines.append("")
            lines.append("  DETAILED COLUMN DESCRIPTIONS:")
            lines.append("")

            for col in info["columns"]:
                parts = [f"  {col['field_name']} ({col['field_type']})"]

                if col.get("verbose_name"):
                    parts.append(f'    Label: "{col["verbose_name"]}"')
                if col.get("help_text"):
                    parts.append(f'    Help: "{col["help_text"]}"')
                if col.get("default") is not None:
                    parts.append(f"    Default: {col['default']}")
                if col.get("max_length"):
                    parts.append(f"    Max length: {col['max_length']}")
                if col.get("max_digits"):
                    parts.append(
                        f"    Precision: {col['max_digits']} digits, {col['decimal_places']} decimal places"
                    )
                if col.get("choices"):
                    parts.append("    Choices:")
                    for ch in col["choices"]:
                        parts.append(f'      - "{ch["value"]}" → "{ch["label"]}"')
                if col.get("validators"):
                    parts.append(f"    Validators: {', '.join(col['validators'])}")
                if col.get("upload_to"):
                    parts.append(f'    Upload path: "{col["upload_to"]}"')
                if col.get("references"):
                    ref_type = col.get("field_type", "")
                    parts.append(
                        f'    FK → {col["references"]}  (on_delete={col["on_delete"]}, related_name="{col.get("related_name", "")}")'
                    )

                lines.append("\n".join(parts))
                lines.append("")

            # M2M fields
            if info["m2m_fields"]:
                lines.append("  MANY-TO-MANY FIELDS:")
                for m2m in info["m2m_fields"]:
                    through = m2m.get("through") or "auto-generated"
                    lines.append(
                        f'    {m2m["name"]} → {m2m["related_model"]}  '
                        f'(through={through}, related_name="{m2m["related_name"]}")'
                    )
                lines.append("")

            # Constraints
            if info["constraints"]:
                lines.append("  CONSTRAINTS:")
                for c in info["constraints"]:
                    cols = ", ".join(c["columns"])
                    lines.append(f'    {c["name"]}  ({c["type"]})  columns=[{cols}]')
                lines.append("")

            # Indexes
            if info["indexes"]:
                lines.append("  INDEXES:")
                for ix in info["indexes"]:
                    cols = ", ".join(ix["columns"])
                    lines.append(
                        f'    {ix["name"]}  columns=[{cols}]  type={ix["type"]}'
                    )
                lines.append("")

            # Unique together
            if info["unique_together"]:
                lines.append("  UNIQUE TOGETHER:")
                for ut in info["unique_together"]:
                    lines.append(f"    columns={ut}")
                lines.append("")

            lines.append(sep)

        # ---- Relationship summary ----
        lines.append("")
        lines.append("RELATIONSHIP SUMMARY")
        lines.append("-" * 80)
        for label, info in tables.items():
            for fk in info["foreign_keys"]:
                rel_type = fk.get("type", "ForeignKey")
                lines.append(
                    f'  {info["db_table"]}.{fk["column"]}  →  '
                    f'{fk["db_table"]}  ({rel_type}, on_delete={fk["on_delete"]})'
                )
            for m2m in info["m2m_fields"]:
                through = m2m.get("through") or "auto"
                lines.append(
                    f'  {info["db_table"]}.{m2m["name"]}  →  '
                    f'{m2m["related_model"]}  (ManyToMany, through={through})'
                )
        lines.append("")

        # ---- M2M join tables ----
        m2m_tables = []
        for label, info in tables.items():
            for m2m in info["m2m_fields"]:
                if m2m.get("through"):
                    m2m_tables.append(m2m["through"])

        if m2m_tables:
            lines.append("M2M JOIN TABLES (auto-managed by Django):")
            for t in sorted(set(m2m_tables)):
                lines.append(f"  - {t}")
            lines.append("")

        lines.append(sep)
        lines.append("END OF SCHEMA")
        lines.append(sep)

        return "\n".join(lines)
