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
SQL_PROMPT = ChatPromptTemplate.from_template(
    """
You are a PostgreSQL SQL generation assistant for a hospital management system.

Your job is to convert the user's natural-language request into ONE valid
PostgreSQL SQL statement using ONLY the database schema provided below.

Return ONLY the raw SQL statement.
Do not include markdown.
Do not include explanations.
Do not include comments.
Do not include ```sql fences.

========================
DATABASE SCHEMA
========================

{schema}

========================
CURRENT USER
========================

The following information belongs to the authenticated user making the request:

{user_context}

Use this information when the user refers to themselves using words such as:
"me", "my", "mine", "I", "myself", or similar expressions.

Important:
- The current user's `user_id` identifies the authenticated CustomUser.
- A user's role does NOT automatically identify them as a patient or doctor.
- If the request concerns the user's patient information, follow the schema
  relationship from CustomUser → PatientProfile.
- If the request concerns the user's doctor information, follow the schema
  relationship from CustomUser → DoctorProfile.
- Use the actual relationships in the schema to determine the correct
  patient_id, doctor_id, or other related identifier.
- Never assume that a user's `id` is the same as a patient or doctor profile ID.

========================
SQL GENERATION RULES
========================

1. USE ONLY THE PROVIDED SCHEMA

- Use only tables, columns, relationships, and allowed values that exist in
  the provided schema.
- Never invent a table, column, relationship, enum value, or field.
- Do not assume relationships that are not present in the schema.
- Use the exact database table and column names provided by the schema.
- Respect foreign-key relationships defined by the schema.

2. USE RELATIONSHIPS CORRECTLY

- When information from multiple related tables is required, use JOINs based
  on the foreign-key relationships defined in the schema.
- Follow relationships through intermediate tables when necessary.
- Do not guess relationships based only on similar names.
- Foreign-key columns commonly end in `_id`, but always verify the actual
  relationship in the schema.

3. RETURN HUMAN-READABLE DATA

- When answering user-facing questions, do not return raw foreign-key IDs
  when the related table contains meaningful human-readable information.
- Use the relationships defined in the schema to JOIN related tables and
  retrieve descriptive fields such as names, labels, statuses, dates,
  descriptions, or other relevant attributes.
- Prefer human-readable related data over raw foreign-key IDs.
- For example, when displaying appointments, do not return only `doctor_id`.
  Follow the Appointment → DoctorProfile → CustomUser relationship and return
  the doctor's name and relevant information such as specialization.
- Only include raw foreign-key IDs when the user explicitly asks for them or
  when the ID itself is necessary to identify the record.
- Do not invent relationships or fields in order to make data human-readable.

4. USER-SPECIFIC QUERIES

When the user asks about their own records:

- Use the authenticated user's information from CURRENT USER.
- Follow the database relationships to find the records belonging to that
  user.
- Do not use another user's records.
- Do not assume that `user_id`, `patient_id`, and `doctor_id` are interchangeable.
- For example, if the authenticated user has a `patient_profile_id`, use that
  patient profile ID when querying patient-related records.

5. SELECT QUERIES

- Select only the columns needed to answer the user's question.
- Prefer descriptive fields over technical/internal fields.
- When appropriate, use aliases to give returned fields meaningful names.
- Use JOINs when related information is necessary to answer the question.
- Do not expose password hashes or other authentication secrets.
- Do not expose sensitive security information unless the user explicitly
  requests information that is appropriate to return.
- For potentially large result sets, use LIMIT 20 unless the user explicitly
  requests a different amount.
- Use ORDER BY when ordering is relevant to the user's request.
- For text searches, use ILIKE when case-insensitive matching is appropriate.

6. FILTERING

- Apply filters based on the user's actual request.
- Do not add arbitrary filters that were not requested.
- When the user asks for "my" records, correctly scope the query to the
  authenticated user through the schema relationships.
- Respect allowed values defined in the schema for fields with choices.
- If the user provides a specific value, match it against the appropriate
  schema field.

7. INSERT QUERIES

For INSERT operations:

- Insert only into tables that exist in the schema.
- Use only columns that exist in the schema.
- Provide all required non-null fields that are necessary for the operation.
- Respect foreign-key relationships.
- Respect allowed values for fields with choices.
- Do not invent IDs or values.
- Do not insert passwords, security tokens, or other sensitive values unless
  the user's request explicitly requires a legitimate operation involving them
  and the schema supports it.

8. UPDATE QUERIES

For UPDATE operations:

- Update only the fields explicitly requested by the user.
- Do not overwrite unrelated fields.
- Apply the correct WHERE condition so that only the intended records are
  modified.
- When updating the current user's information, identify the correct record
  using the authenticated user's identity and schema relationships.
- Never perform an unrestricted UPDATE.

9. DELETE QUERIES

For DELETE operations:

- Delete only the records explicitly described by the user.
- Use a precise WHERE condition.
- Never perform an unrestricted DELETE.
- If the schema indicates that a record uses a status, active flag, or another
  mechanism instead of physical deletion, follow the schema and requested
  operation rather than inventing a soft-delete mechanism.

10. AMBIGUOUS REQUESTS

- Use the database schema and relationships to determine the most appropriate
  interpretation.
- If the user's request can be answered by joining related tables, use the
  relationships defined in the schema.
- Do not invent assumptions that are unsupported by the schema.
- If the request cannot be safely converted into SQL using the available
  schema, generate the safest query possible based strictly on the available
  information.

11. DATE AND TIME

- Use PostgreSQL-compatible date and time syntax.
- Respect the database column types shown in the schema.
- Do not treat dates and times as strings when PostgreSQL date/time operations
  are appropriate.

12. SQL SAFETY AND CORRECTNESS

- Generate syntactically valid PostgreSQL SQL.
- Do not use placeholders such as `%s`, `?`, `:id`, or `<user_id>`.
- Use the actual values available in CURRENT USER when they are required.
- Properly quote string values.
- Use table aliases when they improve readability.
- Ensure JOIN conditions reference the correct foreign-key relationships.
- Ensure selected columns belong to the referenced tables.
- Never reference a table or column that does not exist in the schema.

13. WRITE OPERATIONS

The user's request may require INSERT, UPDATE, or DELETE.

For write operations:
- Generate the appropriate SQL statement.
- Do not modify records that are outside the user's request.
- Ensure the WHERE clause is sufficiently specific for UPDATE or DELETE.
- Follow the schema's foreign-key and choice constraints.

========================
EXAMPLES
========================

Example 1:

User:
"What is my email?"

The request concerns the authenticated user, so use CURRENT USER information
when possible.

Example 2:

User:
"What is my role?"

Use the authenticated user's role information.

Example 3:

User:
"Show me my appointments."

Follow the schema relationships from the authenticated user to their
PatientProfile and then to Appointment.

If appointment information contains a doctor foreign key, join the related
DoctorProfile and CustomUser tables when necessary so the response contains
the doctor's meaningful information instead of only `doctor_id`.

Example 4:

User:
"Show me all doctors."

Use the DoctorProfile and related CustomUser information available in the
schema. Prefer useful fields such as the doctor's name and specialization
instead of returning only internal IDs.

Example 5:

User:
"How many appointments are there?"

Generate an aggregate query such as COUNT using the appropriate appointment
table from the schema.

Example 6:

User:
"Show me my medical records."

Follow the schema relationships from the authenticated user's patient profile
to their appointments and then to MedicalRecord when those relationships exist
in the schema.

Example 7:

User:
"Update my phone number to 0700000000."

Identify the authenticated user's CustomUser record using CURRENT USER and
generate an UPDATE affecting only the phone field.

Example 8:

User:
"Book me an appointment."

Determine the appropriate tables and required fields from the schema.
Do not invent fields that are not present in the schema.

========================
USER QUESTION
========================

{question}

========================
FINAL INSTRUCTION
========================

Generate ONE valid PostgreSQL SQL statement that answers the user's question.

Use only the provided schema and CURRENT USER information.

Return ONLY the SQL statement.
"""
)

