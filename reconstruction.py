"""
Pedurma Footnote Reconstruction
Footnote reconstruction script for the ocred katen pedurma using annotation transfer with 
google's dmp.(https://github.com/google/diff-match-patch) 
This script allows to transfer a specific set of annotations(footnotes and footnote markers) 
from text A(OCRed etext) to text B(clean etext). We first compute a diff between  texts 
A and B, then filter the annotations(dmp diffs) we want to transfer and then apply them to 
text B.

Tibetan alphabet:
- 


"""
import re
import unicodedata
from pathlib import Path
from functools import partial
import yaml
from diff_match_patch import diff_match_patch


def preprocess_footnote(B, A):
    """Normalises edition markers to minimise noise in diffs.
    Args:
        target (str): Target text
        source (str): source text
    Returns:
        str: normalised target text
        str: normalised source text
    """
    patterns = [["〈〈?", "«"], ["〉〉?", "»"], ["《", "«"], ["》", "»"]]
    clean_B = B
    clean_A = A
    for pattern in patterns:
        clean_B = re.sub(pattern[0], pattern[1], clean_B)
        clean_A = re.sub(pattern[0], pattern[1], clean_A)
    return clean_B, clean_A


def get_diff(B, A):
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
    diffs = dmp.diff_main(B, A)
    # beautifies the diff list
    # dmp.diff_cleanupSemantic(diffs)
    print("Diff computation done.")
    return diffs


def to_yaml(list_, base_path, type_=None):
    """Dump list to yaml and write the yaml to a file on mentioned path.

    Args:
        list_ (list): list
        base_path (path): base path object
        type_ (str, optional): type of list you want to dump as yaml. Defaults to None.
    """
    print(f"Dumping {type_}...")
    list_yaml = yaml.safe_dump(list_, allow_unicode=True)
    list_yaml_path = base_path / f"{type_}.yaml"
    list_yaml_path.write_text(list_yaml, encoding="utf-8")
    print(f'{type_} Yaml saved...')


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
        " +",
        "།",
    ]
    for pattern in patterns:
        noise = re.search(pattern, diff)
        if noise:
            result = result.replace(noise[0], "")
    return result


def rm_markers_ann(text):
    """Remove page annotation and replace footnotemarker with #.

    Args:
        text (str): diff applied text

    Returns:
        str: diff applied text without page annotation and replaced footnotemarker with #
    """
    result = ""
    lines = text.splitlines()
    for line in lines:
        line = re.sub("<<.+?>>", "", line)
        line = re.sub("<.+?>", "#", line)
        result += line + "\n"
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


