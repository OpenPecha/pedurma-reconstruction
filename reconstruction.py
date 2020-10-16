# coding='utf-8'

"""
Pedurma footnotes Reconstruction
footnotes reconstruction script for the ocred katen pedurma using annotation transfer with 
google's dmp.(https://github.com/google/diff-match-patch) 
This script allows to transfer a specific set of annotations(footnotes and footnotes markers) 
from text A(OCRed etext) to text B(clean etext). We first compute a diff between  texts 
A and B, then filter the annotations(dmp diffs) we want to transfer and then apply them to 
text B.
"""
import re
from itertools import zip_longest
import unicodedata
from pathlib import Path
from functools import partial
import yaml
from diff_match_patch import diff_match_patch
from preprocess import preprocess_google_notes, preprocess_namsel_notes
from utils import optimized_diff_match_patch
from antx import transfer
from horology import timed
from collections import defaultdict


# @timed(unit="min")
def preprocess_footnotes(B, A):
    """Normalise edition markers to minimise noise in diffs.

    Args:
        target (str): Target text
        source (str): source text
    Returns:
        str: normalised target text
        str: normalised source text
    """
    patterns = [["〈〈?", "«"], ["〉〉?", "»"], ["《", "«"], ["》", "»"]]
    clean_namsel_text = B
    clean_google_text = A
    for pattern in patterns:
        clean_namsel_text = re.sub(pattern[0], pattern[1], clean_namsel_text)
        clean_google_text = re.sub(pattern[0], pattern[1], clean_google_text)
    return clean_namsel_text, clean_google_text


# @timed(unit="min")
def rm_google_ocr_header(text):
    """Remove header of google ocr.

    Args:
        text (str): google ocr

    Returns:
        str: header removed
    """
    header_pattern = "\n\n\n\n{1,18}.+\n(.{1,30}\n)?(.{1,15}\n)?(.{1,15}\n)?(.{1,15}\n)?"
    result = re.sub(header_pattern, "\n\n\n", text)
    return result


@timed(unit="min")
def get_diffs(text1, text2, optimized=True):
    """Compute diff between source and target with DMP.

    Args:
        source (str): source text
        target (str): target text
        optimized (bool): whether to use optimized dmp with node.
    Returns:
        list: list of diffs
    """
    print("[INFO] Computing diffs ...")
    if optimized:
        dmp = optimized_diff_match_patch()
    else:
        dmp = diff_match_patch()
        dmp.Diff_Timeout = 0  # compute diff till end of file
    diffs = dmp.diff_main(text1, text2)
    print("[INFO] Diff computed!")
    return diffs


# @timed(unit="min")
def to_yaml(list_, vol_path, type_=None):
    """Dump list to yaml and write the yaml to a file on mentioned path.

    Args:
        list_ (list): list
        vol_path (path): base path object
        type_ (str, optional): type of list you want to dump as yaml. Defaults to None.
    """
    print(f"Dumping {type_}...")
    list_yaml = yaml.safe_dump(list_, allow_unicode=True)
    list_yaml_path = vol_path / f"{type_}.yaml"
    list_yaml_path.write_text(list_yaml, encoding="utf-8")
    print(f"{type_} Yaml saved...")


# @timed(unit="min")
def from_yaml(path):
    """Load yaml to list

    Args:
        path (path): path object
    Returns:
        list: list inside the yaml 
    """
    diffs = yaml.safe_load(path.read_text(encoding="utf-8"))
    diffs_list = list(diffs)
    return diffs_list


# HACK is that useful?
# @timed(unit="min")
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
        "\u0020+",
        "་+?",
    ]
    for pattern in patterns:
        noise = re.search(pattern, diff)
        if noise:
            result = result.replace(noise[0], "")
    return result


# @timed(unit="min")
def rm_markers_ann(text):
    """Remove page annotation and replace footnotesmarker with #.

    Args:
        text (str): diff applied text

    Returns:
        str: diff applied text without page annotation and replaced footnotesmarker with #
    """
    result = ""
    lines = text.splitlines()
    for line in lines:
        line = re.sub("<p.+?>", "", line)
        line = re.sub("<.+?>", "#", line)
        result += line + "\n"
    return result


# @timed(unit="min")
def get_pg_ann(diff, vol_num):
    """Extract pedurma page and put page annotation.

    Args:
        diff (str): diff text
        vol_num (int): volume number

    Returns:
        str: page annotation
    """
    pg_no_pattern = f"{vol_num}\S*?(\d+)"
    pg_pat = re.search(pg_no_pattern, diff)
    pg_num = pg_pat.group(1)
    return f"<p{vol_num}-{pg_num}>"


