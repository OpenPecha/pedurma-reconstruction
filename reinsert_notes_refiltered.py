from pathlib import Path


def parse_notes(notes_raw):
    notes = []
    page = ''
    for n in notes_raw:
        if not n.startswith('\t'):
            page = n.split('\t')[0]
            notes.append(n)
        else:
            notes.append(page + n)
    return notes


def reinsert_notes(notes, derge, mode=1):
    out = []
    for i in range(len(derge)):
        print(i)
        text = derge[i]
        try:
            if mode == 1:
                note = notes[i]
            elif mode == 2:
                note = notes[i].split(' ', 1)[1].strip()
            else:
                raise ValueError('either 1 or 2')
        except IndexError:
            note = ''
        out.append(text)
        out.append(note)

    out = ''.join(out).replace('[', '\n\n[')
    return out


if __name__ == '__main__':
    mode = 1

    p = '/home/helios/Documents/Lotsawa Apprenticeship/BO/G002 བག་མ་གཏོང་བ་ཕྱི་མ།/'
    p = Path(p)
    derge = p / 'G002_num.txt'
    notes = p / 'notes.txt'
    outfile = p / "reinserted.txt"

    derge = derge.read_text()
    derge = derge.split('\n')

    notes_raw = notes.read_text().split('\n')

    out = reinsert_notes(parse_notes(notes_raw), derge, mode=mode)
    outfile.write_text(out)
