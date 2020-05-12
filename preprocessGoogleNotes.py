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
        # delete tibetan numbers
        # ['[༠-༩]', ''],
        # normalize punct
        ['\r', '\n'],
        ['༑', '།'],
        ['།།', '། །'],
        ['།་', '། '],
        # ['ག་', 'ག '],   # »-ཅག་༧ »གཞག་༡9 TODO
        ['\s+', ' '],
        ['།\s།\s*\n', '།\n'],
        ['།\s།\s«', '། «'],
        ['༌', '་'],      # normalize NB tsek
        ['ག\s*།', 'ག'],
        ['་\s*', '་'],
        ['་\s*', '་'],
        ['་\s*\n', '་'],
        ['་+', '་'],
        # 
        ['([^+\s་ཀ-ྼ])། ', '\g<1>?། '],   # ༧། TODO
        # tag pedurma page numbers #<vol-page>#
        ['([0-9]{1,3})\D་?([0-9]+)', '\n#\g<1>-\g<2>#\n'],    # well formated
        ['([^\d#-])([0-9]{3,10})', '\g<1>\n#\g<2>#\n'],    # not well formated
        # headers ++<header>++
        ['#\n(.+?)«', '#\n++\g<1>\n++«'],
        # special notes
        ['\(?(པོད་འདིའི་ནང་.+?)\)\s*', '\n{\g<1>}\n'],
        ['(\{[^\}]+?) (.+?\})', '\g<1>_\g<2>'],     # deal with spaces in special notes
        ['(\{[^\}]+?) (.+?\})', '\g<1>_\g<2>'],     # deal with spaces in special notes
        ['(\{[^\}]+?) (.+?\})', '\g<1>_\g<2>'],     # deal with spaces in special notes
        # normalize edition marks «<edition>»
        ['〈〈?', '«'],      
        ['〉〉?', '»'], 
        ['《', '«'], 
        ['》', '»'],
        ['([ཀགཤ།]) །«', '\g<1> «'],
        ['([ཀགཤ།])་?«', '\g<1> «'],
        ['»\s+', '»'],
        ['«\s+«', '«'],
        ['»+', '»'],
        ['[=—]', '-'],
        ['\s+-', '-'],
        ['\s+\+', '+'],
        ['»\s+«', '»«'],
        # add missing markers
        [' ([^«]+»)', ' «\g<1>'],
        ['([^»]+«) ', '\g<1>» '],
        ['([^»]+«)-', '\g<1>»-'],
        ['(«[^་]+?་)([^»])', '\g<1>»\g<2>'],
        # tag note markers \<<note>\>
        ['། ([^།»\}]+)«', '།\n<\g<1>>«'],
        ['<\n(\{.+?)>«', '\g<1>«'],     # fix special note markers
        ['([ཀགཤ།] )([^།»\{\}]+)«', '\g<1>\n<\g<2>>«'],
        # ['ཀ ([^།»\{\}]+)«', 'ཀ\n<\g<1>>«'],
        # ['ཤ ([^།»\{\}]+)«', 'ཤ\n<\g<1>>«'],
        # [' ([^ༀ-࿚]+)«', '\n<\g<1>>«'],  # catch ། @ «
        # delete note markers
        # ['<', ''],

        ['»\n', '»'],  # to put all the notes split on two lines on a single one
        ['། །\n', '།\n'],
        ]


    for p in patterns:
        text = re.sub(p[0], p[1], text)
    return text
'''
»འཁྲང་། ༄༅། «གཡུང་»
'''

