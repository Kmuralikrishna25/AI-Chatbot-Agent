import os

import psycopg
from dotenv import load_dotenv


load_dotenv()


DATABASE_URL = os.getenv("DATABASE_URL")


if not DATABASE_URL:
    raise ValueError(
        "DATABASE_URL is not set. "
        "Please check your .env file."
    )


def save_document(
    filename: str,
    file_type: str,
    file_path: str,
    chunks: list[dict]
) -> int:

    with psycopg.connect(DATABASE_URL) as connection:

        with connection.cursor() as cursor:

            cursor.execute(
                """
                INSERT INTO documents
                    (filename, file_type, file_path)
                VALUES
                    (%s, %s, %s)
                RETURNING id;
                """,
                (
                    filename,
                    file_type,
                    file_path
                )
            )

            document_id = cursor.fetchone()[0]

            for chunk in chunks:

                cursor.execute(
                    """
                    INSERT INTO document_chunks
                        (
                            document_id,
                            chunk_number,
                            content,
                            page_number
                        )
                    VALUES
                        (%s, %s, %s, %s);
                    """,
                    (
                        document_id,
                        chunk["chunk_number"],
                        chunk["text"],
                        chunk["page_number"]
                    )
                )

        connection.commit()

    return document_id


def get_chunks_by_ids(
    chunk_ids: list[int]
) -> list[dict]:

    if not chunk_ids:
        return []


    with psycopg.connect(DATABASE_URL) as connection:

        with connection.cursor() as cursor:

            cursor.execute(
                """
                SELECT
                    dc.id,
                    dc.document_id,
                    dc.chunk_number,
                    dc.content,
                    dc.page_number,
                    d.filename
                FROM document_chunks dc
                JOIN documents d
                    ON dc.document_id = d.id
                WHERE dc.id = ANY(%s);
                """,
                (chunk_ids,)
            )

            rows = cursor.fetchall()


    chunks = []

    for row in rows:

        chunks.append(
            {
                "id": row[0],
                "document_id": row[1],
                "chunk_number": row[2],
                "content": row[3],
                "page_number": row[4],
                "filename": row[5]
            }
        )


    return chunks