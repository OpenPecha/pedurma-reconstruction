import pytest
import sys

# sys.path.append("../")
import re
import yaml
from functools import partial
from pathlib import Path

from reconstruction import get_preview_page

def test_get_preview_page():
    text_meta = {
        'vol': 1,
        'work_id': 'W1PD95844',
        'img_grp_offset': 845,
        'pref': 'I1PD95'
    }
    g_body_page = Path('./tests/preview_test/109b_dg.txt').read_text(encoding='utf-8')
    n_body_page =  Path('./tests/preview_test/109b_n.txt').read_text(encoding='utf-8')
    g_durchen_page = Path('./tests/preview_test/113a_g.txt').read_text(encoding='utf-8')
    n_durchen_page = Path('./tests/preview_test/113a_n.txt').read_text(encoding='utf-8')
    preview_page = get_preview_page(g_body_page, n_body_page, g_durchen_page, n_durchen_page, text_meta)
    return preview_page

if __name__ == "__main__":
    prev_pg = test_get_preview_page()
    Path('./tests/preview_test/prev_pg.txt').write_text(prev_pg, encoding='utf-8')