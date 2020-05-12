"""
Pedurma Footnote Reconstruction
Footnote reconstruction script for the ocred katen pedurma using annotation transfer with 
google's dmp.(https://github.com/google/diff-match-patch) 
This script allows to transfer a specific set of annotations(footnotes and footnote markers) 
from text A(OCRed etext) to text B(clean etext). We first compute a diff between  texts 
A and B, then filter the annotations(dmp diffs) we want to transfer and then apply them to 
text B.
"""
import re
from pathlib import Path
import yaml
from diff_match_patch import diff_match_patch


def preprocess_footnote(B, A):
    """
    Normalises edition markers to minimise noise in diffs.

    Input: B text and A text
    Process: normalise the edition markers in the footnote
    Output: B text and A text with same edition markers
    """
    patterns = [["〈〈?", "«"], ["〉〉?", "»"], ["《", "«"], ["》", "»"]]
    clean_B = B
    clean_A = A
    for pattern in patterns:
        clean_B = re.sub(pattern[0], pattern[1], clean_B)
        clean_A = re.sub(pattern[0], pattern[1], clean_A)
    return clean_B, clean_A


def get_diff(B, A):
    """
    Input: B and A text (str)
    Process: computes diff of input texts using DMP.
    Output: returns list of cleaned diffs.
    """
    dmp = diff_match_patch()
    # Diff_timeout is set to 0 inorder to compute diff till end of file.
    dmp.Diff_Timeout = 0
    diffs = dmp.diff_main(B, A)
    # beautifies the diff list
    # dmp.diff_cleanupSemantic(diffs)
    print("Diff computation done.")
    return diffs


def rm_noise(diff):
    """
    Filters out noise in diff.

    Input: diff text
    Process: removes noise
    Output: footnote or footnote marker
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
    """
    Input: diff and volume number
    Process: 
        - from diff, page number pattern will be extracted
        -  page number will be then extraccted from the pattern
        - pg_annotation will be added and returned
    Output: page annotation <<pg_no,pg_pattern>>
    """
    pg_no_pattern = f"{vol_num}\S*?(\d+)"
    pg_pat = re.search(pg_no_pattern, diff)
    pg_num = pg_pat.group(1)
    return f"<<{pg_num},{pg_pat[0]}>>"


def get_noisy_lone_marker(left_diff, diff, right_diff):
    if is_punct(left_diff[-1]) == False and (right_diff[0] == "་"):
        if marker := get_abs_marker(diff):
            return marker
        elif marker := get_excep_marker(diff):
            return marker
        else:
            return ""
    else:
        return ""


def get_abs_marker(diff):
    """
    Input: diff
    Process: extract footnote marker from diff
    Output: fotenote marker
    """
    marker_ = ""
    patterns = [
        "[\u2460-\u2469]",
        "[\u0F20-\u0F29]+",
        "[\u0030-\u0039]+",
    ]
    for pattern in patterns:
        if marker := re.search(pattern, diff):
            marker_ += marker[0]
    return marker_


def get_excep_marker(diff):
    """Check is diff belong to exception marker or not if so returns it.

    Args:
        diff (str): diff text

    Returns:
        str: exception marker
    """
    marker_ = ""
    patterns = ["པོ་", "འི", "ཚོ་", "ད", "སུ", "རིན", "\(", "\)"]
    for pattern in patterns:
        marker = re.search(pattern, diff)
        if marker := re.search(pattern, diff):
            marker_ += marker[0]
    return marker_


def is_punct(char):
    """Check whether char is tibetan punctuation or not.

    Args:
        diff (str): character from diff

    Returns:
        flag: true if char is punctuation false if not
    """
    if char in ["་", "།", "༔", ":", "། །"]:
        return True
    else:
        return False


def is_midsyl(left_diff, right_diff):
    """Check whether current diff is mid syllabus or not.

    Args:
        left_diff (str): left diff text
        right_diff (str): right diff text

    Returns:
        str: flag to indicate whether current diff is mid syllabus or not
    """
    flag = True
    if is_punct(left_diff[-1]) and is_punct(right_diff[0]):
        flag = False
    return flag


def get_noisy_marker(diff):
    """Extarct marker from noisy marker.

    Args:
        diff (str): diff text

    Returns:
        str: marker
    """
    if marker := get_abs_marker(diff):
        return marker
    elif marker := get_excep_marker(diff):
        return marker
    else:
        return ""


def is_circle_number(footnote_marker):
    """
    Checks whether a footnote marker is number in circle or not, return if yes.

    Input: footnote marker
    Process: 
        - checks whether the footnote marker is number in circle or not
        - if so return number in circle.
    Output: number in circle 
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
    """
    Input: footnote marker
    Process: translate tibetan numerals to roman numbers and returns the result
    Output: numbers(roman)
    """
    value = ""
    if re.search("\d+\S+(\d+)", footnote_marker):
        return value
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