# @timed(unit="min")
def get_abs_marker(diff):
    """Extract absolute footnotes marker from diff text.

    Args:
        diff (str): diff text

    Returns:
        str: footnotes marker
    """
    marker_ = ""
    patterns = [
        "[①-⓪]+",
        "[༠-༩]+",
        "[0-9]+",
    ]
    for pattern in patterns:
        if re.search(pattern, diff):
            marker = re.search(pattern, diff)
            marker_ += marker[0]
    return marker_


# @timed(unit="min")
def get_excep_marker(diff):
    """Check is diff belong to exception marker or not if so returns it.

    Args:
        diff (str): diff text

    Returns:
        str: exception marker
    """
    marker_ = ""
    patterns = ["<m(.+?)>", "(.*#.*)"]
    for pattern in patterns:
        marker = re.search(pattern, diff)
        if re.search(pattern, diff):
            marker = re.search(pattern, diff)
            marker_ = marker.group(1)
    return marker_


# @timed(unit="min")
def is_punct(char):
    """Check whether char is tibetan punctuation or not.

    Args:
        diff (str): character from diff

    Returns:
        flag: true if char is punctuation false if not
    """
    if char in ["་", "།", "༔", ":", "། །", "༄", "༅"]:
        return True
    else:
        return False


# @timed(unit="min")
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


# @timed(unit="min")
def is_midsyl(left_diff, right_diff):
    """Check if current diff is mid syllabus.

    Args:
        left_diff (str): left diff text
        right_diff (str): right diff text

    Returns:
        boolean : True if it is mid syllabus else False
    """
    if left_diff:
        right_diff_text = right_diff.replace("\n", "")
        left_diff_text = left_diff.replace("\n", "")
        if not right_diff_text or not left_diff_text:
            return False
        if (is_punct(left_diff_text[-1]) == False) and (is_punct(right_diff_text[0]) == False):
            return True
    return False


# @timed(unit="min")
def double_mid_syl_marker(result):
    """Handle the consecutive marker occurance in body text.

    Args:
        result (list): filtered diffs

    Returns:
        Boolean: True if double consecutive marker detected in case of mid syl esle false
    """
    i = -1
    while not is_punct(result[i][1]):
        if result[i][2] == "marker":
            return False
        else:
            i -= 1
    return True


# @timed(unit="min")
def handle_mid_syl(result, diffs, left_diff, i, diff, right_diff_text, marker_type=None):
    """Handle the middle of syllabus diff text in different situation.

    Args:
        result (list): Filtered diff list
        diffs (list): Unfilterd diff list
        left_diff (list): left diff type and text from current diff
        diff (list): current diff type and text
        i (int): current diff index
        right_diff (list): right diff type and text from current diff
        marker_type (str): marker type can be marker or candidate marker
    """
    # make it marker if marker found  (revision)
    if double_mid_syl_marker(result):
        diff_ = rm_noise(diff[1])
        if left_diff[1][-1] == " ":
            lasttwo = left_diff[1][-2:]
            result[-1][1] = result[-1][1][:-2]
            result.append([1, diff_, f"{marker_type}"])
            diffs[i + 1][1] = lasttwo + diffs[i + 1][1]
        elif right_diff_text[0] == " ":
            result.append([1, diff_, f"{marker_type}"])
        elif isvowel(left_diff[1][-1]):
            syls = re.split("(་|།)", right_diff_text)
            first_syl = syls[0]
            result[-1][1] += first_syl
            diffs[i + 1][1] = diffs[i + 1][1][len(first_syl) :]
            result.append([1, diff_, f"{marker_type}"])
        else:
            if isvowel(right_diff_text[0]):
                syls = re.split("(་|།)", right_diff_text)
                first_syl = syls[0]
                result[-1][1] += first_syl
                diffs[i + 1][1] = diffs[i + 1][1][len(first_syl) :]
                result.append([1, diff_, f"{marker_type}"])
            else:
                if left_diff[0] != (0 or 1):
                    lastsyl = left_diff[1].split("་")[-1]
                    result[-1][1] = result[-1][1][: -len(lastsyl)]
                    result.append([1, diff_, f"{marker_type}"])
                    diffs[i + 1][1] = lastsyl + diffs[i + 1][1]


