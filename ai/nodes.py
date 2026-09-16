from ai.agent import (
    classify_question,
    generate_sql,
    generate_answer,
    generate_general_answer,
    generate_user_answer,
)
from ai.service import execute_sql
from ai.state import AgentState


def generate_sql_node(state: AgentState):
    sql = generate_sql(
        state["question"],
        user=state.get("user"),
    )

    return {
        "sql": sql
    }


def execute_sql_node(state: AgentState):
    print("GENERATED SQL:", state["sql"])
    result = execute_sql(state["sql"])

    print("SQL RESULT:", result)

    return {
        "result": result
    }


def generate_answer_node(state: AgentState):
    answer = generate_answer(
        state["question"],
        state["result"]
    )

    return {
        "answer": answer
    }


def classify_question_node(state: AgentState):
    intent = classify_question(state["question"])

    return {
        "intent": intent
    }


def generate_general_answer_node(state: AgentState):
    answer = generate_general_answer(
        state["question"]
    )

    return {
        "answer": answer
    }


def generate_user_answer_node(state: AgentState):
    answer = generate_user_answer(
        state["question"],
        state.get("user"),
    )

    return {
        "answer": answer
    }