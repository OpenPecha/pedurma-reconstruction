"""This module is to extract body text of namsel orc text by excluding durchen(footnote)."""

import re
from pathlib import Path

from diff_match_patch import diff_match_patch


def get_start_sync_point(namsel_text, clean_text):
    """Compute the starting sync point in namselOCRed text.

    Args:
        namsel_text (str): first 5000 characters of namselOCRed text
        basetext (str): first 5000 charachets of clean etext text

    Returns:
        (int): start sync index
    """
    dmp = diff_match_patch()
    dmp.Diff_Timeout = 0
    start_diffs = dmp.diff_main(namsel_text, clean_text)
    dmp.diff_cleanupSemantic(start_diffs)
    starting_noise = start_diffs[0][1]
    return len(starting_noise)


def get_end_sync_point(namsel_text, clean_text):
    """Compute end sync point of namsel text to exclude durchen.

    Args:
        namsel_text (str): contents namsel ocr text
        clean_text (str): contents clean etext

    Returns:
        (int): end sync index
    """
    end_noise = ""
    durchen = re.search("〈〈\S+?〉〉", namsel_text)
    dmp.Diff_Timeout = 0
    clean_end = clean_text[-1000:]
    durchen = re.search("〈〈\S+?〉〉", namsel_text)
    if durchen:
        durchen_start = durchen.start() - 100
        nam_end = namsel_text[durchen_start:]
        end_diffs = dmp.diff_main(nam_end, clean_end)
        dmp.diff_cleanupSemantic(end_diffs)
        # print(len(end_diffs))
        for end_diff in end_diffs:
            if end_diff[0] == -1:
                end_noise += end_diff[1]
        return len(end_noise)
    else:
        print("No Durchen found")
        return 0


def get_main_text(namsel_text, clean_text):
    """Extract body text from namselOCRed text using clean_text.

    Args:
        namsel_text (str): namsel ocr text
        clean_text (str): clean text

    Returns:
        (str): body text
    """
    main_text = ""
    start_point = get_start_sync_point(namsel_text, basetext)
    print(start_point)
    end_point = get_end_sync_point(namsel_text, basetext)
    print(end_point)
    main_text = namsel_text[start_point:-end_point]
    return main_text


if __name__ == "__main__":
    namsel_text = Path("./input/namselORCed_text/v073.txt").read_text()
    clean_text = Path("./input/body_text/cleantext/v073.txt").read_text()
    body_text = get_body_text(namsel_text, clean_text)
    vol_num = 73
    with open(f"./input/body_text/ocred_text/{vol_num}.txt", "w+") as f:
        f.write(body_text)
