"""Boxes 1 to 3 of the workflow: "File Created", "File Updated", "Download File".

The real workflow looks into a Google Drive folder once a minute. Ours looks into the folder company/.
To tell a new file from a changed one, we keep a fingerprint of every file we have seen.
"""
import hashlib
import os

from meter import tokens
from save import save

HERE = os.path.dirname(os.path.abspath(__file__))
FOLDER = os.path.join(HERE, 'company')


def read(name, folder=FOLDER):
    with open(os.path.join(folder, name)) as f:
        return f.read()


def look(folder=FOLDER):
    """One look into the folder: file name -> fingerprint of its text."""
    return {name: hashlib.sha1(read(name, folder).encode()).hexdigest()
            for name in sorted(os.listdir(folder)) if name.endswith('.md')}


def changes(now, seen):
    """Compare this look with the last one. Returns the new files and the changed files."""
    created = [name for name in now if name not in seen]
    updated = [name for name in now if name in seen and now[name] != seen[name]]
    return created, updated


def run():
    seen = {}
    now = look()
    created, updated = changes(now, seen)
    print('first look : %d new files, %d changed' % (len(created), len(updated)))
    rows = []
    for name in created:
        text = read(name)
        rows.append({'name': name, 'chars': len(text), 'tokens': tokens(text)})
        print('  %-20s %5d characters %5d tokens' % (name, len(text), tokens(text)))
    again = changes(look(), now)
    print('second look: %d new files, %d changed' % (len(again[0]), len(again[1])))
    total = sum(r['tokens'] for r in rows)
    print('whole folder: %d characters, %d tokens' % (sum(r['chars'] for r in rows), total))
    save(1, files=rows, chars=sum(r['chars'] for r in rows), tokens=total, second=[len(again[0]), len(again[1])])


if __name__ == '__main__':
    run()
