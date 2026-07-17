# backend/app/utils/pdf_utils.py

import os
from pypdf import PdfReader
from fastapi import HTTPException, status


def extract_text_from_pdf(relative_file_path: str) -> str:
    """
    Extracts all readable text from a PDF file on disk.

    relative_file_path example: "uploads/resumes/user_1_resume_....pdf"
    (this is exactly what we stored in Resume.file_path in Phase 8)

    Returns the extracted text as a single string.
    Raises HTTPException if the file can't be read or has no extractable text.

    NOTE: This is a GENERIC helper — it knows nothing about resumes,
    users, or AI. It just converts "PDF file path" → "text string".
    That's exactly what belongs in utils/.
    """

    # Build the absolute path to the file on disk
    full_path = os.path.normpath(
        os.path.join(
            os.path.dirname(__file__),   # .../app/utils/
            "..",                         # .../app/
            "..",                         # .../backend/
            relative_file_path,
        )
    )

    if not os.path.exists(full_path):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Resume file not found on disk",
        )

    try:
        reader = PdfReader(full_path)

        # Extract text from every page and join them together
        text_parts = []
        for page in reader.pages:
            page_text = page.extract_text()
            if page_text:
                text_parts.append(page_text)

        full_text = "\n".join(text_parts)

    except Exception:
        # pypdf can raise various errors for corrupted/encrypted PDFs
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Could not extract text from this PDF file",
        )

    if not full_text.strip():
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="This PDF appears to have no extractable text (possibly a scanned image)",
        )

    return full_text