# @timed(unit="min")
def tseg_shifter(result, diffs, left_diff_text, i, right_diff_text):
    """Shift tseg if right diff starts with one and left diff ends with non punct.

    Args:
        result (list): filtered diff
        diffs (list): unfiltered diffs
        left_diff (list): contains left diff type and text
        i (int): current index if diff in diffs
        right_diff (list): contains right diff type and text
    """
    if right_diff_text[0] == "་" and not is_punct(left_diff_text):
        result[-1][1] += "་"
        diffs[i + 1][1] = diffs[i + 1][1][1:]


# @timed(unit="min")
def get_marker(diff):
    """Extarct marker from diff text.

    Args:
        diff (str): diff text

    Returns:
        str: marker
    """
    if get_abs_marker(diff):
        marker = get_abs_marker(diff)
        return marker
    elif get_excep_marker(diff):
        marker = get_excep_marker(diff)
        return marker
    else:
        return ""


# @timed(unit="min")
def is_circle_number(footnotes_marker):
    """Check whether footnotes marker is number in circle or not and if so 
       returns equivalent number.

    Args:
        footnotes_marker (str): footnotes marker
    Returns:
        str: number inside the circle
    """
    value = ""
    number = re.search("[①-⓪]", footnotes_marker)
    if number:
        circle_num = {
            "⓪": "0",
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
            "⑮": "15",
            "⑯": "16",
            "⑰": "17",
            "⑱": "18",
            "⑲": "19",
            "⑳": "20",
        }
        value = circle_num.get(number[0])
    return value


# @timed(unit="min")
def translate_tib_number(footnotes_marker):
    """Translate tibetan numeral in footnotes marker to roman number.

    Args:
        footnotes_marker (str): footnotes marker
    Returns:
        str: footnotes marker having numbers in roman numeral
    """
    value = ""
    if re.search("\d+\S+(\d+)", footnotes_marker):
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
    numbers = re.finditer("\d", footnotes_marker)
    if numbers:
        for number in numbers:
            if re.search("[༠-༩]", number[0]):
                value += tib_num.get(number[0])
            else:
                value += number[0]
    return value


# @timed(unit="min")
def get_value(footnotes_marker):
    """Compute the equivalent numbers in footnotes marker payload and return it.

    Args:
        footnotes_marker (str): footnotes marker
    Returns:
        str: numbers in footnotes marker
    """
    value = ""
    if is_circle_number(footnotes_marker):
        value = is_circle_number(footnotes_marker)
        return value
    elif translate_tib_number(footnotes_marker):
        value = translate_tib_number(footnotes_marker)
        return value
    return value


# @timed(unit="min")
def format_diff(filter_diffs_yaml_path, image_info, type_=None):
    """Format list of diff on target text.

    Args:
        diffs (list): list of diffs
        image_info (list): contains work_id, volume number and image source offset
        type_ (str): diff type can be footnotes or body
    Returns:
        str: target text with transfered annotations with markers.
    """
    diffs = from_yaml(filter_diffs_yaml_path)
    vol_num = image_info[1]
    result = ""
    for diff_type, diff_text, diff_tag in diffs:
        if diff_type == 1 or diff_type == 0:
            if diff_tag:
                if diff_tag == "pedurma-page":
                    result += get_pg_ann(diff_text, vol_num)
                if diff_tag == "marker":
                    if get_abs_marker(diff_text):
                        marker = get_abs_marker(diff_text)
                        value = get_value(marker)
                        result += f"<{value},{marker}>"
                    elif get_excep_marker(diff_text):
                        marker = get_excep_marker(diff_text)
                        result += f"<{marker}>"
                    else:
                        result += f"<{diff_text}>"
                elif diff_tag == "pg_ref":
                    result += diff_text
            else:
                result += diff_text

    return result


# @timed(unit="min")
def reformatting_body(text):
    """Reformat marker annotation using pedurma page.

    Args:
        text (str): unformatted text

    Returns:
        str: formatted text
    """
    result = ""
    page_anns = re.findall("<p\S+?>", text)
    pages = re.split("<p\S+?>", text)
    for page, ann in zip_longest(pages, page_anns, fillvalue=""):
        markers = re.finditer("<.+?>", page)
        for i, marker in enumerate(markers, 1):
            repl = f"<{i},{marker[0][1:-1]}>"
            page = page.replace(marker[0], repl, 1)
        result += page + ann
    return result


