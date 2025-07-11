from fastapi import UploadFile
from app.core.config import settings
import os
from pathlib import Path

class FileHandler:
    @staticmethod
    async def save_file(file: UploadFile) -> str:
        os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
        file_path = str(Path(settings.UPLOAD_DIR) / file.filename)
        with open(file_path, "wb") as f:
            f.write(await file.read())
        return file_path

    @staticmethod
    def read_file_content(file_path: str) -> str:
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read()

    @staticmethod
    def extract_content(file_path: str) -> str:
        """
        Extracts full content from a file. For CSV, returns text. For PDF, extracts text using pdfplumber and returns as string.
        """
        if file_path.lower().endswith('.csv'):
            content = FileHandler.read_file_content(file_path)
        elif file_path.lower().endswith('.pdf'):
            try:
                import pdfplumber
                with pdfplumber.open(file_path) as pdf:
                    text = "\n".join(page.extract_text() or "" for page in pdf.pages)
                content = text
            except Exception as e:
                raise ValueError(f"Failed to extract text from PDF: {e}")
        else:
            raise ValueError("Unsupported file type for extraction.")
        return content

    @staticmethod
    def split_content_for_model(content: str, max_length: int = 8000) -> list:
        """
        Splits content into chunks of max_length characters for safe model processing.
        """
        return [content[i:i+max_length] for i in range(0, len(content), max_length)]