"""Separate public/authenticated workflows with no protected data operations."""

from langgraph.graph import StateGraph, START, END

from ai.state import PublicAgentState
from ai.nodes import (
    classify_question_node,
    generate_general_answer_node,
    protected_operation_unavailable_node,
)


def route_intent(state):
    # Classification only chooses response wording. Even a malicious or wrong
    # "general" classification cannot reach a database or private-user node.
    return "general" if state.get("intent") == "general" else "unavailable"


def build_general_only_graph():
    builder = StateGraph(PublicAgentState)
    builder.add_node("classify", classify_question_node)
    builder.add_node("general", generate_general_answer_node)
    builder.add_node("unavailable", protected_operation_unavailable_node)
    builder.add_edge(START, "classify")
    builder.add_conditional_edges("classify", route_intent, {
        "general": "general",
        "unavailable": "unavailable",
    })
    builder.add_edge("general", END)
    builder.add_edge("unavailable", END)
    return builder.compile()


public_graph = build_general_only_graph()
authenticated_graph = build_general_only_graph()
# Preserve the old graph entry point, but it is now general-only too.
graph = authenticated_graph


def ask_assistant(question: str, user=None):
    if not isinstance(question, str) or not question.strip():
        raise ValueError("A non-empty question is required.")
    authenticated = bool(
        user is not None
        and getattr(user, "is_authenticated", False)
        and getattr(user, "is_active", False)
    )
    workflow = authenticated_graph if authenticated else public_graph
    # Never give either model path a user object, roles, grants or prior results.
    return workflow.invoke({"question": question.strip()})
