from pathlib import Path
import re


def derge_page_increment(p_num):
    sides = {"a": "b", "b": "a"}
    page, side = int(p_num[1:-2]), p_num[-2:-1]

    # increment
    if side == "b":
        page += 1
    side = sides[side]

    return f"[{page}{side}]"


def preprocessGoogleNotes(text):
    """
    this cleans up all note markers
    :param text: plain text
    :return: cleaned text
    """
    patterns = [
        # delete tibetan numbers
        # ['[༠-༩]', ''],
        # normalize punct
        ["\r", "\n"],
        ["༑", "།"],
        ["།།", "། །"],
        ["།་", "། "],
        # normalize edition marks «<edition>»
        ["〈〈?", "«"],
        ["〉〉?", "»"],
        ["《", "«"],
        ["》", "»"],
        ["([ཀགཤ།]) །«", "\g<1> «"],
        ["([ཀགཤ།])་?«", "\g<1> «"],
        ["»\s+", "»"],
        ["«\s+«", "«"],
        ["»+", "»"],
        ["[=—]", "-"],
        ["\s+-", "-"],
        ["\s+\+", "+"],
        ["»\s+«", "»«"],
        # add missing markers
        [" ([^«]+»)", " «\g<1>"],
        ["([^»]+«) ", "\g<1>» "],
        ["([^»]+«)-", "\g<1>»-"],
        ["(«[^་]+?་)([^»])", "\g<1>»\g<2>"],
        # tag pedurma page numbers #<vol-page>#
        [
            "(\n[0-9]+?)((-+?)|(\n))([0-9]+?\n)",
            "#\g<1>-\g<5>#",
        ],  # separators FIXME not catching 73-821
        ["([^#]\n+?)-([0-9]+?\n)", "#\g<1>-\g<2>#"],  #
        # ['([^\d#-])([0-9]{3,10})', '\g<1>#\g<2>#'],    # not well formated
        # ['\d#(\d+?-\d+?)#«', '\g<1>«'],    # clear false positives
        ["([02468])#", "\g<1>e#"],  # even:
        ["([13579])#", "\g<1>o#"],  # odd: only have text། [༠-༩]
        # ['ག་', 'ག '],   # »-ཅག་༧ »གཞག་༡9 TODO
        ["\s+", " "],
        ["།\s།\s*\n", "།\n"],
        ["།\s།\s«", "། «"],
        ["༌", "་"],  # normalize NB tsek
        ["ག\s*།", "ག"],
        ["་\s*", "་"],
        ["་\s*", "་"],
        ["་\s*\n", "་"],
        ["་+", "་"],
        #
        ["([^+\s་ཀ-ྼ])། ", "\g<1>?། "],  # ༧། TODO
        # special notes
        ["(\(?པོད་འདིའི་ནང་.+?\))\s*", "{\g<1>}\n"],
        ["(\{[^\}]+?) (.+?\})", "\g<1>_\g<2>"],  # deal with spaces in special notes
        ["(\{[^\}]+?) (.+?\})", "\g<1>_\g<2>"],  # deal with spaces in special notes
        ["(\{[^\}]+?) (.+?\})", "\g<1>_\g<2>"],  # deal with spaces in special notes
        ["\(\s+?\{", "{("],  # include ( in the note
        # tag note markers \<<note>\>
        ["། ([^།»\{\}]+)«", "།\n<m\g<1>>«"],
        ["<m\n(\}\{.+?)>«", "\g<1>«"],  # fix special note markers
        ["([ཀགཤ།] )([^།»\{\}]+)«", "\g<1>\n<m\g<2>>«"],
        # ['ཀ ([^།»\{\}]+)«', 'ཀ\n<\g<1>>«'],
        # ['ཤ ([^།»\{\}]+)«', 'ཤ\n<\g<1>>«'],
        # [' ([^ༀ-࿚]+)«', '\n<\g<1>>«'],  # catch ། @ «
        # delete note markers
        # ['<', ''],
        # headers ++<header>++
        # ['(#.+?e#[^།]+?།)', '#++\g<1>\g<2>++\g<3>«'],   # even
        ["»\n", "»"],  # put all the notes split on two lines on a single one
        ["། །\n", "།\n"],
        ["<m.+?>", "4"],  # replace m tag with m only
    ]

    # «ཅོ་»«ཞོལ་»གྲག་༡༨)

    for p in patterns:
        text = re.sub(p[0], p[1], text)
    return text


