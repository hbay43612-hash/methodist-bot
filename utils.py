def get_paragraphs_from_docx(filepath):
    try:
        doc = docx.Document(filepath)
        paragraphs = []
        for p in doc.paragraphs:
            txt = p.text.strip()
            style_name = p.style.name.lower()
            if txt and ("heading" in style_name or "заголовок" in style_name or re.match(r'^[А-Я]|^\d', txt)):
                paragraphs.append(txt)
        return paragraphs
    except:
        return []

def get_textbook_paragraph_content(filepath, heading):
    try:
        doc = docx.Document(filepath)
        result = []
        found = False
        for p in doc.paragraphs:
            txt = p.text.strip()
            if found:
                if p.style.name.lower() and ("heading" in p.style.name.lower() or "заголовок" in p.style.name.lower()):
                    break
                if txt:
                    result.append(txt)
            if txt == heading:
                found = True
        return "\n".join(result)
    except:
        return ""
