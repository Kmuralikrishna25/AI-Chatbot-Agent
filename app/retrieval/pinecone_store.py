import os

from dotenv import load_dotenv
from pinecone import Pinecone

from .embeddings import create_embedding


load_dotenv()


PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
PINECONE_INDEX_NAME = os.getenv("PINECONE_INDEX_NAME")


if not PINECONE_API_KEY:
    raise ValueError(
        "PINECONE_API_KEY is not set. "
        "Please check your .env file."
    )


if not PINECONE_INDEX_NAME:
    raise ValueError(
        "PINECONE_INDEX_NAME is not set. "
        "Please check your .env file."
    )


pc = Pinecone(api_key=PINECONE_API_KEY)

index = pc.Index(PINECONE_INDEX_NAME)


def upsert_chunks(chunks: list[dict]) -> int:

    vectors = []

    for chunk in chunks:

        chunk_id = chunk["id"]
        text = chunk["content"]

        print(
            f"Creating embedding for chunk {chunk_id}..."
        )

        embedding = create_embedding(text)

        metadata = {
            "chunk_id": chunk_id,
            "document_id": chunk["document_id"],
            "chunk_number": chunk["chunk_number"],
            "filename": chunk["filename"],
            "page_number": (
                chunk["page_number"]
                if chunk["page_number"] is not None
                else -1
            )
        }

        vectors.append(
            {
                "id": f"chunk-{chunk_id}",
                "values": embedding,
                "metadata": metadata
            }
        )

    if vectors:

        index.upsert(
            vectors=vectors
        )

    return len(vectors)