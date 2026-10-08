"""Boxes 4 and 5: "Data Loader" and "Recursive Character Text Splitter".

A document is cut into pieces of at most 1,000 characters. The template sets an overlap of 100 characters.
The rule (the same as in the LangChain library that n8n uses): cut at blank lines first. Only if a part is
still too long, cut it at line ends, then at spaces. Then glue neighbours together while they still fit.
The overlap is made of whole parts: the end of one piece is repeated in the next only if a part fits in 100.
"""
from save import save
from step1_folder import look, read

SIZE, OVERLAP = 1000, 100
CUTS = ['\n\n', '\n', ' ', '']


def glue(parts, cut, size, overlap):
    pieces, now, total = [], [], 0
    for part in parts:
        if now and total + len(part) + len(cut) > size:
            pieces.append(cut.join(now).strip())
            while total > overlap or (total > 0 and total + len(part) + (len(cut) if now else 0) > size):
                total -= len(now.pop(0)) + (len(cut) if now else 0)
        now.append(part)
        total += len(part) + (len(cut) if len(now) > 1 else 0)
    pieces.append(cut.join(now).strip())
    return [p for p in pieces if p]


def split(text, size=SIZE, overlap=OVERLAP, cuts=CUTS):
    cut, finer = '', []
    for i, c in enumerate(cuts):
        if c == '' or c in text:
            cut, finer = c, cuts[i + 1:]
            break
    parts = text.split(cut) if cut else list(text)
    pieces, short = [], []
    for part in parts:
        if len(part) < size:
            short.append(part)
            continue
        pieces += glue(short, cut, size, overlap) if short else []
        short = []
        pieces += split(part, size, overlap, finer) if finer else [part]
    return pieces + (glue(short, cut, size, overlap) if short else [])


def shared(a, b):
    """How many characters at the end of piece a come back at the start of piece b."""
    return max([n for n in range(1, min(len(a), len(b)) + 1) if a[-n:] == b[:n]], default=0)


def run():
    pieces = []
    for name in look():
        for text in split(read(name)):
            pieces.append({'file': name, 'text': text})
    sizes = [len(p['text']) for p in pieces]
    print('%d files -> %d pieces, from %d to %d characters' % (len(look()), len(pieces), min(sizes), max(sizes)))
    for p in pieces:
        print('  %-20s %4d  %s' % (p['file'], len(p['text']), p['text'][:48].replace('\n', ' | ')))
    repeats = [shared(a['text'], b['text']) for a, b in zip(pieces, pieces[1:]) if a['file'] == b['file']]
    print('characters repeated between neighbours:', repeats)

    # The same handbook as it comes out of many PDF files: one block, with no blank lines.
    block = ' '.join(read('handbook.md').split())
    cut_up = split(block)
    over = [shared(a, b) for a, b in zip(cut_up, cut_up[1:])]
    print('handbook without blank lines -> %d pieces, repeated characters: %s' % (len(cut_up), over))
    print('  piece 1 ends  : ...%s' % cut_up[0][-70:])
    print('  piece 2 starts: %s...' % cut_up[1][:150])
    save(2, n=len(pieces), sizes=sizes, files=[p['file'] for p in pieces], heads=[p['text'][:60] for p in pieces],
         repeats=repeats, block_n=len(cut_up), block_over=over, end1=cut_up[0][-70:], start2=cut_up[1][:150],
         block_sizes=[len(c) for c in cut_up])


if __name__ == '__main__':
    run()
