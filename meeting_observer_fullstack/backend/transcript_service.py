from io import BytesIO
from pathlib import Path
from docx import Document
from pypdf import PdfReader

ALLOWED_EXTENSIONS = {".txt", ".md", ".docx", ".pdf"}

def extract_transcript_from_upload(uploaded_file):
    filename = uploaded_file.filename or ""
    extension = Path(filename).suffix.lower()

    if extension not in ALLOWED_EXTENSIONS:
        raise ValueError("Unsupported file type. Upload TXT, MD, DOCX or PDF.")

    raw_bytes = uploaded_file.read()
    if not raw_bytes:
        raise ValueError("The uploaded file is empty.")

    if extension in {".txt", ".md"}:
        try:
            return raw_bytes.decode("utf-8-sig").strip()
        except UnicodeDecodeError as error:
            raise ValueError("Text file must use UTF-8 encoding.") from error

    if extension == ".docx":
        document = Document(BytesIO(raw_bytes))
        paragraphs = [paragraph.text for paragraph in document.paragraphs]
        return "\n".join(paragraphs).strip()

    if extension == ".pdf":
        reader = PdfReader(BytesIO(raw_bytes))
        pages = []
        for page in reader.pages:
            page_text = page.extract_text() or ""
            pages.append(page_text)
        return "\n".join(pages).strip()

    raise ValueError("Could not extract transcript text.")