def get_page_link(text, image_info, pg_pat):
    work = image_info[0]
    vol = image_info[1]
    pref = f"I{work[1:-3]}"
    igroup = f"{pref}{783+vol}" if work == "W1PD96682" else f"{pref}{845+vol}"
    offset = image_info[2]
    if re.search(pg_pat, text):
        pg_no = re.search(pg_pat, text)
        if len(pg_no.group(1)) > 3:
            pg_num = int(pg_no.group(1)[:3]) + offset
        else:
            pg_num = int(pg_no.group(1)) + offset
        link = f"[https://www.tbrc.org/browser/ImageService?work={work}&igroup={igroup}&image={pg_num}&first=1&last=2000&fetchimg=yes]"
    return link


# @timed(unit="min")
def add_link(text, image_info):
    """Add link of source image page.

    Args:
        text (str): target text having footnotes maker transfered
        image_info (list): contains work_id, volume number and image source offset
    Returns:
        str: target text with source image page link
    """
    result = ""
    pg_pats = {"body_pg": r"<p\d+-(\d+)>", "durchen_pg": r"<dp(\d+)>"}
    lines = text.splitlines()
    for line in lines:
        # detect page numbers and convert to image url
        if re.search(pg_pats["body_pg"], line):
            links = ""
            for type, pg_pat in pg_pats.items():
                link = get_page_link(line, image_info, pg_pat)
                links += f"\n{type}: {link}"
            line += links
        result += line + "\n"
    return result


# @timed(unit="min")
def get_page(diff, cur_loc, diffs, vol_num):
    """Extract pedurma page from diffs.

    Args:
        diff (str): diff text
        cur_loc (int): current diff location in diff list
        diffs (list): diff list
        vol_num (int): volume number

    Returns:
        str: pedurma page
    """
    page = ""
    step = 0
    if diff == str(vol_num):
        for walker in diffs[cur_loc + 1 :]:
            if walker[0] == 0:
                break
            step += 1
        page += f"{diff}—{walker[1]}"
        del diffs[cur_loc + 1 : cur_loc + 2 + step]
    return page


# @timed(unit="min")
def rm_marker(diff):
    """Remove marker of google ocr text.

    Args:
        diff (str): diff text

    Returns:
        str: diff text without footnotes marker of google ocr
    """
    result = diff
    patterns = [
        "©",
        "®",
        "\“",
        "•",
        "[༠-༩]",
        "[a-zA-Z]",
        "\)",
        "\(",
        "\u0020+",
        "@",
        "་+?",
        "། །",
        "\d",
        "།",
        "༄༅",
    ]
    for pattern in patterns:
        if re.search(pattern, diff):
            result = re.sub(pattern, "", result)
    return result


# @timed(unit="min")
def is_note(diff):
    """Check if diff text is note or marker.

    Args:
        diff (str): diff text

    Returns:
        boolean: True if diff text is note else False.
    """
    flag = True
    patterns = ["[①-⑳]", "[༠-༩]", "\)", "\(", "\d", "⓪"]
    for pattern in patterns:
        if re.search(pattern, diff):
            flag = False
    return flag


# @timed(unit="min")
def parse_pg_ref_diff(diff, result):
    """Parse page ref and marker if both exist in one diff.

    Args:
        diff (str): diff text
        result (list): filtered diff
    """
    lines = diff.splitlines()
    for line in lines:
        if line:
            if re.search("<r.+?>", line):
                result.append([1, line, "page_ref"])
            elif re.search("(<m.+?>)(.+)", line):
                marker = re.search("(<m.+?>)(.+)", line)
                result.append([1, marker.group(1), "marker"])
                result.append([1, marker.group(2), ""])
            elif re.search("<m.+?>", line):
                marker = re.search("<m.+?>", line)
                result.append([1, marker[0], "marker"])


# @timed(unit="min")
def double_marker_handler(result):
    if len(result) > 3:
        prev2 = result[-3]
        prev1 = result[-2]
        cur = result[-1]
        if cur[2] == "marker":
            if prev2[2] == "marker" and prev1[1] in ["\n", " ", "", "།"]:
                del result[-1]
    else:
        pass


# @timed(unit="min")
def reformat_footnotes(text):
    """Replace edition name with their respective unique id and brings every footnotes to newline.
    
    Args:
        text (str): google OCRed footnotes with namsel footnotes markers transfered.
    Returns:
        (str): reformatted footnote
    """
    text = text.replace("\n", "")
    text = re.sub("(<+)", r"\n\1", text)
    result = demultiply_diffs(text)

    editions = [
        ["«སྡེ་»", "«d»"],
        ["«གཡུང་»", "«y»"],
        ["«གཡུང»", "«y»"],
        ["«ལི་»", "«j»"],
        ["«པེ་»", "«q»"],
        ["«སྣར་»", "«n»"],
        ["«ཅོ་»", "«c»"],
        ["«ཁུ་»", "«u»"],
        ["«ཞོལ་»", "«h»"],
    ]
    # for edition, edition_id in editions:
    #     text = text.replace(edition, edition_id)

    return result


