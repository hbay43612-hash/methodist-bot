# Вместо выбора учебника:
# textbook_choice = st.selectbox("Учебник", textbook_files, key="textbook_selector")
# ...

# Добавим функцию поиска параграфа в учебнике:
def find_paragraph_in_textbook(theme, textbook_path):
    """Ищет в docx-файле параграф с заголовком, совпадающим с темой."""
    try:
        doc = docx.Document(textbook_path)
        current_heading = None
        paragraphs = []
        for p in doc.paragraphs:
            text = p.text.strip()
            if text and (p.style.name.lower().startswith('heading') or p.style.name.lower().startswith('заголовок')):
                if current_heading and current_heading.lower() == theme.lower():
                    return '\n'.join(paragraphs)
                current_heading = text
                paragraphs = []
            elif current_heading:
                paragraphs.append(text)
        # Если не нашли точное совпадение, ищем по вхождению
        for p in doc.paragraphs:
            if theme.lower() in p.text.lower():
                return p.text
        return ""
    except:
        return ""
