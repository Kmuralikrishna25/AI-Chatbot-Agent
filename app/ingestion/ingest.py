from pathlib import Path

from .loader import load_document
from .chunker import chunk_documents
from .database import save_document


# ============================================================
# INGEST DOCUMENT
# ============================================================

def ingest_document(file_path: str) -> int:
    """
    Complete document ingestion pipeline.

    Pipeline:
        File
        ↓
        Load
        ↓
        Chunk
        ↓
        PostgreSQL

    Returns:
        int: Database document ID
    """

    path = Path(file_path)

    # --------------------------------------------------------
    # Validate file
    # --------------------------------------------------------

    if not path.exists():
        raise FileNotFoundError(
            f"File not found: {file_path}"
        )

    # --------------------------------------------------------
    # Get file information
    # --------------------------------------------------------

    filename = path.name
    file_type = path.suffix.lower()

    print(f"\nIngesting: {filename}")
    print(f"File type: {file_type}")

    # --------------------------------------------------------
    # Step 1: Load document
    # --------------------------------------------------------

    print("\n[1/3] Loading document...")

    documents = load_document(file_path)

    print(
        f"Loaded {len(documents)} document section(s)."
    )

    # --------------------------------------------------------
    # Step 2: Chunk document
    # --------------------------------------------------------

    print("\n[2/3] Creating chunks...")

    chunks = chunk_documents(documents)

    print(
        f"Generated {len(chunks)} chunk(s)."
    )

    # --------------------------------------------------------
    # Step 3: Save to PostgreSQL
    # --------------------------------------------------------

    print("\n[3/3] Saving to PostgreSQL...")

    document_id = save_document(
        filename=filename,
        file_type=file_type,
        file_path=str(path),
        chunks=chunks
    )

    print(
        f"Document saved with ID: {document_id}"
    )

    return document_id