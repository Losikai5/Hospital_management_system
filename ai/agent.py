import json
from pathlib import Path
from dotenv import load_dotenv
from django.core.exceptions import ObjectDoesNotExist
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
load_dotenv()


DEFAULT_SCHEMA = (
    Path(__file__).resolve().parent.parent
    / "apps"
    / "core"
    / "schema.json"
)

DEFAULT_MODEL = "openai/gpt-oss-120b"



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
        (
            "You are the SQL generation component of a hospital management AI agent. "
            "Your job is to convert the user's request into a valid PostgreSQL SQL statement "
            "using only the database schema provided below.\n\n"

            "The request may require reading, creating, updating, or deleting hospital data.\n\n"

            "Rules:\n"
            "- Return ONLY the raw SQL statement.\n"
            "- Do NOT return markdown, backticks, explanations, comments, or prefixes.\n"
            "- Use valid PostgreSQL syntax.\n"
            "- Use ONLY tables and columns that exist in the provided schema.\n"
            "- NEVER invent tables, columns, relationships, or values.\n"
            "- Use the relationships defined in the schema when joining tables.\n"
            "- Foreign-key columns normally end with `_id`.\n"
            "- Respect foreign-key relationships when resolving related records.\n"
            "- Respect the allowed values defined for fields with choices.\n"
            "- Use ILIKE for case-insensitive text matching when appropriate.\n"
            "- Use the current user's information when the request contains references "
            "such as 'me', 'my', 'mine', 'I', or 'myself'.\n"
            "- The Current User section identifies the authenticated user making the request.\n"
            "- Do not assume that the user's role alone identifies their hospital profile. "
            "Use the actual relationships in the schema to determine whether the user is "
            "associated with a patient, doctor, or another entity.\n"
            "- If the request requires information related to the current user, follow the "
            "appropriate foreign-key relationships from the schema.\n"
            "- For INSERT statements, provide values for all required non-null fields unless "
            "the database supplies a default value.\n"
            "- For UPDATE statements, update only the fields relevant to the user's request.\n"
            "- For DELETE statements, target only the records described by the user's request.\n"
            "- Do not modify unrelated records.\n"
            "- For SELECT statements, return only columns relevant to answering the user's question.\n"
            "- Unless the user explicitly asks for more, limit large SELECT results to 20 rows.\n"
            "- Do not select sensitive authentication fields such as passwords or password hashes.\n"
            "- Do not use parameterized placeholders such as `%s`, `?`, `:user_id`, or `:id`. "
            "Generate a self-contained SQL statement using the information provided in the prompt.\n"
            "- When a value is a string, use valid PostgreSQL string quoting.\n"
            "- When a request is ambiguous, use the database relationships and available schema "
            "information to determine the most appropriate query rather than inventing information.\n\n"

            "Current User:\n"
            "{user_context}\n\n"

            "Database Schema:\n"
            "{schema}"
        )
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
You are deciding what the assistant needs to answer the user's request.

Return exactly ONE of:

user
general
database_read
database_write

user:
    The answer can be obtained from the authenticated user's information,
    role, or permissions.

general:
    The question does not require information from the hospital database
    or the authenticated user's information.

database_read:
    The request requires reading information from the hospital database.

database_write:
    The request requires creating, updating, or deleting information
    in the hospital database.

Examples:

"What is my email?" → user
"What is my role?" → user
"What permissions do I have?" → user

"What is diabetes?" → general

"How many appointments are there?" → database_read
"Show me all doctors." → database_read
"Show me my appointments." → database_read

"Book me an appointment." → database_write
"Cancel my appointment." → database_write
"Update my phone number." → database_write

Return ONLY one word.
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


USER_ANSWER_PROMPT = ChatPromptTemplate.from_messages([
    (
        "system",
        """
You are an AI assistant for a hospital management system.

Answer the user's question using only the authenticated user's information
provided below.

Do not invent information.

Authenticated User:
{user_context}

Answer naturally and concisely.
"""
    ),
    (
        "human",
        "{question}"
    ),
])


def generate_user_answer(question: str, user) -> str:
    prompt = USER_ANSWER_PROMPT.invoke({
        "question": question,
        "user_context": format_user_context(user),
    })

    response = llm.invoke(prompt)

    return response.content.strip()


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



def format_user_context(user) -> str:
    if user is None or not user.is_authenticated:
        return "Anonymous (no authenticated user)"

    lines = [
        f"user_id: {user.pk}",
        f"email: {user.email}",
        f"role: {user.role_code}",
    ]

    try:
        patient = user.patient_profile
        lines.append(f"patient_profile_id: {patient.pk}")
    except ObjectDoesNotExist:
        pass

    try:
        doctor = user.doctor_profile
        lines.append(f"doctor_profile_id: {doctor.pk}")
    except ObjectDoesNotExist:
        pass

    return "\n".join(lines)


def generate_sql(question: str, user=None) -> str:
    prompt = SQL_PROMPT.invoke({
        "schema": SCHEMA_TEXT,
        "question": question,
        "user_context": format_user_context(user),
    })

    response = llm.invoke(prompt)

    return response.content.strip()