def get_value(footnote_marker):
    """
    Input: footnote_marker
    Process: equivalent number is computed from footnote marker and returned
    Output: equivalent numbers from footnote marker
    """
    value = ""
    if is_circle_number(footnote_marker):
        value = is_circle_number(footnote_marker)
        return value
    elif translate_tib_number(footnote_marker):
        value = translate_tib_number(footnote_marker)
        return value
    return value


def apply_diff_body(diffs, image_info):
    """
    Input: list of diffs
    Process: 
        - filter the diffs
        - add diff markers '<diff>'
        - apply filtered diffs to B text
    Output: B text with transfered annotations with markers.
    """
    vol_num = image_info[1]
    result = ""
    left_diff = [0, ""]
    # right_diff = [0, ""]
    for i, diff in enumerate(diffs):
        if diff[0] == 0 or diff[0] == 1:  # in B not in A
            result += diff[1]
        elif diff[0] == -1:  # in A not in B
            if diff[1] == "(༦)ཅི་(༧ད":
                print("here")
            if i > 0:
                left_diff = diffs[i - 1]
            if i < len(diffs) - 1:
                right_diff = diffs[i + 1]
            diff_ = rm_noise(diff[1])
            if re.search(f"{vol_num}་?\D་?\d+", diff_):
                result += get_pg_ann(diff_, vol_num)
                diff_ = re.sub(f"{vol_num}་?\D་?\d+", "", diff_)
            if left_diff[0] == 0 and right_diff[0] == 0:
                if marker := get_noisy_lone_marker(left_diff[1], diff_, right_diff[1]):
                    if value := get_value(marker):
                        result = f"{result[:-1]}<{value},{marker}>{left_diff[1][-1]}"
                    else:
                        result = f"{result[:-1]}<{marker}>{left_diff[1][-1]}"
                elif marker := get_abs_marker(diff_):
                    value = get_value(marker)
                    result += f"<{value},{marker}>"
                elif marker := get_excep_marker(diff_):
                    result += f"<{marker}>"
                # elif is_midsyl(left_diff[1], right_diff[1]):
                #     result += "cor"
            elif right_diff[0] == 1:
                # if is_midsyl(left_diff[1], right_diff[1]):
                #     result += "cor"
                if marker := get_noisy_marker(diff_):
                    if value := get_value(marker):
                        result += f"<{value},{marker}>"
                    else:
                        result += f"<{marker}>"

    return result


def add_link(text, image_info):
    result = ""

    work = image_info[0]
    vol = image_info[1]
    pref = f"I{work[1:-3]}"
    igroup = f"{pref}{783+vol}" if work == "W1PD96682" else f"{pref}{845+vol}"
    offset = image_info[2]

    lines = text.splitlines()
    for line in lines:
        # detect page numbers and convert to image url
        if re.search("<<\d+,\d+\S+\d+>>", line):
            pg_no = re.search("<<(\d+),(\d+\S+\d+)>>", line)
            if re.search("[\u0030-\u0039]", pg_no.group(2)):
                if len(pg_no.group(1)) > 3:
                    pg_no = int(pg_no.group(1)[:3]) + offset
                else:
                    pg_no = int(pg_no.group(1)) + offset
                link = f"[https://www.tbrc.org/browser/ImageService?work={work}&igroup={igroup}&image={pg_no}&first=1&last=2000&fetchimg=yes]"
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
    # needs revision
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
    Input:
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
    # TODO: needs revision
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