# @timed(unit="min")
def filter_diffs(diffs_yaml_path, type, image_info):
    """Filter diff of text A and text B.

    Args:
        diffs_list (list): list of diffs
        type (str): type of text
        image_info (list): contains work_id, volume number and source image offset.

    Returns:
        list: filtered diff
    """
    left_diff = [0, ""]
    result = []
    vol_num = image_info[1]
    diffs = from_yaml(diffs_yaml_path)
    for i, diff in enumerate(diffs):
        diff_type, diff_text = diff
        if diff_type == 0:  # in both
            result.append([diff_type, diff_text, ""])

        elif diff_type == 1:  # in target
            result.append([diff_type, diff_text, ""])
        elif diff_type == -1:  # in source

            if re.search(f"{vol_num}་?\D་?\d+", diff_text):  # checking diff text is page or not
                result.append([1, diff_text, "pedurma-page"])
            else:

                if i > 0:  # extracting left context of current diff
                    left_diff = diffs[i - 1]
                left_diff_type, left_diff_text = left_diff
                if i < len(diffs) - 1:  # extracting right context of current diff
                    right_diff = diffs[i + 1]
                right_diff_type, right_diff_text = right_diff
                diff_ = rm_noise(diff_text)  # removes unwanted new line, space and punct
                if left_diff_type == 0 and right_diff_type == 0:
                    # checks if current diff text is located in middle of a syllable
                    if is_midsyl(left_diff_text, right_diff_text,) and get_marker(diff_text):
                        handle_mid_syl(
                            result,
                            diffs,
                            left_diff,
                            i,
                            diff,
                            right_diff_text,
                            marker_type="marker",
                        )
                    # checks if current diff text contains absolute marker or not
                    elif get_marker(diff_text):
                        # Since cur diff is not mid syl, hence if any right diff starts with tseg will
                        # be shift to left last as there are no marker before tseg.
                        tseg_shifter(result, diffs, left_diff_text, i, right_diff_text)
                        result.append([1, diff_, "marker"])
                    # Since diff type of -1 is from namsel and till now we are not able to detect
                    # marker from cur diff, we will consider it as candidate marker.
                    elif diff_:
                        if (
                            "ང" in left_diff_text[-3:] and diff_ == "སྐེ" or diff_ == "ུ"
                        ):  # an exception case where candidate fails to be marker.
                            continue
                        # print(diffs.index(right_diff), right_diff)
                        elif is_midsyl(left_diff_text, right_diff_text):
                            handle_mid_syl(
                                result,
                                diffs,
                                left_diff,
                                i,
                                diff,
                                right_diff_text,
                                marker_type="marker",
                            )

                        else:
                            tseg_shifter(result, diffs, left_diff_text, i, right_diff_text)
                            result.append([1, diff_, "marker"])
                elif right_diff_type == 1:
                    # Check if current diff is located in middle of syllabus or not.
                    if is_midsyl(left_diff_text, right_diff_text) and get_marker(diff_text):
                        handle_mid_syl(
                            result,
                            diffs,
                            left_diff,
                            i,
                            diff,
                            right_diff_text,
                            marker_type="marker",
                        )
                    elif get_marker(diff_text):
                        # Since cur diff is not mid syl, hence if any right diff starts with tseg will
                        # be shift to left last as there are no marker before tseg.
                        tseg_shifter(result, diffs, left_diff_text, i, right_diff_text)
                        result.append([1, diff_, "marker"])
                        # if "#" in right_diff[1]:
                        #     diffs[i + 1][1] = diffs[i + 1][1].replace("#", "")
                    else:
                        if diff_ != "" and right_diff_text in ["\n", " ", "་"]:
                            if (
                                "ང" in left_diff_text[-2:] and diff_ == "སྐེ"
                            ):  # an exception case where candidate fails to be marker.
                                continue
                            elif is_midsyl(left_diff_text, right_diff_text):
                                handle_mid_syl(
                                    result,
                                    diffs,
                                    left_diff,
                                    i,
                                    diff,
                                    right_diff_text,
                                    marker_type="marker",
                                )
                            else:
                                tseg_shifter(result, diffs, left_diff_text, i, right_diff_text)
                                result.append([1, diff_, "marker"])
                                # if "#" in right_diff[1]:
                                #     diffs[i + 1][1] = diffs[i + 1][1].replace("#", "")
                    # if diff_ is not empty and right diff is ['\n', ' '] then make it candidate markrer
                double_marker_handler(result)

    filter_diffs = result

    return filter_diffs


