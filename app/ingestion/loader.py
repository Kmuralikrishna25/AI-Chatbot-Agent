from pathlib import Path

from pypdf import PdfReader
from docx import Document


def load_document(file_path: str):
    """
    Load a PDF, DOCX, or TXT file.

    Returns:
        list[dict]: A list of pages/sections containing
        text and metadata.
    """

    path = Path(file_path)

    if not path.exists():
        raise FileNotFoundError(
            f"File not found: {file_path}"
        )

    extension = path.suffix.lower()

    # ========================================================
    # PDF
    # ========================================================

    if extension == ".pdf":

        reader = PdfReader(str(path))

        documents = []

        for page_number, page in enumerate(reader.pages, start=1):

            text = page.extract_text() or ""

            if text.strip():

                documents.append({
                    "text": text,
                    "page_number": page_number
                })

        return documents

    # ========================================================
    # DOCX
    # ========================================================

    elif extension == ".docx":

        document = Document(str(path))

        text = "\n".join(
            paragraph.text
            for paragraph in document.paragraphs
            if paragraph.text.strip()
        )

        return [
            {
                "text": text,
                "page_number": None
            }
        ]

    # ========================================================
    # TXT
    # ========================================================

    elif extension == ".txt":

        text = path.read_text(
            encoding="utf-8"
        )

        return [
            {
                "text": text,
                "page_number": None
            }
        ]

    # ========================================================
    # UNSUPPORTED FILE
    # ========================================================

    else:

        raise ValueError(
            f"Unsupported file type: {extension}. "
            "Supported types are PDF, DOCX, and TXT."
        )

