"""
Pedurma Footnote Reconstruction.
Footnote reconstruction script for the ocred katen pedurma using annotation transfer with 
google's dmp.(https://github.com/google/diff-match-patch) 
This script allows to transfer a specific set of annotations(footnotes and footnote markers) 
from text A(OCRed etext) to text B(clean etext). We first compute a diff between  texts 
A and B, then filter the annotations(dmp diffs) we want to transfer and then apply them to 
text B.
"""
import re
from pathlib import Path

from diff_match_patch import diff_match_patch


def preprocess_footnote(target, source):
    """Normalises edition markers to minimise noise in diffs.

    Args:
        target (str): Target text
        source (str): source text

    Returns:
        str: normalised target text
        str: normalised source text
    """
    patterns = [["〈〈?", "«"], ["〉〉?", "»"], ["《", "«"], ["》", "»"]]
    clean_target = target
    clean_source = source
    for old_pattern, std_pattern in patterns:
        clean_target = re.sub(old_pattern, std_pattern, clean_target)
        clean_source = re.sub(old_pattern, std_pattern, clean_source)
    return clean_target, clean_source


def get_diff(target, source):
    """Compute diff between target and source using DMP.

    Args:
        target (str): target text
        source (str): source text

    Returns:
        list: list of diffs
    """
    dmp = diff_match_patch()
    # Diff_timeout is set to 0 inorder to compute diff till end of file.
    dmp.Diff_Timeout = 0
    diffs = dmp.diff_main(target, source)
    # beautifies the diff list
    dmp.diff_cleanupSemantic(diffs)
    print(" Diff computation done!!!")
    return diffs


def rm_noise(diff):
    """Filter out noise from diff text.

    Args:
        diff (str): diff text

    Returns:
        str: cleaned diff text
    """
    result = diff
    patterns = [
        "\n",
        "་+?",
        "\u0020+",
        "།",
    ]
    for pattern in patterns:
        noise = re.search(pattern, diff)
        if noise:
            result = result.replace(noise[0], "")
    return result


def get_pg_ann(diff, vol_num):
    """Add page annotion to page pattern with page number as payload.

    Args:
        diff (str): diff text
        vol_num (int): volume number

    Returns:
        str: page annotation <<pg_num, pg_pattern>>
    """
    pg_no_pattern = f"{vol_num}\S*?(\d+)"
    pg_pat = re.search(pg_no_pattern, diff)
    pg_num = pg_pat.group(1)
    return f"<<{pg_num},{pg_pat[0]}>>"


def identify_footnote_marker(diff):
    """Extract footnote marker from diff text.

    Args:
        diff (str): diff text

    Returns:
        str: footnote marker
    """
    result = ""
    ann_ = ""
    patterns = [
        "[\u2460-\u2469]",
        "[\u0F20-\u0F29]+",
        "[\u0030-\u0039]+",
    ]
    for pattern in patterns:
        ann = re.search(pattern, diff)
        if ann:
            ann_ += ann[0]
    return ann_


def is_circle_number(footnote_marker):
    """Check whether footnote marker is number in circle or not and if so returns equivalent number.

    Args:
        footnote_marker (str): footnote marker

    Returns:
        str: number inside the circle
    """
    value = ""
    number = re.search("[\u2460-\u2469]", footnote_marker)
    if number:
        circle_num = {
            "①": "1",
            "②": "2",
            "③": "3",
            "④": "4",
            "⑤": "5",
            "⑥": "6",
            "⑦": "7",
            "⑧": "8",
            "⑨": "9",
            "⑩": "10",
        }
        value = circle_num.get(number[0])
    return value


def translate_tib_number(footnote_marker):
    """Translate tibetan numeral in footnote marker to roman number.

    Args:
        footnote_marker (str): footnote marker

    Returns:
        str: footnote marker having numbers in roman numeral
    """
    value = ""
    tib_num = {
        "༠": "0",
        "༡": "1",
        "༢": "2",
        "༣": "3",
        "༤": "4",
        "༥": "5",
        "༦": "6",
        "༧": "7",
        "༨": "8",
        "༩": "9",
    }
    numbers = re.finditer("\d", footnote_marker)
    if numbers:
        for number in numbers:
            if re.search("[\u0F20-\u0F29]", number[0]):
                value += tib_num.get(number[0])
            else:
                value += number[0]
    return value


def get_payload(footnote_marker):
    """Compute the equivalent numbers in footnote marker and return as payload.

    Args:
        footnote_marker (str): footnote marker

    Returns:
        str: numbers in footnote marker
    """
    value = ""
    if is_circle_number(footnote_marker):
        value = is_circle_number(footnote_marker)
        return value
    elif translate_tib_number(footnote_marker):
        value = translate_tib_number(footnote_marker)
        return value
    return value


def apply_diff_body(diffs, vol_num):
    """Filter the diffs; add diff markers '<diff>';apply filtered diffs to target text.

    Args:
        diffs (list): list of diffs
        vol_num (int): volume number

    Returns:
        str: target text with transfered annotations with markers.
    """
    result = ""
    for diff in diffs:
        if diff[0] == 0 or diff[0] == -1:  # in target not in source
            result += diff[1]
        elif diff[0] == 1:  # in source not in target
            diff_ = rm_noise(diff[1])  # keep only footnote and footnote markers
            if re.search(f"{vol_num}+\S+\d+", diff_):
                result += get_pg_ann(diff_, vol_num)
            else:
                footnote_marker = identify_footnote_marker(diff_)  # add annotation markers
                if footnote_marker:
                    payload = get_payload(footnote_marker)
                    result += f"<{payload},{footnote_marker}>"
                elif diff_:
                    result += f"<{diff_}>"
    return result


