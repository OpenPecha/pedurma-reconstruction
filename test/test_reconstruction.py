import sys

sys.path.append("../")
import re
from pathlib import Path

import reconstruction


def rm_markers_ann(text):
    result = ""
    lines = text.splitlines()
    for line in lines:
        line = re.sub("<<.+?>>", "", line)
        line = re.sub("<.+?>", "#", line)
        result += line + "\n"
    return result


def test_reconstruction():
    target_path = "./data/Reconstructor/body_text/test1clean.txt"
    source_path = "./data/Reconstructor/body_text/test1namsel.txt"
    truth_path = "./data/Reconstructor/body_text/test1truth.txt"
    vol_num = 74
    target = Path(target_path).read_text()
    source = Path(source_path).read_text()
    expected = Path(truth_path).read_text()
    diffs = reconstruction.get_diff(target, source)
    result = reconstruction.apply_diff_body(diffs, vol_num)
    result = rm_markers_ann(result)
    # with open(f"./data/Reconstructor/body_text/test1result.txt", "w+") as f:
    #     f.write(result)
    assert result == expected, "Not match"


if __name__ == "__main__":
    test_reconstruction()
