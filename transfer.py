import re
from itertools import zip_longest
import unicodedata
from pathlib import Path
from functools import partial
import yaml
from diff_match_patch import diff_match_patch
from preprocess import preprocess_google_notes, preprocess_namsel_notes
from horology import timed


@timed(unit="s")
def get_diffs(A, B):
    """Compute diff between source and target with DMP.
    Args:
        source (str): source text
        target (str): target text
    Returns:
        list: list of diffs
    """
    print("Diff computation started...")
    dmp = diff_match_patch()
    dmp.Diff_Timeout = 0  # compute diff till end of file
    diffs = dmp.diff_main(A, B)
    # dmp.diff_cleanupSemantic(diffs)    # beautifies the diff list
    diffs_list = list(map(list, diffs))
    print("Diff computation completed!")
    return diffs_list


@timed(unit="s", name="to_yaml: ")
def to_yaml(list_, path, type=None):
    """Dump list to yaml and write the yaml to a file on mentioned path.
    Args:
        list_ (list): list
        vol_path (path): base path object
    """
    list_yaml = yaml.safe_dump(list_, allow_unicode=True)
    list_yaml_path = path
    list_yaml_path.write_text(list_yaml, encoding="utf-8")
    print(f"{type} saved")


@timed(unit="s", name="from_yaml: ")
def from_yaml(path):
    """Load yaml to list
    Args:
        vol_path (path): base path object
        type (string): 
    """
    diffs = yaml.safe_load(path.read_text(encoding="utf-8"))
    diffs_list = list(diffs)
    return diffs_list


@timed(unit="s", name="format: ")
def format(diffs):
    result = ""
    for n, s in diffs:
        if n == 0 or n == 1:
            result += s
        else:
            pass
    return result


@timed(unit="s", name="filter_annotations: ")
def filter_annotations(annotations, diffs):
    a = annotations[1]

    # Isolate annotation: 1 per diff string, not split
    result = []
    for i, diff in enumerate(diffs):
        if diff[0] != -1:
            if diff[0] == 1:
                diff[1] = re.sub(a, "", diff[1])
        if diff[0] == -1:
            if re.search(a, diff[1]):
                if diff[1] == a:
                    diff[0] = 1
                    result.append(diff)
                else:
                    split_string = re.split(f"({a})", diff[1])
                    for chunk in split_string:
                        if chunk == a:
                            result.append([1, chunk])
                        else:
                            result.append([-1, chunk])
            else:
                result.append(diff)
        else:
            result.append(diff)
    return result


def tag_to_tofu(content, annotations):
    all_annotations = "("
    for i, annotation in enumerate(annotations):
        if annotation is annotations[-1]:
            all_annotations += f"{annotation[1]})"
        else:
            all_annotations += f"{annotation[1]}|"
    split_list = re.split(all_annotations, content)
    tofu_mapping = {}
    for i, e in enumerate(split_list):
        if re.search(all_annotations, e):
            tofu = chr(i + 1000000)
            for annotation in annotations:
                if re.search(annotation[1], e):
                    tofu_mapping[tofu] = [annotation[0], e]
            split_list[i] = tofu
    new_content = "".join(split_list)
    return new_content, tofu_mapping


def filter_diff(diffs_list, tofu_mapping):
    result = []
    for i, (diff_type, diff_text) in enumerate(diffs_list):
        if diff_type == 0 and diff_type == 1:
            result.append([diff_type, diff_text, ""])
        else:
            if re.search("[chr(1000000)-chr(2000000)]", diff_text):
                anns = re.split("([chr(1000000)-chr(2000000)])", diff_text)
                for ann in anns:
                    if tofu_mapping.get(ann):
                        tag, value = tofu_mapping.get(ann)
                        result.append([0, value, tag])
                    else:
                        result.append([0, ann, ""])
    return result


@timed(unit="s", name="transfer: ")
def transfer(source_path, annotations, target_path):
    # catches annotation in source with regex and transfer them to target while preserving
    # all the content in both source and target.
    # converts annotations to tofu id in source and save the mapping
    # generate diff between tofu source and target
    # in diff isolate tofu ids by spliting noisy strings
    # filter diffs by tofu id range and asignining diff type as 0
    # convert tofu id back to annotation using mapping
    # return transfer diffs containing target+ annotation

    source = source_path.read_text(encoding="utf-8")
    target = target_path.read_text(encoding="utf-8")
    tofu_source, tofu_mapping = tag_to_tofu(source, annotations)
    Path("./tests/durchen_test1/tofu.txt").write_text(tofu_source, encoding="utf-8")
    print("Tofu done..")
    diffs = get_diffs(tofu_source, target)

    transfered_diff = filter_diff(diffs, tofu_mapping)
    return transfered_diff


if __name__ == "__main__":
    base_path = Path("tests/durchen_test1")

    source = base_path / "input/G.txt"
    annotations = [
        ["marker", "(<m.+?>)"],
        ["marker", "([①-⑩])"],
        ["pg_ref", "(<r.+?>)"],
        ["pedurma_page", "(<p.+?>)"],
    ]
    target = base_path / "input/N.txt"

    transfered_diffs = transfer(source, annotations, target)
    to_yaml(transfered_diffs, base_path / "transfered_diff.yaml", type=None)
