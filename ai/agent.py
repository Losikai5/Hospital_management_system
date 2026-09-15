import json
from pathlib import Path
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from .service import execute_sql
load_dotenv()


DEFAULT_SCHEMA = (
    Path(__file__).resolve().parent.parent
    / "apps"
    / "core"
    / "schema.json"
)

DEFAULT_MODEL = "openai/gpt-oss-120b"


# -------------------------
# Load and format schema
# -------------------------

with open(DEFAULT_SCHEMA, encoding="utf-8") as f:
    schema_data = json.load(f)





def format_schema_for_llm(data: dict) -> str:
    lines = []

    for model, table in data.items():
        lines.append(
            f"TABLE: {table['db_table']} ({model})"
        )

        for col in table["columns"]:
            cname = col.get("name")

            if not cname:
                continue

            ctype = col.get("pg_type") or ""

            parts = [f"  {cname} ({ctype})"]

            if col.get("max_length"):
                parts.append(
                    f"max_length={col['max_length']}"
                )

            if col.get("references"):
                reference = col["references"]

                # references is a Django model name,
                # e.g. doctors.DoctorProfile
                parts.append(
                    f"REFERENCES {reference}"
                )

            if col.get("primary_key"):
                parts.append("PK")

            if col.get("choices"):
                choices = [
                    choice["value"]
                    for choice in col["choices"]
                ]

                parts.append(
                    f"allowed values={choices}"
                )

            lines.append(" ".join(parts))

        lines.append("")

    return "\n".join(lines)



SCHEMA_TEXT = format_schema_for_llm(schema_data)



llm = ChatGroq(
    model_name=DEFAULT_MODEL
)

SQL_PROMPT = ChatPromptTemplate.from_messages([
    (
        "system",
        """
You are a SQL generation assistant for a hospital management system.

Your job is to convert the user's question into a PostgreSQL SQL query.

Use ONLY the tables and columns provided in the database schema.

Do not invent tables, columns, or relationships.

Use the foreign-key relationships provided in the schema when joins are necessary.

Respect the allowed values provided for fields with choices.

Return ONLY the SQL query.

Do not use markdown code blocks.
Do not explain the query.

Database schema:

{schema}
"""
    ),
    (
        "human",
        "{question}"
    ),
])


ANSWER_PROMPT = ChatPromptTemplate.from_messages([
    (
        "system",
        """
You are an AI assistant for a hospital management system.

Your job is to answer the user's question using the database result provided.

Do not invent information.

Use only the information contained in the database result.

Answer the user clearly and naturally.

If the result is empty, explain that no matching records were found.

Database result:

{result}
"""
    ),
    (
        "human",
        "{question}"
    ),
])



CLASSIFIER_PROMPT = ChatPromptTemplate.from_messages([
    (
        "system",
        """
You are an intent classifier for a hospital management system AI assistant.

Classify the user's message into exactly one of these intents:

database
general

Use "database" when the user is asking for information that requires
reading data from the hospital database.

Examples:
- How many appointments are there?
- Show me today's appointments.
- How many doctors are registered?
- Which patients have appointments?
- What is the total amount paid?

Use "general" for normal conversation that does not require querying
the hospital database.

Examples:
- Hello
- How are you?
- Thank you
- What can you do?
- Tell me a joke

Return ONLY one word:

database

or

general
"""
    ),
    (
        "human",
        "{question}"
    ),
])



GENERAL_ANSWER_PROMPT = ChatPromptTemplate.from_messages([
    (
        "system",
        """
        You are a friendly AI assistant for a hospital management system.

        Answer the user's message naturally and helpfully.

        Do not query or invent database information.
        If the user asks for database information, that question should
        be handled by the database path instead.

        Keep responses concise.
        """
    ),
    ("human", "{question}"),
])


def generate_general_answer(question: str) -> str:
    prompt = GENERAL_ANSWER_PROMPT.invoke({
        "question": question,
    })

    response = llm.invoke(prompt)

    return response.content.strip()






def classify_question(question: str) -> str:
    prompt = CLASSIFIER_PROMPT.invoke({
        "question": question,
    })

    response = llm.invoke(prompt)

    return response.content.strip().lower()


def generate_answer(question: str, result: dict) -> str:
    prompt = ANSWER_PROMPT.invoke({
        "question": question,
        "result": result,
    })

    response = llm.invoke(prompt)

    return response.content.strip()



def generate_sql(question: str) -> str:
    prompt = SQL_PROMPT.invoke({
        "schema": SCHEMA_TEXT,
        "question": question,
    })

    response = llm.invoke(prompt)

    return response.content.strip()

def ask_database(question:str):
    sql = generate_sql(question)
    result = execute_sql(sql)
    answer = generate_answer(question,result)

    return answer