"""
»འཁྲང་། ༄༅། «གཡུང་»
"""


def preprocessNamselNotes(text):
    """
    this cleans up all note markers
    :param text: plain text
    :return: cleaned text
    """

    patterns = [
        # normalize single zeros '༥༥་' --> '༥༥༠'
        ["([༠-༩])[་༷]", "\g<1>༠"],
        # normalize double zeros '༧༷་' --> '༧༠༠'
        ["༠[་༷]", "༠༠"],
        ["༠[་༷]", "༠༠"],
        # normalize punct
        ["\r", "\n"],
        ["༑", "།"],
        ["།།", "། །"],
        ["།་", "། "],
        ["\s+", " "],
        ["།\s།\s*\n", "།\n"],
        ["།\s།\s«", "། «"],
        ["༌", "་"],  # normalize NB tsek
        ["ག\s*།", "ག"],
        ["་\s*", "་"],
        ["་\s*", "་"],
        ["་\s*\n", "་"],
        ["་+", "་"],
        # delete tibetan numbers
        # ['[༠-༩]', ''],
        # headers ++<header>++
        # ['#\n(.+?)«', '#\n++\g<1>\n++«'],
        # special notes
        ["\(?(པོད་འདིའི་.+?)\)\s*", "\n{\g<1>}\n"],
        ["(\{[^\}]+?) (.+?\})", "\g<1>_\g<2>"],  # deal with spaces in special notes
        ["(\{[^\}]+?) (.+?\})", "\g<1>_\g<2>"],  # deal with spaces in special notes
        ["(\{[^\}]+?) (.+?\})", "\g<1>_\g<2>"],  # deal with spaces in special notes
        # normalize and tag page numbers '73ཝ་768' --> ' <p73-768> '
        ["([0-9]+?)[ཝ—-]་?([0-9]+)", " <p\g<1>-\g<2>> "],
        # tag page references '༡༤༥ ①' --> <p༡༤༥> ①'
        [" ?([༠-༩]+?)(\s\(?[①-⓪༠-༩ ཿ༅]\)?)", " \n<r\g<1>>\g<2>"],  # basic page ref
        # normalize edition marks «<edition>»
        ["〈〈?", "«"],
        ["〉〉?", "»"],
        ["《", "«"],
        ["》", "»"],
        ["([ཀགཤ།]) །«", "\g<1> «"],
        ["([ཀགཤ།])་?«", "\g<1> «"],
        ["»\s+", "»"],
        ["«\s+«", "«"],
        ["»+", "»"],
        ["[=—]", "-"],
        ["\s+-", "-"],
        ["\s+\+", "+"],
        ["»\s+«", "»«"],
        # add missing markers
        [" ([^«]+»)", " «\g<1>"],
        ["([^»]+«) ", "\g<1>» "],
        ["([^»]+«)-", "\g<1>»-"],
        ["(«[^་]+?་)([^»])", "\g<1>»\g<2>"],
        ["(»[^«]+?)»", "\g<1>"],  # fix extra
        # tag note markers <note>
        ["([ཤཀག།\n] )([^།»\}<>]+)«", "\g<1>\n<m\g<2>>«"],
        ["<\n(\{.+?)>«", "\g<1>«"],  # fix special note markers
        ["(\s?[①-㊿༠-༩]+)«", "\n<m\g<1>>«"],
        ["\n<m([^ >]+?[ཤཀག།] )", "\g<1>\n<m"],  # fix multi-syls A
        ["\n([^།»\{}<>]+)«", "\n<m\g<1>>«"],  # fix ref at line start
        ["> ?([^>«»]+?)«", ">\n<m\g<1>>«"],  # fix ref + marker
        ["m\s+", "m"],  # delete spaces after m
        ["([^\n])<r", "\g<1>\n<r"],  # fix inline ref
        ["\s([^<>«» ]+?)«", " \n<m\g<1>>«"],  # fix ?
        ["«[^»]+?«ང་»", "«གཡུང་»"],  # fix g.yung
        # [' ([^ༀ-࿚]+)«', '\n<\g<1>>«'],  # catch ། @ «
        # Add page references to first footnote marker
        # ['([༠-༩]+)([\n\s]*)<([\s]*①)', '\g<2><\g<1>\g<3>'],
        ["»\n([^<])", "»\g<1>"],  # to put all the notes split on two lines on a single one
        ["། །\n", "།\n"],
        ["(<[mpr])\n", "\g<1>"],
        ["\n<m\s*>", ""],  # fix multi-syls B
        ["\n<m(\{[^<>]+?)>", "\g<1>"],  # keep special notes on first line
        ["\n<m([^>]+?།[^>]+?)>", "\g<1>"],  # keep split notes on first line
        # Deal with multiple markers
        ["<m\(?(.*?)\)?>", "<m\g<1>>"],  # clear ()
        ["<m>", "<m0>"],  # add replacement where needed
        ["<m.?དྷི.?>", "<m4>"],
        ["<m.?ཉེ.?>", "<m༡༠>"],
        ["<m.?ཀྱེ.?>", "<m༨>"],
        ["<m.?སྟེ.?>", "<m10>"],
        ["<m་?ཏུ་?>", "<m9>"],
        ["<m་?ཏུཉེ་?>", "<m10>"],
        ["<m་?ཏུམེ་?>", "<m11>"],
        ["<m་?པོཉེ་?>", "<m༦>"],
        ["<m་?ཕོཉེ་?>", "<m11>"],
        ["<m་?ཐོཉེ་?>", "<m11>"],
        ["<m་?ཐོའི་?>", "<m11>"],
        ["<m་?སྣེ་?>", "<m༣>"],
        ["<m་?ནི་?>", "<m༣>"],
        ["<m་?བེ་?>", "<m༣>"],
        ["<m་?ཐོ་?>", "<m10>"],
        ["<m་?ཐོན་?>", "<m10>"],
        ["<m་?ཡི་?>", "<m10>"],
        ["<m་?པེ་?>", "<m༤>"],
        ["<m་?འོན་?>", "<m12>"],
        ["<m་?ཧུཉེ་?>", "<m13>"],
        ["<m་?ཉུགེ?>", "<m13>"],
        ["<m་?གེ་?>", "<m5>"],
        ["<m་?དུ་?>", "<m10>"],
        ["<m་?༠་?>", "<m0>"],
        ["<m་?ཿ་?>", "<m༡>"],
        ["<mགདུ་>", "<m⑧⑧>"],
        ["<m88>", "<m⑧⑧>"],
        ["<m[^> །]{6,8}>", "<m⑧⑧>"],
        ["<m888>", "<m⑧⑧⑧>"],
        ["<m[^> །]{9,14}>", "<m⑧⑧⑧>"],
        ["<m8888>", "<m⑧⑧⑧⑧>"],
        ["<m[^> །]{15,20}>", "<m⑧⑧⑧⑧>"],
        ["<m88888>", "<m⑧⑧⑧⑧⑧>"],
        ["<m་?([①-⓪])་?>", "<m\g<1>>"],
        ["<m[0༠]>", "<m⓪>"],
        ["<m[༡1]>", "<m①>"],
        ["<m[2༢]>", "<m②>"],
        ["<m[3༣]>", "<m③>"],
        ["<m[4༤]>", "<m④>"],
        ["<m[5༥]>", "<m⑤>"],
        ["<m[6༦]>", "<m⑥>"],
        ["<m[7༧]>", "<m⑦>"],
        ["<m[8༨]>", "<m⑧>"],
        ["<m[9༩]>", "<m⑨>"],
        ["<m10>", "<m⑩>"],
        ["<m༡༠>", "<m⑩>"],
        ["<m11>", "<m⑪>"],
        ["<m༡༡>", "<m⑪>"],
        ["<m12>", "<m⑫>"],
        ["<m༡༢>", "<m⑫>"],
        ["<m13>", "<m⑬>"],
        ["<m༡༣>", "<m⑬>"],
        ["<m14>", "<m⑭>"],
        ["<m༡༤>", "<m⑭>"],
        ["<m15>", "<m⑮>"],
        ["<m༡༥>", "<m⑮>"],
        ["<m16>", "<m⑯>"],
        ["<m༡༦>", "<m⑯>"],
        ["<m17>", "<m⑰>"],
        ["<m༡༧>", "<m⑰>"],
        ["<m18>", "<m⑱>"],
        ["<m༡༨>", "<m⑱>"],
        ["<m19>", "<m⑲>"],
        ["<m༡༩>", "<m⑲>"],
        ["<m20>", "<m⑳>"],
        ["<m༢༠>", "<m⑳>"],
        ["<m21>", "<m⑳>"],
        ["<m༢༡>", "<m⑳>"],
        ["<m22>", "<m⑳>"],
        ["<m༢༢>", "<m⑳>"],
        ["<m23>", "<m⑳>"],
        ["<m24>", "<m⑳>"],
        ["<m25>", "<m⑳>"],
        ["<m26>", "<m⑳>"],
        ["<m27>", "<m⑳>"],
        ["<m28>", "<m⑳>"],
        ["<m29>", "<m⑳>"],
        ["<m30>", "<m⑳>"],
        # duplicate
        # ["(\n<m)([①-⓪])([①-⓪])([①-⓪])([①-⓪])([①-⓪])(>.+)","\g<1>\g<2>\g<7>\g<1>\g<3>\g<7>\g<1>\g<4>\g<7>\g<1>\g<5>\g<7>\g<1>\g<6>\g<7>"],
        # ["(\n<m)([①-⓪])([①-⓪])([①-⓪])([①-⓪])(>.+)","\g<1>\g<2>\g<6>\g<1>\g<3>\g<6>\g<1>\g<4>\g<6>\g<1>\g<5>\g<6>"],
        # ["(\n<m)([①-⓪])([①-⓪])([①-⓪])(>.+)","\g<1>\g<2>\g<5>\g<1>\g<3>\g<5>\g<1>\g<4>\g<5>"],
        # ["(\n<m)([①-⓪])([①-⓪])(>.+)","\g<1>\g<2>\g<4>\g<1>\g<3>\g<4>"],
    ]

    for p in patterns:
        text = re.sub(p[0], p[1], text)
    return text