# @timed(unit="min")
def filter_footnotes_diffs(diffs_yaml_path, vol_num):
    """Filter the diffs of google ocr output and namsel ocr output.

    Args:
        diffs (list): diff list
        vol_num (int): colume number

    Returns:
        list: filtered diff containing notes from google ocr o/p and marker from namsel ocr o/p
    """
    diffs = from_yaml(diffs_yaml_path)
    left_diff = [0, "", ""]
    filtered_diffs = []
    for i, diff in enumerate(diffs):
        diff_type, diff_text, diff_tag = diff
        if diff_type == 0:
            filtered_diffs.append(diff)
        elif diff_type == 1:
            if i > 0:  # extracting left context of current diff
                left_diff = diffs[i - 1]
            if i < len(diffs) - 1:  # extracting right context of current diff
                right_diff = diffs[i + 1]
            left_diff_tag = left_diff[2]
            if left_diff_tag != "marker":
                if "4" in diff_text:
                    right_diff_text = rm_noise(right_diff[1])
                    if re.search("\d{2}", diff_text) or not right_diff_text:
                        continue
                    clean_diff = re.sub("[^4|\n]", "", diff_text)
                    filtered_diffs.append([0, clean_diff, "marker"])
                else:
                    diff_text = rm_marker(diff_text)
                    filtered_diffs.append(diff)
        else:
            filtered_diffs.append(diff)

    return filtered_diffs


def get_pedurma_pages(footnotes, vol_num):
    result = defaultdict(str)
    content_pg_nums = re.split(r"(<p.+?>)", footnotes)
    contents = content_pg_nums[::2]
    pg_nums = content_pg_nums[1::2]
    for pg_num, content in zip(pg_nums, contents):
        pg_pat = re.search(f"<p{vol_num}-(\d+)>", pg_num)
        pg_no = pg_pat.group(1)
        result[pg_no] = content
    return result


# @timed(unit="min")
def postprocess_footnotes(footnotes, vol_num):
    """Save the formatted footnotes to dictionary with key as page ref and value as footnotes in that page.
    
    Args:
        footnotes (str): formatted footnote
    Returns:
        dict: key as page ref and value as footnotes in that page
    """
    result = []
    durchens = get_pedurma_pages(footnotes, vol_num)
    for pg_num, durchen_content in durchens.items():
        page_refs = re.findall("<r.+?>", durchen_content)
        pages = re.split("<r.+?>", durchen_content)[1:]

        first_ref = page_refs[0]
        table = first_ref.maketrans("༡༢༣༤༥༦༧༨༩༠", "1234567890", "<r>")
        start = int(first_ref.translate(table))
        print(f"number of page ref found -{len(page_refs)} number of page found-{len(pages)}")
        for walker, (page, page_ref) in enumerate(
            zip_longest(pages, page_refs, fillvalue=""), start
        ):
            markers = re.finditer("<.+?>", page)
            marker_l = []
            for i, marker in enumerate(markers, 1):
                repl = f"<{i},{marker[0][1:-1]}>"
                page = page.replace(marker[0], repl, 1)
            marker_list = [durchen_content.strip() for durchen_content in page.splitlines()]
            marker_list[0] = f"{walker:03}-{page_ref[1:-1]}"
            # Removes the noise marker without footnote
            for marker in marker_list:
                if re.search("<.+?>(.+?)", marker):
                    marker_l.append(marker)
                else:
                    if "<" not in marker:
                        marker_l.append(marker)
            marker_l.append(pg_num)
            result.append(marker_l)
            # result[f"{walker:03}-{page_ref[1:-1]}"] = marker_list[1:]
    return result


