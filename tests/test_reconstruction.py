import sys

sys.path.append("../")
import re
import yaml
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
    basePath = Path("./test2/")
    target_path = basePath / "input" / "a.txt"
    source_path = basePath / "input" / "b.txt"
    # truth_path = basePath / "test1truth.txt"
    image_info = [
        "W1PD96682",
        74,
        19,
    ]
    target = Path(target_path).read_text()
    source = Path(source_path).read_text()
    # expected = Path(truth_path).read_text()
    diffs = reconstruction.get_diff(source, target)
    diffsList = list(map(list, diffs))
    print("Dumping diffs...")
    diffsYaml = yaml.safe_dump(diffsList, allow_unicode=True)
    diffsYamlPath = basePath / "diffs.yaml"
    diffsYamlPath.write_text(diffsYaml, encoding="utf-8")
    filterdiffs = reconstruction.filterDiffs(diffsYamlPath, "body", image_info)
    filterdiffsYaml = yaml.safe_dump(filterdiffs, allow_unicode=True)
    filterDiffPath = basePath / "filterdiff.yaml"
    filterDiffPath.write_text(filterdiffsYaml, encoding="utf-8")
    # write_diffs(diffs)
    result = reconstruction.apply_diff_body(filterdiffs, image_info)
    # result = reconstruction.add_link(result, image_info)
    result = rm_markers_ann(result)
    with open(f"./test2/output/result.txt", "w+") as f:
        f.write(result)
    # assert result == expected, "Not match"


# def test_preprocessed():
#     """Test the preprocessing of footnote being normalised or not."""

#     google_path = "./data/Reconstructor/footnote_text/input/test1google.txt"
#     namsel_path = "./data/Reconstructor/footnote_text/input/test1namsel.txt"
#     google_truth_path = "./data/Reconstructor/footnote_text/input/test1googletruth.txt"
#     namsel_truth_path = "./data/Reconstructor/footnote_text/input/test1namseltruth.txt"
#     google_text = Path(google_path).read_text()
#     namsel_text = Path(namsel_path).read_text()
#     google_truth = Path(google_truth_path).read_text()
#     namse_truth = Path(namsel_truth_path).read_text()
#     clean_google, clean_namsel = reconstruction.preprocess_footnote(google_text, namsel_text)
#     assert google_truth == clean_google
#     assert namse_truth == clean_namsel


if __name__ == "__main__":
    test_reconstruction()