"""
«༦༣༦
«ཅོ་»༦༢་ཿ«སྣ། 
བརྩིག༦༡༦\n< ①>«ཅོ་»འགྲོའོ།
(གོང་གི་དུམ་བུ་འདི་(དེབ་འདིའི་ལྡེབ་༦༡༥ང༢༡་༦༡༨ང༡༦པའི་བར་)
<①>«གཡུང་»ཉིར། \n<ཅིག >«པེ་»ཉིད། \n<ཅིག ①>«སྣར་»«ཞོལ་»མམ། 

[^»> ]«
"""


def save(content, filename, tag):
    # saves file
    new_file = filename.parent / (filename.stem + tag + filename.suffix)
    new_file.write_text(content, encoding="utf-8")


if __name__ == "__main__":
    # Path to the initial Google OCR file
    basePath = Path("./input/footnote_text")

    googlePath = basePath / "googleOCR_text" / "73durchen-google.txt"
    namselPath = basePath / "namselOCR_text" / "73durchen-namsel.txt"

    # derge page on which the text starts
    init_num = "[135a]"

    # Google footnotes
    google_content = googlePath.read_text(encoding="utf-8")
    # get text
    googlePrep = preprocessGoogleNotes(google_content)
    # get text
    save(googlePrep, googlePath, "_num")
    # get text
    # googleProc = process(googlePrep, init_num)

    # Namsel footnotes
    namsel_content = namselPath.read_text(encoding="utf-8")
    # isolate and normalize pedurma pages '73-23་' --> ' <p73-230> '
    # namsel_content = tag_page_numbers(namsel_content)
    # isolate and normalize pedurma page references '༢༣་' --> ' <r༢༣༠> '
    # namsel_content = tag_page_references(namsel_content)
    # save(namsel_content, namselPath, '_num')
    # clean content
    namselPrep = preprocessNamselNotes(namsel_content)
    # write to file
    save(namselPrep, namselPath, "_num")
    # get text
    # namselProc = process(namselPrep, init_num)