# @timed(unit="min")
def demultiply_diffs(text):
    """ '<12,⓪⓪>note' --> '<12,⓪>note\n<12,⓪>note' 

    Arguments:
        text {str} -- [description]

    Returns:
        str -- [description]
    """
    patterns = [
        [
            "(\n<\d+,)([①-⓪])([①-⓪])([①-⓪])([①-⓪])([①-⓪])(>.+)",
            "\g<1>\g<2>\g<7>\g<1>\g<3>\g<7>\g<1>\g<4>\g<7>\g<1>\g<5>\g<7>\g<1>\g<6>\g<7>",
        ],
        [
            "(\n<\d+,)([①-⓪])([①-⓪])([①-⓪])([①-⓪])(>.+)",
            "\g<1>\g<2>\g<6>\g<1>\g<3>\g<6>\g<1>\g<4>\g<6>\g<1>\g<5>\g<6>",
        ],
        ["(\n<\d+,)([①-⓪])([①-⓪])([①-⓪])(>.+)", "\g<1>\g<2>\g<5>\g<1>\g<3>\g<5>\g<1>\g<4>\g<5>"],
        ["(\n<\d+,)([①-⓪])([①-⓪])(>.+)", "\g<1>\g<2>\g<4>\g<1>\g<3>\g<4>"],
    ]
    for p in patterns:
        text = re.sub(p[0], p[1], text)
    return text


# @timed(unit="min")
def rm_diff_tag(filtered_diffs):
    result = []
    for diff_type, diff_text in filtered_diffs:
        result.append([diff_type, diff_text])
    return result


# @timed(unit="min")
def merge_footnotes_per_page(page, foot_notes):
    """Merge the footnote of a certain page to its body text.

    Args:
        page (str): content in page
        foot_notes (list): list of footnotes

    Returns:
        str: content of page attached with their footnote adjacent to their marker
    """
    with_marker = page
    without_marker = page
    markers = re.finditer("<.+?>", page)
    for i, (marker, foot_note) in enumerate(zip(markers, foot_notes[1:])):
        marker_parts = marker[0][1:-1].split(",")
        body_incremental = marker_parts[0]
        body_value = marker_parts[1]
        footnotes_parts = foot_note.split(">")
        footnotes_incremental = footnotes_parts[0].split(",")[0][1:]
        footnotes_value = footnotes_parts[0].split(",")[1]
        note = footnotes_parts[1]
        repl1 = (
            f"<{body_incremental},{body_value};{footnotes_incremental},{footnotes_value},{note}>"
        )
        repl2 = f"<{note}>"
        with_marker = with_marker.replace(marker[0], repl1, 1)
        without_marker = without_marker.replace(marker[0], repl2, 1)
    if foot_notes:
        result_with_marker = with_marker + f"/{foot_notes[0]}/<dp{foot_notes[-1]}>"
        # result_without_marker = without_marker + f"/{foot_notes[0]}/"
    else:
        result_with_marker = with_marker
    result_without_marker = without_marker
    return result_with_marker, result_without_marker


# @timed(unit="min")
def merge_footnote(body_text_path, footnote_yaml_path):
    """Merge footnotes of a whole text abjacent to the marker in their content.

    Args:
        body_text_path (obj): body text path path object
        footnote_yaml_path (obj): footnote yaml path object

    Returns:
        str: footnote combined with their respective marker in text content 
    """
    body_text = body_text_path.read_text(encoding="utf-8")
    footnotes = from_yaml(footnote_yaml_path)
    pages = re.split("<p.+?>", body_text)[:-1]
    page_ann = re.findall("<p.+?>", body_text)
    result_with_marker = ""
    result_without_marker = ""
    print(f"Page found {len(pages)} Page ref found {len(page_ann)}")
    for i, (page, footnotes) in enumerate(zip_longest(pages, footnotes, fillvalue=[])):
        with_marker = ""
        without_marker = ""
        try:
            with_marker, without_marker = merge_footnotes_per_page(page, footnotes)
            result_with_marker += with_marker
            result_without_marker += without_marker
        except:
            result_with_marker += f"pages: {len(page)}, footnotes: {len(footnotes)}"
        try:
            with_marker = page_ann[i]
            result_with_marker += with_marker
            # result_without_marker += without_marker
        except:
            result_with_marker += "page missing!"
    result_without_marker = result_without_marker.replace("\n", "")
    result_without_marker = re.sub("(\[.+?\])", r"\n\1", result_without_marker)
    return result_with_marker, result_without_marker


