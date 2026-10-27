from ai.agent import classify_question, generate_general_answer
from ai.service import PROTECTED_OPERATION_UNAVAILABLE
from ai.state import AgentState


def protected_operation_unavailable_node(state):
    return {"answer": PROTECTED_OPERATION_UNAVAILABLE}


# Retain legacy names for later approved-operation integration. Direct callers
# cannot generate SQL, read private user details, or summarize supplied records.
def generate_sql_node(state: AgentState):
    return protected_operation_unavailable_node(state)


def execute_sql_node(state: AgentState):
    return {
        **protected_operation_unavailable_node(state),
        "sql_validation": {"valid": False, "error": "AI data access is disabled."},
        "result": {"columns": [], "rows": [], "rowcount": 0},
    }


def route_after_sql(state: AgentState):
    return "invalid"


def sql_validation_error_node(state: AgentState):
    return protected_operation_unavailable_node(state)


def generate_answer_node(state: AgentState):
    return protected_operation_unavailable_node(state)


def classify_question_node(state):
    return {"intent": classify_question(state["question"])}


def generate_general_answer_node(state):
    return {"answer": generate_general_answer(state["question"])}


def generate_user_answer_node(state: AgentState):
    return protected_operation_unavailable_node(state)
