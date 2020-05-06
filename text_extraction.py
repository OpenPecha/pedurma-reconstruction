
import re
from diff_match_patch import diff_match_patch
from IPython.core.debugger import set_trace

def get_text(file):
    with open(file) as f:
        return f.read()


def get_start_sync_point(namsel_text, basetext):
    dmp = diff_match_patch()
    dmp.Diff_Timeout = 0
    nam_start = namsel_text[:5000]
    base_start = basetext[:5000]
    start_diffs = dmp.diff_main(nam_start, base_start)
    dmp.diff_cleanupSemantic(start_diffs)
    starting_noise = start_diffs[0][1]
    return len(starting_noise)


def get_end_sync_point(namsel_text, basetext):
    end_noise = ''
    dmp = diff_match_patch()
    dmp.Diff_Timeout = 0
    base_end = basetext[-1000:]
    durchen = re.search('〈〈\S+?〉〉', namsel_text)
    if durchen:
        durchen_start = durchen.start() - 100
        nam_end = namsel_text[durchen_start:]
    else:
        print('No Durchen found')
        nam_end = ''
    end_diffs = dmp.diff_main(nam_end, base_end)
    dmp.diff_cleanupSemantic(end_diffs)
    #print(len(end_diffs))
    for end_diff in end_diffs:
        if end_diff[0]==-1:
            end_noise += end_diff[1]
    return len(end_noise)


def get_main_text(namsel_text, basetext):
    main_text = ''
    start_point = get_start_sync_point(namsel_text, basetext)
    print(start_point)
    end_point = get_end_sync_point(namsel_text, basetext)
    print(end_point)
    main_text = namsel_text[start_point:-end_point]
    return main_text


def flow(namsel_path, basetext_path):
    namsel_text = get_text(namsel_path)
    basetext = get_text(basetext_path)
    pecha_num = re.search('\d+', basetext_path)[0]
    main_text = get_main_text(namsel_text, basetext)
    with open(f'./namsel_body_text/{pecha_num}.txt','w+') as f:
        f.write(main_text)
    print('Done')