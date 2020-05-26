import re
from itertools import zip_longest
import unicodedata
from pathlib import Path
from functools import partial
import yaml
from diff_match_patch import diff_match_patch
from preprocess_footnotes import preprocessGoogleNotes, preprocessNamselNotes
from horology import timed


@timed(unit='s')
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
    dmp.Diff_Timeout = 0    # compute diff till end of file
    diffs = dmp.diff_main(A, B)
    # dmp.diff_cleanupSemantic(diffs)    # beautifies the diff list
    diffs_list = list(map(list, diffs))
    print("Diff computation completed!")
    return diffs_list

@timed(unit='s', name='to_yaml: ')
def to_yaml(list_, target_path, type=None):
    """Dump list to yaml and write the yaml to a file on mentioned path.
    Args:
        list_ (list): list
        base_path (path): base path object
        type (string): 
    """
    list_yaml = yaml.safe_dump(list_, allow_unicode=True)
    list_yaml_path = target_path.parent / f'{type}.yml'
    list_yaml_path.write_text(list_yaml, encoding="utf-8")
    print(f"{type} saved")

@timed(unit='s', name='from_yaml: ')
def from_yaml(path):
    """Load yaml to list
    Args:
        base_path (path): base path object
        type (string): 
    """
    diffs = yaml.safe_load(path.read_text(encoding="utf-8"))
    diffs_list = list(diffs)
    return diffs_list

@timed(unit='s', name='format: ')
def format(diffs):
    result = ''
    for n, s in diffs:
        if n == 0 or n == 1 :
            result += s
        else:
            pass
    return result


@timed(unit='s', name='filter_annotations: ')
def filter_annotations(annotations, diffs):
    a = annotations[0]

    # simple annotation: 1 per diff string, not split 

    result =[]
    for i, diff in enumerate(diffs):
        print(i)
        if diff[0] == -1:
            if re.search(a, diff[1]):
                if diff[1] == a:
                    diff[0] = 1
                    result.append(diff)
                elif re.match(a, diff[1]):
                    result.append([1, a])    # center
                    diff[1] = re.sub(f"{a}([^{a}]+)", "\1", diff[1]) # right context
                    result.append(diff)
                else:
                    result.append([-1, re.sub(f"([^{a}]+){a}([^{a}]+)", "\g<1>", diff[1])]) # left 
                    result.append([1, a])    # center
                    diff[1] = re.sub(f"([^{a}]+){a}([^{a}]+)", "\g<2>", diff[1]) # right
                    result.append(diff)
            else:
                result.append(diff)
        else:
            result.append(diff)
    return result

@timed(unit='s', name='transfer: ')
def transfer(source_path, annotations, target_path):

    source = source_path.read_text(encoding="utf-8")
    target = target_path.read_text(encoding="utf-8")

    raw_yaml_path = target_path.parent / 'raw.yml'

    if raw_yaml_path.is_file():
        diffs = from_yaml(raw_yaml_path)
        pass
    else:
        diffs = get_diffs(source, target)
        to_yaml(diffs, target_path, 'raw')
    
    edit_yaml_path = target_path.parent / 'edit.yml'

    filtered = filter_annotations(annotations, diffs)
    to_yaml(filtered, target_path, 'edit')
    edited = from_yaml(edit_yaml_path)

    formated_path = target_path.parent / 'transfered.txt'
    formated = format(edited)
    formated_path.write_text(formated, encoding="utf-8")



if __name__ == "__main__":
    base_path = Path("input/body_text/input")

    source = base_path / "73G.txt"
    annotations = ["#"]
    target = base_path / "73A.txt"

    transfer(source, annotations, target)