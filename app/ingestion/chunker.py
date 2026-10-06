from langchain_text_splitters import RecursiveCharacterTextSplitter



# CHUNKING CONFIGURATION
CHUNK_SIZE = 1000
CHUNK_OVERLAP = 200

# CREATE TEXT SPLITTER
text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=CHUNK_SIZE,
    chunk_overlap=CHUNK_OVERLAP,
    separators=[
        "\n\n",
        "\n",
        ". ",
        " ",
        ""
    ]
)
# CHUNK DOCUMENT
def chunk_documents(documents: list[dict]) -> list[dict]:
    """
    Split loaded documents into smaller chunks.

    Each input document contains:
        text
        page_number

    Returns:
        list[dict]: Chunked documents with metadata.
    """

    chunks = []

    for document in documents:

        text = document["text"]
        page_number = document["page_number"]

        split_texts = text_splitter.split_text(text)

        for chunk_number, chunk_text in enumerate(
            split_texts,
            start=1
        ):

            chunks.append({
                "text": chunk_text,
                "page_number": page_number,
                "chunk_number": chunk_number
            })

    return chunks

