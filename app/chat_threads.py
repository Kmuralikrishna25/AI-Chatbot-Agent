import os

import psycopg
from dotenv import load_dotenv


# ============================================================
# ENVIRONMENT
# ============================================================

load_dotenv(override=True)

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise ValueError(
        "DATABASE_URL is not set. "
        "Please check your .env file."
    )


# ============================================================
# CREATE CHAT THREADS TABLE
# ============================================================

def initialize_chat_threads():

    with psycopg.connect(
        DATABASE_URL
    ) as connection:

        with connection.cursor() as cursor:

            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS chat_threads (
                    thread_id TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
                """
            )

        connection.commit()


# ============================================================
# CREATE NEW THREAD
# ============================================================

def create_thread(
    thread_id: str,
    title: str = "New Conversation"
):

    with psycopg.connect(
        DATABASE_URL
    ) as connection:

        with connection.cursor() as cursor:

            cursor.execute(
                """
                INSERT INTO chat_threads
                    (thread_id, title)
                VALUES
                    (%s, %s)
                ON CONFLICT (thread_id)
                DO NOTHING;
                """,
                (
                    thread_id,
                    title
                )
            )

        connection.commit()


# ============================================================
# GET ALL THREADS
# ============================================================

def get_threads():

    with psycopg.connect(
        DATABASE_URL
    ) as connection:

        with connection.cursor() as cursor:

            cursor.execute(
                """
                SELECT
                    thread_id,
                    title,
                    created_at,
                    updated_at
                FROM chat_threads
                ORDER BY updated_at DESC;
                """
            )

            rows = cursor.fetchall()

    return [
        {
            "thread_id": row[0],
            "title": row[1],
            "created_at": row[2],
            "updated_at": row[3],
        }
        for row in rows
    ]


# ============================================================
# UPDATE THREAD TITLE
# ============================================================

def update_thread_title(
    thread_id: str,
    title: str
):

    with psycopg.connect(
        DATABASE_URL
    ) as connection:

        with connection.cursor() as cursor:

            cursor.execute(
                """
                UPDATE chat_threads
                SET
                    title = %s,
                    updated_at = CURRENT_TIMESTAMP
                WHERE thread_id = %s;
                """,
                (
                    title,
                    thread_id
                )
            )

        connection.commit()


# ============================================================
# UPDATE THREAD TIMESTAMP
# ============================================================

def touch_thread(
    thread_id: str
):

    with psycopg.connect(
        DATABASE_URL
    ) as connection:

        with connection.cursor() as cursor:

            cursor.execute(
                """
                UPDATE chat_threads
                SET updated_at = CURRENT_TIMESTAMP
                WHERE thread_id = %s;
                """,
                (thread_id,)
            )

        connection.commit()


# ============================================================
# DELETE THREAD FROM CHAT LIST
# ============================================================

def delete_thread(
    thread_id: str
):

    with psycopg.connect(
        DATABASE_URL
    ) as connection:

        with connection.cursor() as cursor:

            cursor.execute(
                """
                DELETE FROM chat_threads
                WHERE thread_id = %s;
                """,
                (thread_id,)
            )

        connection.commit()
