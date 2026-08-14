# backend/app/utils/file_utils.py

import os
import uuid
from datetime import datetime

from fastapi import HTTPException, UploadFile, status

# ==========================================================
# Constants
# ==========================================================

UPLOAD_DIR = os.path.join(
    os.path.dirname(__file__),
    "..",
    "..",
    "uploads",
    "resumes",
)

ALLOWED_EXTENSIONS = {".pdf"}
ALLOWED_CONTENT_TYPES = {"application/pdf"}

MAX_FILE_SIZE_BYTES = 5 * 1024 * 1024  # 5 MB
PDF_MAGIC_BYTES = b"%PDF"


# ==========================================================
# Validate PDF
# ==========================================================


async def validate_pdf_file(file: UploadFile) -> bytes:
    """
    Validate an uploaded PDF file.

    Checks:
    - Filename
    - Extension
    - Content-Type
    - File Size
    - PDF Magic Bytes
    """

    if not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No filename provided",
        )

    _, extension = os.path.splitext(file.filename.lower())

    if extension not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only PDF files are allowed.",
        )

    if file.content_type not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid content type.",
        )

    contents = await file.read()

    if not contents:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded file is empty.",
        )

    if len(contents) > MAX_FILE_SIZE_BYTES:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="File size must be less than 5 MB.",
        )

    if not contents.startswith(PDF_MAGIC_BYTES):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid PDF file.",
        )

    return contents


# ==========================================================
# Generate Filename
# ==========================================================


def generate_unique_filename(
    user_id: int,
    original_filename: str,
) -> str:
    """
    Generate a unique filename for storing resumes.
    """

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    unique_id = uuid.uuid4().hex[:8]

    return f"user_{user_id}_resume_{timestamp}_{unique_id}.pdf"


# ==========================================================
# Save File
# ==========================================================


def save_file_to_disk(
    contents: bytes,
    filename: str,
) -> str:
    """
    Save the uploaded file and return its relative path.
    """

    os.makedirs(UPLOAD_DIR, exist_ok=True)

    full_path = os.path.join(UPLOAD_DIR, filename)

    with open(full_path, "wb") as file:
        file.write(contents)

    return os.path.join(
        "uploads",
        "resumes",
        filename,
    )


# ==========================================================
# Delete File
# ==========================================================


def delete_file_from_disk(file_path: str) -> None:
    """
    Delete a file from disk if it exists.
    """

    full_path = os.path.normpath(
        os.path.join(
            os.path.dirname(__file__),
            "..",
            "..",
            file_path,
        )
    )

    if os.path.exists(full_path):
        os.remove(full_path)