def add_link(text, offset):
    """Add link of source image page.

    Args:
        text (str): target text having footnote maker transfered
        offset (int): source image page offset

    Returns:
        str: target text with source image page link
    """
    result = ""
    lines = text.splitlines()
    for line in lines:
        if re.search("<<\d+,\d+\S+\d+>>", line):
            pg_no = re.search("<<(\d+),(\d+\S+\d+)>>", line)
            if re.search("[\u0030-\u0039]", pg_no.group(2)):
                if len(pg_no.group(1)) > 3:
                    pg_no = int(pg_no.group(1)[:3]) + offset
                else:
                    pg_no = int(pg_no.group(1)) + offset
                link = f"[https://www.tbrc.org/browser/ImageService?work=W1PD96682&igroup=I1PD96856&image={pg_no}&first=1&last=862&fetchimg=yes]"
                result += line + "\n" + link + "\n"
            else:
                result += line + "\n"
        else:
            result += line + "\n"
    return result


def get_addition_footnote(diff):
    value = diff_cleaner(diff)
    result = ""
    ann_ = ""
    patterns = ["[\u2460-\u2469]", "[\u0F20-\u0F29]+", "\)", "\(", "\d+", "\d+\S+\d+"]
    for pattern in patterns:
        ann = re.search(pattern, value)
        if ann:
            ann_ = ann[0]
    if ann_:
        addition = rm_noise(ann_)
        pay_load = get_payload(addition)
        result = re.sub(ann_, f"<{pay_load},{ann_}>", value, 1)
        cir_num = re.search("(>|་)[\u2460-\u2469]", result)
        if cir_num:
            cpl = get_payload(cir_num[0][1:])
            result = re.sub("[\u2460-\u2469]", f"<{cpl},{cir_num[0][1:]}>", result, 1)
        pg = re.search("»\d+,(74\S*?\d+)", result)
        if pg:
            ppl = get_payload(pg[0][1:])
            result = re.sub("74\S*?\d+", f"<{ppl},{pg.group(1)}>", result, 1)
    else:
        result = f"<{value}>"
    # print(f'{value}    {result}')
    return result


def is_subtract(diff):
    flag = False
    patterns = [
        "©",
        "®",
        "\“",
        "•",
        "[\u0F20-\u0F29]",
        "[a-zA-Z]",
        "\)",
        "\(",
        "@",
        "་+?",
        "\u0020+",
        "། །",
        "\d",
    ]
    for pattern in patterns:
        if re.search(pattern, diff):
            flag = True
    return flag


def is_note(diff):
    flag = True
    patterns = [
        "[\u2460-\u2469]",
        "[\u0F20-\u0F29]",
        "\)",
        "\(",
        "\d",
    ]
    for pattern in patterns:
        if re.search(pattern, diff):
            flag = False
    return flag


def reformat_footnote(text):
    """Replace edition name with their respective unique id and brings every footnote to newline.

    Args:
        text (str): google OCRed footnote with namsel footnote markers transfered.

    Returns:
        (str): reformatted footnote
    """
    editions = [
        ["«དགེ»", "«d»"],
        ["«གཡུང་»", "«y»"],
        ["«ལི་»", "«j»"],
        ["«པེ་»", "«q»"],
        ["«སྣར་»", "«n»"],
        ["«ཅོ་»", "«c»"],
        ["«ཁུ་»", "«u»"],
        ["«ཞོལ་»", "«h»"],
    ]
    text = text.replace("\n", "")
    text = text.replace("<", "\n<")
    for edition, edition_id in editions:
        text = text.replace(edition, edition_id)
    return text


def apply_diff_durchen(diffs):
    result = ""
    for diff in diffs:
        if diff[0] == 0:
            pg = diff_cleaner(diff[1])
            pg_ann = re.search("[^\u0F20-\u0F29]\d+", pg)
            if pg_ann:
                if pg_ann[0] == "74":
                    result += f"<{pg_ann[0]}-"
                else:
                    result = f"{result[:-3]}{pg_ann[0]},74-{pg_ann[0]}>"
            else:
                result += diff[1]
        elif diff[0] == -1:
            if is_subtract(diff[1]):
                continue
            # remove noise from diff
            result += diff[1]
        else:
            if is_note(diff[1]):
                continue
            result += get_addition_dur(diff[1])
    result = reformat_durchen(result)
    result = add_link(result)
    return result


def flow(target_path, source_path, text_type, image_offset):
    """
    Input: target text, source text, text_type(body text or footnote) and source image offset
    Process: Diff is computed between target and source text; footnotes and footnotes markers
             are from diffs; they are applied to target text with markers; source image links
             are computed and added at the end of each page.
    Output: target text with footnotes with markers and source image links.
    """
    target = Path(target_path).read_text()
    source = Path(source_path).read_text()

    # The volume number info is extracted from the target_path and being used to name the
    # output file.
    vol_num = re.search("\d+", target_path)[0][1:]
    # Text_type can be either body of the text or footnote footnote.
    if text_type == "body":
        diffs = get_diff(target, source)
        result = apply_diff_body(diffs, vol_num)
        result = add_link(result, image_offset)
        with open(f"./output/body_text/{vol_num}.txt", "w+") as f:
            f.write(result)
    elif text_type == "footnote":
        clean_target, clean_source = preprocess_footnote(target, source)
        diffs = get_diff(clean_target, clean_source)
        result = apply_diff_footnote(diffs)
        with open(f"./footnote/footnote_{vol_num}.txt", "w+") as f:
            f.write(result)
    else:
        print("Type not found")
    print("Done")


if __name__ == "__main__":
    target_path = "./input/body_text/cleantext/v073.txt"
    source_path = "./input/body_text/ocred_text/v073.txt"
    offset = 16
    text_type = "body"
    flow(target_path, source_path, text_type, offset)
