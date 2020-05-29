import re
from pathlib import Path
import yaml
from diff_match_patch import diff_match_patch
from horology import timed


@timed(unit="min")
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
    diffs_list = list(map(list, diffs))
    print("Diff computation completed")
    return diffs_list


@timed(unit="min")
def to_yaml(list_,):
    """Dump list to yaml and write the yaml to a file on mentioned path.
    Args:
        list_ (list): list
        vol_path (path): base path object
    """
    list_yaml = yaml.safe_dump(list_, allow_unicode=True)

    return list_yaml


@timed(unit="min")
def from_yaml(path):
    """Load yaml to list
    Args:
        vol_path (path): base path object
        type (string): 
    """
    diffs = yaml.safe_load(path.read_text(encoding="utf-8"))
    diffs_list = list(diffs)
    return diffs_list


@timed(unit="min")
def to_text(diffs):
    result = ""
    for diff in diffs:
        if diff[0] != -1:
            result += diff[1]
    return result


def tag_to_tofu(content, annotations):
    print("Mapping annotations to tofu-IDs")
    new_content = content
    #  support
    if isinstance(annotations[0], str):
        annotations = [annotations]

    tofu_mapping = {}
    tofu_walker = 0
    for annotation in annotations:
        split_list = re.split(annotation[1], new_content)
        for i, e in enumerate(split_list):
            if re.search(annotation[1], e):
                tofu = chr(tofu_walker + 1000000)
                tofu_walker += 1
                tofu_mapping[tofu] = [annotation[0], e]
                split_list[i] = tofu
        new_content = "".join(split_list)
    return new_content, tofu_mapping


def filter_diff(diffs_list, tofu_mapping):
    print("Transfering annotations...")
    result = []
    for i, (diff_type, diff_text) in enumerate(diffs_list):
        if diff_type == 0 or diff_type == 1:
            result.append([diff_type, diff_text, ""])
        elif diff_type == -1:
            # tofu-IDs are limited to 1114111
            if re.search(f"[{chr(1000000)}-{chr(1114111)}]", diff_text):
                anns = re.split(f"([{chr(1000000)}-{chr(1114111)}])", diff_text)
                for ann in anns:
                    if ann:
                        if tofu_mapping.get(ann):
                            tag, value = tofu_mapping.get(ann)
                            result.append([0, value, tag])
                        else:
                            result.append([-1, ann, ""])
    return result


@timed(unit="min")
def transfer(source, patterns, target, output="diff"):
    """Extract annotations from with regex patterns and transfer to target

    Arguments:
        source {str} -- text version containing the annotations to transfer
        patterns {list} -- ['annotation type', '(regex to detect the annotations)'] Put in () to preserve, without to delete.
        target {str} -- text that will receive the transfered annotation 

    Keyword Arguments:
        output {str} -- ["diff", "yaml" or "txt"] (default: {'diff'})

    Returns:
        [diff, yaml or txt] -- returns a diff with 3 types of strings: 0 overlaps, 1 target and -1 source.
        Can also return the diff in yaml or a string containing target+annotations 
    """

    print(f"Annotation transfer started...")

    tofu_source, tofu_mapping = tag_to_tofu(source, patterns)
    diffs = get_diffs(tofu_source, target)

    filterred_diff = filter_diff(diffs, tofu_mapping)

    if output == "diff":
        result = filterred_diff
    elif output == "yaml":
        result = to_yaml(filterred_diff)
    elif output == "txt":
        result = to_text(filterred_diff)
    return result