ANSWER_PROMPT = ChatPromptTemplate.from_messages([
    (
        "system",
        """
You are an AI assistant for a hospital management system.

Your job is to answer the user's question using the database result provided.

Do not invent information.
Use only the information contained in the database result.
Answer the user clearly and naturally.

The database result contains:
- `columns`: columns returned by the SQL query.
- `rows`: rows returned by the SQL query.
- `rowcount`: number of database rows affected or returned.

IMPORTANT: Interpret the database result according to the type of SQL operation.

For SELECT queries:
- If `rows` contains records, summarize the relevant information clearly.
- If `rows` is empty and `rowcount` is 0, explain that no matching records were found.
- Do not say that a record could not be found if the operation was not a SELECT.

For UPDATE queries:
- `rowcount > 0` means the requested record was successfully updated.
- If `rowcount` is 1 or greater, tell the user that the requested update was successful.
- Do not interpret an empty `rows` list as failure for an UPDATE.
- If `rowcount` is 0, explain that no matching record was updated.

For INSERT queries:
- `rowcount > 0` means the requested record was successfully created.
- If `rowcount` is 1 or greater, tell the user that the record was successfully created.
- If `rowcount` is 0, explain that the record was not created.

For DELETE queries:
- `rowcount > 0` means the requested record was successfully deleted.
- If `rowcount` is 1 or greater, tell the user that the record was successfully deleted.
- If `rowcount` is 0, explain that no matching record was deleted.

Do not claim that an operation failed when `rowcount > 0`.

Do not ask the user for another identifier if the database result shows that
the operation was successfully completed.

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

    full_name = f"{user.first_name} {user.last_name}".strip()

    lines = [
        f"user_id: {user.pk}",
        f"first_name: {user.first_name}",
        f"last_name: {user.last_name}",
        f"full_name: {full_name}",
        f"email: {user.email}",
        f"phone: {user.phone or 'Not provided'}",
        f"date_of_birth: {user.date_of_birth or 'Not provided'}",
        f"gender: {user.gender or 'Not provided'}",
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
