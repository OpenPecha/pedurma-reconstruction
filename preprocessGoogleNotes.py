from pathlib import Path
import re


def derge_page_increment(p_num):
    sides = {'a': 'b', 'b': 'a'}
    page, side = int(p_num[1:-2]), p_num[-2:-1]

    # increment
    if side == 'b':
        page += 1
    side = sides[side]

    return f'[{page}{side}]'


def preprocessGoogleNotes(filename):
    """
    this cleans up all note markers
    :param text: plain text
    :return: cleaned text
    """
    text = filename.read_text(encoding='utf-8')

    patterns = [
        # normalize punct
        ['༑', '།'],
        ['\s+', ' '],
        ['༌', '་'],      # normalize NB tsek
        ['།\s*།', '།'],
        ['ག\s*།', 'ག'],
        ['་\s*', '་'],
        ['་\s*', '་'],
        ['་\s*\n', '་'],
        ['་+', '་'],
        # special notes
        ['\(?(པོད་འདིའི་ནང་.+?\))', '\n{\g<1>}'],
        # delete tibetan numbers
        ['[༠-༩]', ''],
        # normalize edition marks
        ['〈〈?', '«'],      
        ['〉〉?', '»'], 
        ['《', '«'], 
        ['》', '»'],
        ['«\s+«', '«'],
        ['»\s+»', '»'],
        ['[=—]', '-'],
        ['\s+-', '-'],
        ['\s+\+', '+'],
        ['»\s+«', '»«'],
        [' ([^«]+»)', ' «\g<1>'],
        ['([^»]+«) ', '\g<1>» '],
        ['([^»]+«)-', '\g<1>»-'],
        
        # clean up note markers
        ['[༑།] [^།»\}]+«', '།\n\t«'],  # to clean up the google notes ocr
        ['ག [^།»\}]+«', 'ག\n\t«'],  # to clean up the google notes ocr
        ['ཀ [^།»\}]+«', 'ཀ\n\t«'],  # to clean up the google notes ocr
        ['ཤ [^།»\}]+«', 'ཤ\n\t«'],  # to clean up the google notes ocr
        [' [^ༀ-࿚]«', '\n\t«'],  # catch ། @ «
        ['»\n', '»'],  # to put all the notes split on two lines on a single one
        ]

    for p in patterns:
        text = re.sub(p[0], p[1], text)
    return text

def process(dump, page_num):

    output = []
    pages = dump.split('\n\n')
    # print(pages)
    for num, page in enumerate(pages):
        if num != 0:
            page_num = derge_page_increment(page_num)
        output += [page_num, page]

    output = ''.join(output).replace('\n', '')
    output = re.sub(r'<.*?>', r'<\n>', output)
    return output

def save(content, filename, tag):
    # saves file
    new_file = filename.parent / (filename.stem + tag + filename.suffix)
    new_file.write_text(content, encoding='utf-8')


if __name__ == '__main__':
    # Path to the initial Google OCR file
    basePath = Path("./tests/test3")
    filename = basePath / 'input' / 'a.txt'
    # derge page on which the text starts
    init_num = '[135a]'

    # script steps
    preprocessed = preprocessGoogleNotes(filename)
    processed = process(preprocessed, init_num)
    save(preprocessed, filename, '_num')