# @timed(unit="min")
def flow(vol_path, source_path, target_path, text_type, image_info):
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
    namsel_text = source_path.read_text(encoding="utf-8")
    google_text = target_path.read_text(encoding="utf-8")
    diffs_to_yaml = partial(to_yaml, type_="diffs")  # customising to_yaml function for diff list
    filtered_diffs_to_yaml = partial(
        to_yaml, type_="filtered_diffs"
    )  # customising to_yaml function for filtered diffs list
    footnotes_to_yaml = partial(to_yaml, type_="footnotes")

    dir_path = vol_path / text_type

    diffs_yaml_path = dir_path / "diffs.yaml"
    filtered_diffs_yaml_path = dir_path / "filtered_diffs.yaml"
    # Text_type can be either body of the text or footnote footnote.
    if text_type == "body":
        # patterns = [['google_marker','(#)'],["pages", "\[\d+[ab]\]"]]
        # transformed_namsel = transfer(google_text, patterns, namsel_text, output='txt')
        # namsel_text = transformed_namsel.replace('#་','་#')
        # google_text = google_text.replace('#','')
        print("Calculating diffs...")
        diffs = get_diffs(namsel_text, google_text)
        diffs_list = list(map(list, diffs))
        diffs_to_yaml(diffs_list, dir_path)
        print("Filtering diffs...")
        filtered_diffs = filter_diffs(diffs_yaml_path, "body", image_info)
        # filtered_diffs = rm_diff_tag(filtered_diffs)
        filtered_diffs_to_yaml(filtered_diffs, dir_path)
        new_text = format_diff(filtered_diffs_yaml_path, image_info, type_="body")
        new_text = reformatting_body(new_text)
        (dir_path / f"result.txt").write_text(new_text, encoding="utf-8")

    elif text_type == "footnotes":
        annotations = [
            ["marker", "(<m.+?>)"],
            ["marker", "([①-⑩])"],
            ["pg_ref", "(<r.+?>)"],
            ["pedurma-page", "(<p.+?>)"],
        ]
        if (dir_path / "clean_g_fn.txt").is_file():
            clean_google_text = (dir_path / "clean_g_fn.txt").read_text(encoding="utf-8")
        else:
            google_text = rm_google_ocr_header(google_text)
            clean_google_text = preprocess_google_notes(google_text)
            (dir_path / "clean_g_fn.txt").write_text(clean_google_text, encoding="utf-8")
        if (dir_path / "clean_n_fn.txt").is_file():
            clean_namsel_text = (dir_path / "clean_n_fn.txt").read_text(encoding="utf-8")
        else:
            clean_namsel_text = preprocess_namsel_notes(namsel_text)
            (dir_path / "clean_n_fn.txt").write_text(clean_namsel_text, encoding="utf-8")
        print("Calculating diffs..")
        diffs = transfer(clean_namsel_text, annotations, clean_google_text)
        diffs_list = list(map(list, diffs))
        diffs_to_yaml(diffs_list, dir_path)
        filtered_diffs = filter_footnotes_diffs(diffs_yaml_path, image_info[1])
        filtered_diffs_to_yaml(filtered_diffs, dir_path)
        new_text = format_diff(filtered_diffs_yaml_path, image_info, type_="footnotes")
        reformatted_footnotes = reformat_footnotes(new_text)
        formatted_yaml = postprocess_footnotes(reformatted_footnotes, image_info[1])
        footnotes_to_yaml(formatted_yaml, dir_path)
        (dir_path / "result.txt").write_text(reformatted_footnotes, encoding="utf-8")
    else:
        print("Type not found")
    print("Done")


if __name__ == "__main__":
    vol_num = 67
    # only works text by text or note by note for now
    # TODO: run on whole volumes/instances by parsing the BDRC outlines to find and identify text type and get the image locations
    image_info = [
        "W1PD95844",
        vol_num,
        33,
    ]  # [<kangyur: W1PD96682/tengyur: W1PD95844>, <volume>, <offset>]
    text_types = ["body", "footnotes"]
    base_path = Path(f"./data/v{vol_num:03}")
    for text_type in text_types:
        if text_type == "body":
            google_text_path = base_path / text_type / f"{vol_num}E-{text_type}_transfered.txt"
        else:
            google_text_path = base_path / text_type / f"{vol_num}G-{text_type}.txt"
        namsel_text_path = base_path / text_type / f"{vol_num}N-{text_type}.txt"
        flow(base_path, namsel_text_path, google_text_path, text_type, image_info)
        print(f"{text_type} part done..")
    body_result_path = base_path / f"body/result.txt"
    footnote_yaml_path = base_path / f"footnotes/footnotes.yaml"
    merge_marker = ""
    merge = ""
    if body_result_path.is_file() and footnote_yaml_path.is_file():
        print("Merge start..")
        merge_marker, merge = merge_footnote(body_result_path, footnote_yaml_path)
        merge_marker = add_link(merge_marker, image_info)
        (base_path / f"{vol_num}_combined_marker.txt").write_text(merge_marker, encoding="utf-8")
        (base_path / f"{vol_num}_combined.txt").write_text(merge, encoding="utf-8")
        print("Merge complete.")

