import sys

sys.path.append("../")
import re
import yaml
from functools import partial
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
    print(f"{type_} Yaml saved...")


def test_reconstruction():
    """Test for reconstruction.

    """
    base_path = Path("./test1/")
    target_path = base_path / "input" / "a.txt"
    source_path = base_path / "input" / "b.txt"
    diffs_to_yaml = partial(to_yaml, type_="diffs")
    filtered_diffs_to_yaml = partial(to_yaml, type_="filtered_diffs")
    # truth_path = base_path / "test1truth.txt"
    image_info = [
        "W1PD96682",
        74,
        18,
    ]

    target = Path(target_path).read_text()
    source = Path(source_path).read_text()
    # expected = Path(truth_path).read_text()
    print("Calculating diff...")
    diffs = reconstruction.get_diff(source, target)
    diffs_list = list(map(list, diffs))
    diffs_to_yaml(diffs_list, base_path)
    filtered_diffs = reconstruction.filter_diffs(diffs_list, "body", image_info)
    filtered_diffs_to_yaml(filtered_diffs, base_path)
    result = reconstruction.format_diff(filtered_diffs, image_info)
    # result = reconstruction.add_link(result, image_info)
    result = rm_markers_ann(result)
    (base_path / "output/result.txt").write_text(result, encoding="utf-8")
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
