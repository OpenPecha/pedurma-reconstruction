import re
import yaml
from pathlib import Path


def get_pages(vol_text):
    result = []
    pg_text = ""
    pages = re.split(r"(\[[0-9]+[a-z]{1}\])", vol_text)
    for i, page in enumerate(pages[1:]):
        if i % 2 == 0:
            pg_text += page
        else:
            pg_text += page
            result.append(pg_text)
            pg_text = ""
    return result


def get_text(text_with_durchen):
    durchen_starting = re.search('\<d', text_with_durchen).start()
    text_content = text_with_durchen[:durchen_starting]
    return text_content


def get_durchen(text_with_durchen):
    durchen_start = re.search('\<d', text_with_durchen).start()
    durchen_end = re.search('d\>', text_with_durchen).start()
    durchen = text_with_durchen[durchen_start:durchen_end]
    durchen = add_first_page_ann(durchen)
    return durchen


def add_first_page_ann(text):
    lines = text.splitlines()
    line_pat = re.search(r"\[(\w+)\.(\d+)\]", lines[1])
    page_ann = f"[{line_pat.group(1)}]"
    line_ann = f"[{line_pat.group(1)}.{int(line_pat.group(2))-1}]"
    new_text = f"{page_ann}\n{line_ann}{text}"
    return new_text


def get_link(pg_num, text_meta):
    vol = text_meta['vol']
    work = text_meta['work_id']
    img_group_offset = text_meta['img_grp_offset']
    pref = text_meta['pref']
    igroup = f"{pref}{img_group_offset+vol}"
    link = f"https://www.tbrc.org/browser/ImageService?work={work}&igroup={igroup}&image={pg_num}&first=1&last=2000&fetchimg=yes"
    return link


def get_page_num(page_ann):
    pg_num = int(page_ann[:-1])*2
    pg_face = page_ann[-1]
    if pg_face == 'a':
        pg_num -= 1
    return pg_num


def get_page_info(page, text_meta):
    page_info = {}
    page_index = re.search(r"\[([𰵀-󴉱])?[0-9]+[a-z]{1}\]", page)[0][1:-1]
    page_content = re.sub(r"\[([𰵀-󴉱])?[0-9]+[a-z]{1}\]", "", page)
    page_content = re.sub(r"\[(\w+)\.(\d+)\]", "", page_content)
    pg_num = get_page_num(page_index)
    page_link = get_link(pg_num, text_meta)
    if page_content != '\n':
        page_info[page_index] = {
            'pg_content': page_content,
            'pg_link': page_link
        }
    return page_info 


def get_page_wise(text, text_meta):
    page_wise_result = {}
    pages = get_pages(text)
    for page in pages:
        pg_info = get_page_info(page, text_meta)
        page_wise_result.update(pg_info)
    return page_wise_result


def parse_text(text_id, text_content, text_meta):
    
    text_content = add_first_page_ann(text_content)
    text_content = re.sub('[𰵀-󴉱]', '', text_content)
    text = get_text(text_content)
    durchen = get_durchen(text_content)
    pg_wise_text = get_page_wise(text, text_meta)
    pg_wise_durchen = get_page_wise(durchen, text_meta)
    text_durchen = {
        'text': pg_wise_text,
        'durchen': pg_wise_durchen
    }
    return text_durchen
    text_durchen_yml = yaml.safe_dump(text_durchen, sort_keys=False, allow_unicode=True)
    Path(f'./D1109_pg_wise.yml').write_text(text_durchen_json)