def preprocessNamselNotes(filename):
    """
    this cleans up all note markers
    :param text: plain text
    :return: cleaned text
    """
    text = filename.read_text(encoding='utf-8')

    patterns = [
        # normalize punct
        ['\r', '\n'],
        ['༑', '།'],
        ['།།', '། །'],
        ['།་', '། '],
        ['\s+', ' '],
        ['།\s།\s*\n', '།\n'],
        ['།\s།\s«', '། «'],
        ['༌', '་'],      # normalize NB tsek
        ['ག\s*།', 'ག'],
        ['་\s*', '་'],
        ['་\s*', '་'],
        ['་\s*\n', '་'],
        ['་+', '་'],
        # tag pedurma page numbers #<vol-page>#
        ['([0-9]{1,3})\D་?([0-9]+)', '\n#\g<1>-\g<2>#\n'],    # well formated
        # ['([^\d#-])([0-9]{3,10})', '\g<1>\n#\g<2>#\n'],    # not well formated
        # delete tibetan numbers
        # ['[༠-༩]', ''],
        # headers ++<header>++
        # ['#\n(.+?)«', '#\n++\g<1>\n++«'],
        # special notes
        ['\(?(པོད་འདིའི་.+?)\)\s*', '\n{\g<1>}\n'],
        ['(\{[^\}]+?) (.+?\})', '\g<1>_\g<2>'],     # deal with spaces in special notes
        ['(\{[^\}]+?) (.+?\})', '\g<1>_\g<2>'],     # deal with spaces in special notes
        ['(\{[^\}]+?) (.+?\})', '\g<1>_\g<2>'],     # deal with spaces in special notes
        # normalize edition marks «<edition>»
        ['〈〈?', '«'],      
        ['〉〉?', '»'], 
        ['《', '«'], 
        ['》', '»'],
        ['([ཀགཤ།]) །«', '\g<1> «'],
        ['([ཀགཤ།])་?«', '\g<1> «'],
        ['»\s+', '»'],
        ['«\s+«', '«'],
        ['»+', '»'],
        ['[=—]', '-'],
        ['\s+-', '-'],
        ['\s+\+', '+'],
        ['»\s+«', '»«'],
        # add missing markers
        [' ([^«]+»)', ' «\g<1>'],
        ['([^»]+«) ', '\g<1>» '],
        ['([^»]+«)-', '\g<1>»-'],
        ['(«[^་]+?་)([^»])', '\g<1>»\g<2>'],
        # tag note markers \<<note>\>
        ['([ཤཀག།] )([^།»\}]+)«', '\g<1>\n<\g<2>>«'],
        ['<\n(\{.+?)>«', '\g<1>«'],     # fix special note markers
        ['(\s?[①-㊿]+)«', '\n<\g<1>>«'],
        # [' ([^ༀ-࿚]+)«', '\n<\g<1>>«'],  # catch ། @ «
        # Normalize zero in page references
        ['([༠-༩])[༷་]', '\g<1>༠'],
        # Add page references to first footnote marker
        ['([༠-༩]+)([\n\s]*)<([\s]*①)', '\g<2><\g<1>\g<3>'],

        ['»\n', '»'],  # to put all the notes split on two lines on a single one
        ['། །\n', '།\n'],
        ]


    for p in patterns:
        text = re.sub(p[0], p[1], text)
    return text
'''
«༦༣༦
«ཅོ་»༦༢་ཿ«སྣ། 
བརྩིག༦༡༦\n< ①>«ཅོ་»འགྲོའོ།
(གོང་གི་དུམ་བུ་འདི་(དེབ་འདིའི་ལྡེབ་༦༡༥ང༢༡་༦༡༨ང༡༦པའི་བར་)
<①>«གཡུང་»ཉིར། \n<ཅིག >«པེ་»ཉིད། \n<ཅིག ①>«སྣར་»«ཞོལ་»མམ། 

[^»> ]«
'''


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
    basePath = Path("./input/footnote_text")
    googlePath = basePath / 'googleOCR_text' / '73durchen-google.txt'
    namselPath = basePath / 'namselOCR_text' / '73durchen-namsel.txt'
    # derge page on which the text starts
    init_num = '[135a]'

    # script steps
    googlePrep = preprocessGoogleNotes(googlePath)
    save(googlePrep, googlePath, '_num')
    googleProc = process(googlePrep, init_num)

    namselPrep = preprocessNamselNotes(namselPath)
    save(namselPrep, namselPath, '_num')
    namselProc = process(namselPrep, init_num)
