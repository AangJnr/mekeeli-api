def extract_doc_text(file_path: str) -> str:
    try:
        import docx
    except Exception:
        return ""

    try:
        doc = docx.Document(file_path)
        return "\n".join(paragraph.text for paragraph in doc.paragraphs)
    except Exception:
        return ""
