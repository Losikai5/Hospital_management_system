from typing import TypedDict

class AgentState(TypedDict):
    question: str
    user: object
    sql: str
    sql_validation: dict
    result: dict
    answer: str
    intent: str