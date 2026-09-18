from langgraph.graph import StateGraph, START, END

from ai.state import AgentState

from ai.nodes import (
    classify_question_node,
    generate_sql_node,
    execute_sql_node,
    generate_answer_node,
    generate_general_answer_node,
    generate_user_answer_node,
)


def route_intent(state: AgentState):
    return state["intent"]


graph_builder = StateGraph(AgentState)


graph_builder.add_node(
    "classify",
    classify_question_node,
)

graph_builder.add_node(
    "generate_sql",
    generate_sql_node,
)

graph_builder.add_node(
    "execute_sql",
    execute_sql_node,
)

graph_builder.add_node(
    "generate_answer",
    generate_answer_node,
)

graph_builder.add_node(
    "generate_general_answer",
    generate_general_answer_node,
)

graph_builder.add_node(
    "generate_user_answer",
    generate_user_answer_node,
)


graph_builder.add_edge(
    START,
    "classify",
)


graph_builder.add_conditional_edges(
    "classify",
    route_intent,
    {
        "user": "generate_user_answer",
        "general": "generate_general_answer",
        "database_read": "generate_sql",
        "database_write": "generate_sql",
    },
)


graph_builder.add_edge(
    "generate_sql",
    "execute_sql",
)

graph_builder.add_edge(
    "execute_sql",
    "generate_answer",
)

graph_builder.add_edge(
    "generate_answer",
    END,
)

graph_builder.add_edge(
    "generate_general_answer",
    END,
)

graph_builder.add_edge(
    "generate_user_answer",
    END,
)


graph = graph_builder.compile()


def ask_assistant(question: str, user):
    print("AI USER:", user)
    

    print(
        "AI USER ID:",
        user.id if user.is_authenticated else None,
    )

    result = graph.invoke({
        "question": question,
        "user": user,
    })

    return result