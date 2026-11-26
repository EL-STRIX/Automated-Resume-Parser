import os
import docx
import pdfplumber


def extract_text(file):
    if isinstance(file, (str, os.PathLike)):
        filename = os.fspath(file)
    else:
        filename = getattr(file, "filename", None) or getattr(file, "name", "")

    ext = os.path.splitext(filename)[1].lower()

    if hasattr(file, "seek"):
        file.seek(0)

    if ext == ".pdf":
        with pdfplumber.open(file) as pdf:
            pages = [page.extract_text() for page in pdf.pages]
        return "\n".join(text for text in pages if text)

    if ext == ".docx":
        doc = docx.Document(file)
        parts = []
        seen_headers = set()
        for section in doc.sections:
            for p in section.header.paragraphs:
                text = p.text.strip()
                if text and text not in seen_headers:
                    seen_headers.add(text)
                    parts.append(p.text)
        parts.extend(p.text for p in doc.paragraphs if p.text and p.text.strip())
        for table in doc.tables:
            for row in table.rows:
                for cell in row.cells:
                    if cell.text and cell.text.strip():
                        parts.append(cell.text)
        return "\n".join(parts)

    raise ValueError(f"Unsupported file type: {ext or 'unknown'}. Only .pdf and .docx are supported.")
