from ai.agent import (
    classify_question,
    generate_sql,
    generate_answer,
    generate_general_answer,
    generate_user_answer,
)
from ai.service import execute_sql
from ai.state import AgentState
from .sql_validator import validate_sql



def generate_sql_node(state: AgentState):
  

    sql = generate_sql(
        state["question"],
        user=state.get("user"),
    )


    
    print("GENERATED SQL:", sql)

    return {
        "sql": sql
    }


def execute_sql_node(state: AgentState):
    sql = state["sql"]
    print("GENERATED SQL:", sql)
    validation = validate_sql(sql)
    if not validation["valid"]:
        return {
            "sql_validation":validation,
            "result":{
                "columns":[],
                "rows":[],
                "rowcount":0
            },
        }
    result = execute_sql(state["sql"])

    print("SQL RESULT:", result)

    return {
        "sql_validation":validation,
        "result": result
    }

def route_after_sql(state: AgentState):
    if state["sql_validation"]["valid"]:
        return "valid"

    return "invalid"


def sql_validation_error_node(state: AgentState):
    return {
        "answer": (
            "I couldn't complete that request because "
            "the database operation generated for it isn't allowed."
        )
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