if __name__ == "__main__":

    # Sample usage

    source = """[1a]
            [1a.1]༄༅། །མདོ་སྡེ་ཧ་པ་བཞུགས་སོ། །
            [1b]
            [1b.1]{D340}༄༅༅། །རྒྱ་གར་སྐད་དུ། ཀརྨ་ཤ་ཏ་ཀ། བོད་སྐད་དུ། ལས་བརྒྱ་ཐམ་པ་པ། བམ་པོ་དང་པོ། ཐམས་ཅད་མཁྱེན་པ་ལ་ཕྱག་འཚལ་ལོ། །གང་ལས་
            [1b.2]འཇིག་རྟེན་བླ་མ་བདེ་གཤེགས་ཐོས་པའི་སྒོ་ནས་རབ་སྙན་བརྟན་པའི་གསུང་ལྡན་གྱིས། །སེམས་ཅན་རྣམས་ལ་ཕན་པ་འབའ་ཞིག་བཞེད་ཕྱིར་བཤད་པ་རྣམ་པ་སྣ་ཚོགས་རང་ཉིད་ཀྱིས། །
            [1b.3]ལོག་པར་ལྟ་བའི་མུན་ནག་ཆེན་པོ་ཐིབས་པོར་འཐོམས་ཤིང་འཁྲུགས་པ་རྣམས་ལ་རབ་གསུངས་པ། །དེ་ཡི་མིང་ནི་ལས་རྣམ་བརྒྱ་པ་ཞེས་བྱ་ཡོངས་སུ་ཚང་བ་བདག་གིས་བཤད་ཀྱིས་
            [1b.4]ཉོན། །སྤྱི་སྡོམ་ནི། ཁྱི་མོ་དང་ནི་ཤིང་རྟ་དང་། །ཀ་ཙང་ཀ་ལ་བྱམས་མི་སྡུག །བྱ་དང་འཕྱེ་བོ་གང་པོ་དང་། །བུ་རྣམས་དང་ནི་བརྒྱ་བྱིན་ནོ། །སྡོམ་ནི། ཁྱི་མོ་མིག་ཆུང་
            [1b.5]རྫོགས་བྱེད་དང་། །སྒུར་གཉིས་འཆར་ཀ་རྒྱལ་མཚན་དང་། །བདེ་བྱེད་མ་དང་ནོར་བུའི་འོད། །སྣ་མའི་མེ་ཏོག་ང་བྱིན་དང་། །འདུས་མོ་དང་ནི་ཚེམ་བུ་མཁན། །ཁྱི་མོ་ཞེས་བྱ་
            [2a]
            [2a.1]བ་ནི། གླེང་གཞི་མཉན་དུ་ཡོད་པ་ན་བཞུགས་ཏེ། དེའི་ཚེ་མཉན་དུ་ཡོད་པ་ན། ཁྱིམ་བདག་ཕྱུག་ཅིང་ནོར་མང་ལ་ལོངས་སྤྱོད་ཆེ་བ་ཡོངས་སུ་འཛིན་པ་ཡངས་ཤིང་རྒྱ་ཆེ་བ། རྣམ་ཐོས་ཀྱི་བུའི་ནོར་དང་ལྡན་པ། རྣམ་ཐོས་ཀྱི་བུའི་ནོར་དང་འགྲན་
            [2a.2]པ་ཞིག་གནས་ཏེ། མུ་སྟེགས་ཅན་ལ་དགའོ། །དེ་ནས་དེས་ཐབས་ཟླར་བབ་པ་ལས་ཆུང་མ་བླངས་ནས། དེ་དེ་དང་ལྷན་ཅིག་ཏུ་རྩེ་ཞིང་དགའ་ལ་དགའ་མགུར་སྤྱོད་དོ། །དེ་རྩེ་ཞིང་དགའ་ལ་དགའ་མགུར་སྤྱོད་པ་ལས་ཕྱིས་དེའི་ཆུང་མ་ལ་བུ་ཆགས་ནས་དེ་ཟླ་བ་དགུའམ་
    """

    target = """༄༅#
            ༅། །རྒྱ་གར་སྐད་དུ། ཀརྨ་ཤ་ཏ་ཀ། བོད་སྐད་དུ། ལས་བརྒྱ་
            ཐམ་པ་པ། བམ་པོ་དང་པོ། ཐམས་ཅད་མཁྱེན་པ་ལ་ཕྱག་འཚལ་ལོ། །གང་
            ལས་འཇིག་རྟེན་བླ་མ་བདེ་གཤེགས་ཐོས་པའི་སྒོ་ནས་རབ་སྙན་བརྟན་པའི་གསུང་
            ལྡན་གྱིས། །སེམས་ཅན་རྣམས་ལ་ཕན་པ་འབའ་ཞིག་བཞེད་ཕྱིར་བཤད་པ་རྣམ་
            པ་སྣ་ཚོགས་རང་ཉིད་ཀྱིས། །ལོག་པར་ལྟ་བའི་མུན་ནག་ཆེན་པོ་ཐིབས་པོར་
            :འཐོམས་ཤིང#་འཁྲུགས་པ་རྣམས་ལ་རབ་གསུངས་པ། །:དེ་ཡི་#མིང་ནི་ལས་
            རྣམ་#བརྒྱ་པ་ཞེས་བྱ་ཡོངས་སུ་ཚང་བ་བདག་གིས་བཤད་ཀྱིས་#ཉོན། །སྤྱི་སྡོམ་
            ནི། ཁྱི་མོ་དང་ནི་ཤིང་རྟ་དང་། །ཀ་ཙང་#ཀ་ལ་བྱམས་མི་སྡུག །བྱ་དང་འཕྱེ་
            བོ་#གང་པོ་དང་། །བུ་རྣམས་དང་ནི་བརྒྱ་བྱིན་ནོ། །སྡོམ་ནི། ཁྱི་མོ་མིག་ཆུང་#
            རྫོགས་བྱེད་དང་། །སྒུར་གཉིས་འཆར་ཀ་རྒྱལ་མཚན་#དང་། །བདེ་བྱེད་མ་
            དང་ནོར་བུའི་འོད། །སྣ་མའི་མེ་ཏོག་ང་#བྱིན་དང་། །འདུས་མོ་དང་ནི་ཚེམ་བུ་
            མཁན། །ཁྱི་མོ་ཞེས་བྱ་བ་ནི། གླེང་:གཞི་མཉན་དུ་ཡོད་པ་ན་བཞུགས་ཏེ།
            དེའི་ཚེ་མཉན་དུ་ཡོད་པ་ན། ཁྱིམ་བདག་ཕྱུག་ཅིང་ནོར་མང་ལ་ལོངས་སྤྱོད་ཆེ་
            བ་ཡོངས་སུ་འཛིན་པ་ཡངས་ཤིང་རྒྱ་ཆེ་བ། རྣམ་ཐོས་ཀྱི་བུའི་ནོར་དང་ལྡན་པ།
            རྣམ་ཐོས་ཀྱི་བུའི་ནོར་དང་འགྲན་པ་ཞིག་གནས་ཏེ། མུ་སྟེགས་ཅན་ལ་དགའོ། །
            དེ་ནས་དེས་ཐབས་ཟླར་བབ་པ་ལས་ཆུང་#མ་བླངས་ནས། དེ་དེ་དང་ལྷན་ཅིག་
            ཏུ་རྩེ་ཞིང་དགའ་ལ་དགའ་མགུར་སྤྱོད་དོ། །དེ་རྩེ་ཞིང་དགའ་ལ་དགའ་མགུར་
            སྤྱོད་པ་ལས་ཕྱིས་དེའི་ཆུང་མ་ལ་#བུ་ཆགས་ནས་དེ་ཟླ་བ་དགུའམ་བཅུ་ལོན་པ་
            """

    base_path = Path("data/v073/")

    source = (base_path / "body" / "073_མདོ་སྡེ།_ཧ.txt").read_text(encoding="utf-8")
    annotation_patterns = [["pages", "(\[\d+[ab]\])"], ["lines", "\[\d+.\.\d\]"]]
    target = (base_path / "body" / "73E-body_transfered.txt").read_text(
        encoding="utf-8"
    )

    annotated = transfer(source, annotation_patterns, target, "yaml")
    (base_path / "body" / "new.txt").write_text(annotated, encoding="utf-8")