def filterDiffs(diffsYamlPath, type, image_info):
    """
    TODO:

    Create functions for each type of filtering rule.
    rules should edit the diff list and the 0/1/-1 values 

    """
    result = []
    vol_num = image_info[1]
    diffs = yaml.safe_load(diffsYamlPath.read_text(encoding="utf-8"))
    for i, diff in enumerate(diffs):
        if diff[0] == 0 or diff[0] == 1:  # in B not in A
            result.append([diff[0], diff[1], ""])
        elif diff[0] == -1:  # in A not in B
            if re.search(f"{vol_num}་?\D་?\d+", diff[1]):
                result.append([1, diff[1], "pedurma-pagination"])
            else:
                if i > 0:
                    left_diff = diffs[i - 1]
                if i < len(diffs) - 1:
                    right_diff = diffs[i + 1]
                diff_ = rm_noise(diff[1])
                if left_diff[0] == 0 and right_diff[0] == 0:
                    if marker := get_abs_marker(diff_):
                        result.append([1, diff[1], "marker"])
                    elif marker := get_excep_marker(diff_):
                        result.append([1, diff[1], "marker"])
                elif right_diff[0] == 1:
                    if marker := get_noisy_marker(diff_):
                        result.append([1, diff[1], "marker"])

    filterDiffs = result

    return filterDiffs


def flow(B_path, A_path, text_type, image_info):
    """
    Script flow

    Input: B text, A text, text_type(body text or footnote) and A image offset
    Process: 
        - diff is computed between B and A text
        - footnotes and footnotes markers are filtered from diffs
        - they are applied to B text with markers
        - A image links are computed and added at the end of each page
    Output: B text with footnotes, with markers and with A image links
    """
    B = B_path.read_text(encoding="utf-8")
    A = A_path.read_text(encoding="utf-8")

    # Text_type can be either body of the text or footnote footnote.
    if text_type == "body":
        print("Calculating diffs...")
        diffs = get_diff(B, A)
        diffsList = list(map(list, diffs))
        print("Dumping diffs...")
        diffsYaml = yaml.safe_dump(diffsList, allow_unicode=True)
        diffsYamlPath = basePath / "diffs.yaml"
        diffsYamlPath.write_text(diffsYaml, encoding="utf-8")
        filteredDiffs = filterDiffs(diffsYamlPath, "body")
        newText = apply_diff_body(diffs, image_info)
        newText = add_link(newText, image_info)
        # with open(f"./output/body_text/{vol_num}.txt", "w+") as f:
        #     f.write(result)
        (basePath / "result.txt").write_text(newText, encoding="utf-8")
    elif text_type == "footnote":
        clean_B, clean_A = preprocess_footnote(B, A)
        diffs = get_diff(clean_B, clean_A)
        result = apply_diff_footnote(diffs)
        with open(f"./footnote/footnote_{vol_num}.txt", "w+", encoding="utf-8") as f:
            f.write(result)
    else:
        print("Type not found")
    print("Done")


if __name__ == "__main__":

    # basePath = Path("./tests/test2")
    # A_path = basePath / "input" / "a.txt"
    # B_path = basePath / "input" / "b.txt"

    basePath = Path("./input/body_text")
    A_path = basePath / "input" / "83A.txt"
    B_path = basePath / "input" / "83B.txt"

    # only works text by text or note by note for now
    # TODO: run on whole volumes/instances by parsing the BDRC outlines to find and identify text type and get the image locations
    image_info = [
        "W1PD96682",
        73,
        21,
    ]  # [<kangyur: W1PD96682/tengyur: W1PD95844>, <volume>, <offset>]

    text_type = "body"

    flow(B_path, A_path, text_type, image_info)