def get_abs_marker(diff):
    """Extract absolute footnote marker from diff text.

    Args:
        diff (str): diff text

    Returns:
        str: footnote marker
    """
    marker_ = ""
    patterns = [
        "[①-⑳]",
        "[༠-༩]+",
        "[0-9]+",
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


def isvowel(char):
    """Check whether char is tibetan vowel or not.

    Args:
        char (str): char to be checked

    Returns:
        boolean: true for vowel and false for otherwise
    """
    flag = False
    vowels = ["\u0F74", "\u0F72", "\u0F7A", "\u0F7C"]
    for pattern in vowels:
        if re.search(pattern, char):
            flag = True
    return flag


def is_midsyl(left_diff, right_diff):
    """Check if current diff is mid syllabus.

    Args:
        left_diff (str): left diff text
        right_diff (str): right diff text

    Returns:
        boolean : True if it is mid syllabus else False
    """
    if not is_punct(left_diff[-1]) and not is_punct(right_diff[0]):
        return True
    return False


def handle_mid_syl(result, diffs, left_diff, i, diff, right_diff):
    """Handle the middle of syllabus diff text in different situation.

    Args:
        result (list): Filtered diff list
        diffs (list): Unfilterd diff list
        left_diff (list): left diff type and text from current diff
        diff (list): current diff type and text
        i (int): current diff index
        right_diff (list): right diff type and text from current diff
    """
    if left_diff[1][-1] == " ":
        lasttwo = left_diff[1][-2:]
        result[-1][1] = result[-1][1][:-2]
        result.append([1, diff[1], "marker"])
        diffs[i + 1][1] = lasttwo + diffs[i + 1][1]
    elif right_diff[1][0] == " ":
        result.append([1, diff[1], "marker"])
    else:
        if isvowel(right_diff[1][0]):
            result[-1][1] += right_diff[1][0]
            result.append([1, diff[1], "marker"])
            diffs[i + 1][1] = diffs[i + 1][1][1:]
        else:
            lastsyl = left_diff[1].split("་")[-1]
            result[-1][1] = result[-1][1][: -len(lastsyl)]
            result.append([1, diff[1], "marker"])
            diffs[i + 1][1] = lastsyl + diffs[i + 1][1]


def tseg_shifter(result, diffs, left_diff, i, right_diff):
    """Shift tseg if right diff starts with one and left diff ends with non punct.

    Args:
        result (list): filtered diff
        diffs (list): unfiltered diffs
        left_diff (list): contains left diff type and text
        i (int): current index if diff in diffs
        right_diff (list): contains right diff type and text
    """
    if right_diff[1][0] == "་" and not is_punct(left_diff[1]):
        result[-1][1] += "་"
        diffs[i + 1][1] = diffs[i + 1][1][1:]


def get_marker(diff):
    """Extarct marker from diff text.

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
    """Check whether footnote marker is number in circle or not and if so 
       returns equivalent number.
    Args:
        footnote_marker (str): footnote marker
    Returns:
        str: number inside the circle
    """
    value = ""
    number = re.search("[①-⑳]", footnote_marker)
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
            "⑪": "11",
            "⑫": "12",
            "⑬": "13",
            "⑭": "14",
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
            if re.search("[༠-༩]", number[0]):
                value += tib_num.get(number[0])
            else:
                value += number[0]
    return value


def get_value(footnote_marker):
    """Compute the equivalent numbers in footnote marker payload and return it.
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


def format_diff(diffs, image_info):
    """Format list of diff on target text.
    Args:
        diffs (list): list of diffs
        image_info (list): contains work_id, volume number and image source offset
    Returns:
        str: target text with transfered annotations with markers.
    """
    vol_num = image_info[1]
    result = ""
    for diff_type, diff_text, diff_tag in diffs:
        if diff_type == 0:
            result += diff_text
        else:
            if diff_tag:
                if diff_tag == "pedurma-pagination":
                    result += get_pg_ann(diff_text, vol_num)
                elif diff_tag == "marker":
                    if marker := get_abs_marker(diff_text):
                        value = get_value(marker)
                        result += f"<{value},{marker}>"
                    elif marker := get_excep_marker(diff_text):
                        result += f"<{marker}>"
                elif diff_tag == 'cat-marker':
                    result += f'({diff_text})'
            else:
                result += diff_text

    return result


def add_link(text, image_info):
    """Add link of source image page.
    Args:
        text (str): target text having footnote maker transfered
        image_info (list): contains work_id, volume number and image source offset
    Returns:
        str: target text with source image page link
    """
    
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
            if re.search("[0-9]", pg_no.group(2)):
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
    patterns = ["[①-⑩]", "[༠-༩]+", "\)", "\(", "\d+", "\d+\S+\d+"]
    for pattern in patterns:
        ann = re.search(pattern, value)
        if ann:
            ann_ = ann[0]
    if ann_:
        addition = rm_noise(ann_)
        pay_load = get_payload(addition)
        result = re.sub(ann_, f"<{pay_load},{ann_}>", value, 1)
        cir_num = re.search("(>|་)[①-⑩]", result)
        if cir_num:
            cpl = get_payload(cir_num[0][1:])
            result = re.sub("[①-⑩]", f"<{cpl},{cir_num[0][1:]}>", result, 1)
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
        "[༠-༩]",
        "[a-zA-Z]",
        "\)",
        "\(",
        "@",
        "་+?",
        " +",
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
        "[①-⑩]",
        "[༠-༩]",
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
    # TODO: needs revision
    result = ""
    for diff in diffs:
        if diff[0] == 0:
            pg = diff_cleaner(diff[1])
            pg_ann = re.search("[^༠-༩]\d+", pg)
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


def filter_diffs(diffs_list, type, image_info):
    """Filter diff of text A and text B.

    Args:
        diffs_list (list): list of diffs
        type (str): type of text
        image_info (list): contains work_id, volume number and source image offset.

    Returns:
        list: filtered diff
    """
    result = []
    vol_num = image_info[1]
    diffs = diffs_list
    for i, diff in enumerate(diffs):
        if diff[0] == 0 or diff[0] == 1:  # in B not in A
            result.append([diff[0], diff[1], ""])
        elif diff[0] == -1:  # in A not in B
            if re.search(f"{vol_num}་?\D་?\d+", diff[1]): # checking diff text is pg_ann or not
                result.append([1, diff[1], "pedurma-pagination"])
            else:
                if i > 0: # extracting left context of current diff
                    left_diff = diffs[i - 1]
                if i < len(diffs) - 1: # extracting right context of current diff
                    right_diff = diffs[i + 1]
                diff_ = rm_noise(diff[1]) # removes unwanted new line, space and punct
                if left_diff[0] == 0 and right_diff[0] == 0:
                    # checks if current diff text is located in middle of a syllebus
                    if is_midsyl(left_diff[1], right_diff[1]): 
                        handle_mid_syl(result, diffs, left_diff, i, diff, right_diff)
                    # checks if current diff text contains absolute marker or not
                    elif get_marker(diff_):
                        # Since cur diff is not mid syl, hence if any right diff starts with tseg will 
                        # be shift to left last as there are no marker before tseg.
                        tseg_shifter(result, diffs, left_diff, i, right_diff)
                        result.append([1, diff[1], "marker"])
                    # Since diff type of -1 is from namsel and till now we are not able to detect
                    # marker from cur diff, we will consider it as canditate marker.
                    elif diff_:
                        tseg_shifter(result, diffs, left_diff, i, right_diff)
                        result.append([1, diff[1], "cat-marker"])
                elif right_diff[0] == 1:
                    # Check if current diff is located in middle of syllabus or not.
                    if is_midsyl(left_diff[1], right_diff[1]):
                        handle_mid_syl(result, diffs, left_diff, i, diff, right_diff)
                    elif get_marker(diff_):
                        # Since cur diff is not mid syl, hence if any right diff starts with tseg will 
                        # be shift to left last as there are no marker before tseg.
                        tseg_shifter(result, diffs, left_diff, i, right_diff)
                        result.append([1, diff[1], "marker"])

    filter_diffs = result

    return filter_diffs


def flow(B_path, A_path, text_type, image_info):
    """ - diff is computed between B and A text
        - footnotes and footnotes markers are filtered from diffs
        - they are applied to B text with markers
        - A image links are computed and added at the end of each page

    Args:
        B_path (path): path of text B (namsel)
        A_path (path): path of text A (clean)
        text_type (str): type of text can be either body or footnote
        image_info (list): Contains work_id, volume number and source image offset
    """
    B = B_path.read_text(encoding="utf-8")
    A = A_path.read_text(encoding="utf-8")
    diffs_to_yaml = partial(to_yaml, type_ = 'diffs') # customising to_yaml function for diff list
    filtered_diffs_to_yaml = partial(to_yaml, type_ = 'filtered_diffs') # customising to_yaml function for filtered diffs list

    # Text_type can be either body of the text or footnote footnote.
    if text_type == "body":
        print("Calculating diffs...")
        diffs = get_diff(B, A)
        diffs_list = list(map(list, diffs))
        diffs_to_yaml(diffs_list, base_path)
        filtered_diffs = filter_diffs(diffs_list, "body", image_info)
        filtered_diffs_to_yaml(filtered_diffs, base_path)
        new_text = format_diff(filtered_diffs, image_info)
        #new_text = add_link(new_text, image_info)
        new_text = rm_markers_ann(new_text)
        (base_path / "result.txt").write_text(new_text, encoding="utf-8")
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

    base_path = Path("./tests/test2")
    A_path = base_path / "input" / "a.txt"
    B_path = base_path / "input" / "b.txt"

    # base_path = Path("./input/body_text")
    # A_path = base_path / "input" / "83A.txt"
    # B_path = base_path / "input" / "83B.txt"

    # base_path = Path("./input/body_text")
    # A_path = base_path / "cleantext" / "$.txt"
    # B_path = base_path / "ocred_text" / "v073.txt"

    # only works text by text or note by note for now
    # TODO: run on whole volumes/instances by parsing the BDRC outlines to find and identify text type and get the image locations
    image_info = [
        "W1PD96682",
        74,
        18,
    ]  # [<kangyur: W1PD96682/tengyur: W1PD95844>, <volume>, <offset>]

    text_type = "body"

    flow(B_path, A_path, text_type, image_info)
