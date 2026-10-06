from app.ingestion.database import get_chunks_by_ids

from .embeddings import create_embedding
from .pinecone_store import index


def semantic_search(
    query: str,
    top_k: int = 5
) -> list[dict]:

    print(f"\nSearching Pinecone for: {query}")

    query_embedding = create_embedding(query)

    results = index.query(
        vector=query_embedding,
        top_k=top_k,
        include_metadata=True
    )

    if not results.matches:
        return []

    chunk_ids = [
        int(match.metadata["chunk_id"])
        for match in results.matches
    ]

    chunks = get_chunks_by_ids(chunk_ids)

    chunks_by_id = {
        chunk["id"]: chunk
        for chunk in chunks
    }

    final_results = []

    for match in results.matches:

        chunk_id = int(
            match.metadata["chunk_id"]
        )

        chunk = chunks_by_id.get(chunk_id)

        if not chunk:
            continue

        final_results.append(
            {
                "chunk_id": chunk_id,
                "document_id": chunk["document_id"],
                "chunk_number": chunk["chunk_number"],
                "content": chunk["content"],
                "filename": chunk["filename"],
                "page_number": chunk["page_number"],
                "score": match.score
            }
        )

    return final_results