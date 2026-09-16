from django.db import connection


def execute_sql(sql: str):
    with connection.cursor() as cursor:
        cursor.execute(sql)

        if cursor.description:
            columns = [
                column[0]
                for column in cursor.description
            ]

            rows = cursor.fetchall()

            return {
                "columns": columns,
                "rows": rows,
                "rowcount": cursor.rowcount,
            }

        return {
            "columns": [],
            "rows": [],
            "rowcount": cursor.rowcount,
        }

