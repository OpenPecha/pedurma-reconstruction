from docx import Document
from pathlib import Path
import re

def split_text(content):

    chunks = re.split('(<.+?>)', content)
    
    return chunks

def create_docx(chunks, path):
    document = Document()
    p = document.add_paragraph()

    for chunk in chunks:
        if chunk and chunk[0] == '<':
            sub_text = p.add_run(chunk)
            sub_text.font.subscript = True
            # sub_text.font.bold = True
            sub_text.font.name = 'Jomolhari'
        else:
            normal_text = p.add_run(chunk)
            normal_text.font.name = 'Jomolhari'
    
    document.save(str(f'{path}.docx'))

if __name__ == "__main__":
    vol = 73
    source_path = Path(f'data/v{vol:03}/{vol}_combined.txt')
    content = source_path.read_text(encoding='utf-8')
    double_lines = re.sub('\n', '\n\n', content)
    chunks = split_text(content)
    create_docx(chunks, source_path.parent / source_path.stem)