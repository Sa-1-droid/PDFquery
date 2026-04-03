# pdf_utils.py
from pypdf import PdfReader

def load_and_split_pdfs(files):
    """
    Load PDFs and split into pages.
    Returns a list of dicts: {'content', 'source', 'page'}
    """
    docs = []

    for file in files:
        reader = PdfReader(file)
        for i, page in enumerate(reader.pages):
            text = page.extract_text()
            if text and text.strip():
                docs.append({
                    "content": text.strip(),
                    "source": getattr(file, 'name', 'Uploaded PDF'),
                    "page": i + 1
                })
    return docs