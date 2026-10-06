import os

import psycopg
from dotenv import load_dotenv

from app.retrieval.pinecone_store import upsert_chunks


load_dotenv()


DATABASE_URL = os.getenv("DATABASE_URL")


if not DATABASE_URL:
    raise ValueError(
        "DATABASE_URL is not set. "
        "Please check your .env file."
    )


def get_chunks():

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
                ORDER BY dc.id;
                """
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


def main():

    print("\n========================================")
    print("POSTGRESQL → PINECONE INDEXING")
    print("========================================\n")


    print("Loading chunks from PostgreSQL...")

    chunks = get_chunks()

    print(
        f"Found {len(chunks)} chunk(s)."
    )


    if not chunks:

        print(
            "No chunks found in PostgreSQL."
        )

        return


    print("\nGenerating embeddings...")

    count = upsert_chunks(chunks)


    print("\n========================================")
    print("INDEXING COMPLETED")
    print("========================================")
    print(f"Vectors uploaded: {count}")


if __name__ == "__main__":
    main()