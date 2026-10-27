"""AI database access is disabled until approved operations enforce HMS policy."""

PROTECTED_OPERATION_UNAVAILABLE = (
    "Access to private user information and hospital records, including database "
    "changes, is temporarily unavailable in the AI assistant while permission "
    "enforcement is being implemented. I can still answer general-knowledge questions."
)


class AIDataAccessDisabled(PermissionError):
    """No permission-enforced AI database execution path is available yet."""


def execute_sql(sql: str):
    # Syntax validation is not authorization. Keep this guard at the lowest
    # execution boundary, including for direct callers and administrators.
    raise AIDataAccessDisabled(PROTECTED_OPERATION_UNAVAILABLE)
