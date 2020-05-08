import sys

sys.path.append("../")
import re
from pathlib import Path

import reconstruction


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


def write_diffs(diffs):
    """All the diffs are formated and written in a file.

    Args:
        diffs (str): list of diff
    """
    result = ""
    for diff in diffs:
        result += f"  {diff[0]}=>   {diff[1]}\n"
    with open("./data/Reconstructor/body_text/test1diffs.txt", "w+") as f:
        f.write(result)


def test_reconstruction():
    """Test for reconstruction.

    """
    target_path = "./data/Reconstructor/body_text/test1clean.txt"
    source_path = "./data/Reconstructor/body_text/test1namsel.txt"
    truth_path = "./data/Reconstructor/body_text/test1truth.txt"
    vol_num = 74
    target = Path(target_path).read_text()
    source = Path(source_path).read_text()
    expected = Path(truth_path).read_text()
    diffs = reconstruction.get_diff(target, source)
    write_diffs(diffs)
    result = reconstruction.apply_diff_body(diffs, vol_num)
    result = rm_markers_ann(result)
    with open(f"./data/Reconstructor/body_text/test2result.txt", "w+") as f:
        f.write(result)
    # assert result == expected, "Not match"


def test_preprocessed():
    """Test the preprocessing of footnote being normalised or not."""

    google_path = "./data/Reconstructor/footnote_text/input/test1google.txt"
    namsel_path = "./data/Reconstructor/footnote_text/input/test1namsel.txt"
    google_truth_path = "./data/Reconstructor/footnote_text/input/test1googletruth.txt"
    namsel_truth_path = "./data/Reconstructor/footnote_text/input/test1namseltruth.txt"
    google_text = Path(google_path).read_text()
    namsel_text = Path(namsel_path).read_text()
    google_truth = Path(google_truth_path).read_text()
    namse_truth = Path(namsel_truth_path).read_text()
    clean_google, clean_namsel = reconstruction.preprocess_footnote(google_text, namsel_text)
    assert google_truth == clean_google
    assert namse_truth == clean_namsel


if __name__ == "__main__":
    test_reconstruction()
