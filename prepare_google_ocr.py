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


def process_ocr(filename, page_num):
    f = Path(filename)
    dump = f.read_text()

    output = []
    pages = dump.split('\n\n')
    for num, page in enumerate(pages):
        if num != 0:
            page_num = derge_page_increment(page_num)

        output += [page_num, page]

    output = ''.join(output).replace('\n', '')
    output = re.sub(r'<.*?>', r'<\n>', output)

    new_file = f.parent / (f.stem + '_num' + f.suffix)
    new_file.write_text(output)


if __name__ == '__main__':
    # Path to the initial Google OCR file
    filename = '/home/helios/Documents/Lotsawa Apprenticeship/BO/G002 བག་མ་གཏོང་བ་ཕྱི་མ།/G002.txt'
    # derge page on which the text starts
    init_num = '[135a]'
    process_ocr(filename, init_num)

    # replace " [^།»]+«" with "\n\t«" to clean up the google notes ocr
    # then "»\n" with "»" to put all the notes split on two lines on a single one