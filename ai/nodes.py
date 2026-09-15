from ai.agent import (
    classify_question,
    generate_sql,
    generate_answer,
    generate_general_answer,
)
from ai.service import execute_sql
from ai.state import AgentState


def generate_sql_node(state: AgentState):
    sql = generate_sql(state["question"])

    return {
        "sql": sql
    }


def execute_sql_node(state: AgentState):
    result = execute_sql(state["sql"])

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
