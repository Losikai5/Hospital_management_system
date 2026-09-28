import sqlglot

ALLOWED_OPERATIONS = {
    "select",
    "insert",
    "update",
    "delete",
}


def validate_sql(sql):
    if not sql or not sql.strip():
        return {
            "valid": False,
            "operation": None,
            "error": "SQL query is empty.",
        }

    try:
        statements = sqlglot.parse(
            sql,
            dialect="postgres",
        )
    except sqlglot.errors.ParseError as exc:
        return {
            "valid": False,
            "operation": None,
            "error": f"Invalid SQL: {exc}",
        }

    if len(statements) != 1:
        return {
            "valid": False,
            "operation": None,
            "error": "Only one SQL statement is allowed.",
        }

    statement = statements[0]
    operation = statement.key

    if operation not in ALLOWED_OPERATIONS:
        return {
            "valid": False,
            "operation": operation,
            "error": f"SQL operation {operation.upper()} is not allowed.",
        }

    return {
        "valid": True,
        "operation": operation,
        "error": None,
    }
