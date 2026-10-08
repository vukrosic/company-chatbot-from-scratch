"""Three tests of the workflow as it ships, and a small repair for each.

  1. A document is updated.          Shipped: the new pieces are added, the old ones stay.
  2. The model makes something up.   Shipped: nothing checks the answer against the documents.
  3. A private file lands in the folder. Shipped: every employee's question searches every file.
"""
import json

import model
from save import save
from step1_folder import look, read
from step2_split import split
from step3_numbers import rarity
from step4_store import QUESTIONS, Store
from step5_agent import answer, pieces_text, tool

PAY = ('# Harlow Tools pay bands (HR only)\n\n## Bands\nThe salary band of a counter assistant is 31,000 to 36,000 '
       'dollars a year. The salary band of a team leader is 46,000 to 54,000 dollars a year. '
       'The salary band of a department head is 68,000 to 82,000 dollars a year.')
PROOF = ('Use the pieces of company documents below to answer the question at the end. Reply in JSON with two fields: '
         '"answer", and "quote", one sentence copied word for word from the pieces that proves the answer. '
         'If the answer is not in the pieces, leave the quote empty.')
CANNOT = 'I cannot find the answer in the available resources.'


def build(docs, readers=None):
    """docs = file name -> text. Returns a filled store."""
    cut = {name: split(text) for name, text in docs.items()}
    store = Store(rarity([p for pieces in cut.values() for p in pieces]))
    for name, pieces in cut.items():
        store.insert(name, pieces, (readers or {}).get(name))
    return store


def careful(reader=None, flagged=None):
    """A tool that demands a quote, and checks that the quote really stands in the pieces it sent."""
    def lookup(question, store, log):
        found = store.search(question, reader=reader)
        log['asked'], log['found'] = question, found
        reply = model.chat([{'role': 'system', 'content': PROOF},
                            {'role': 'user', 'content': pieces_text(found) + '\n\nQuestion: ' + question}])
        try:
            form = json.loads(reply['content'])
        except ValueError:
            form = {}
        quote = ' '.join(str(form.get('quote', '')).split())
        home = [r['file'] for _, r in found if quote and quote in ' '.join(r['text'].split())]
        if not home:
            if quote and flagged is not None:
                flagged.append({'q': question, 'claimed': quote})
            return CANNOT
        return '%s (source: %s)' % (form['answer'], home[0])
    return lookup


def test_update(docs):
    question = QUESTIONS[0][0]
    new = docs['handbook.md'].replace('25 days', '28 days').replace('twelve and a half', 'fourteen')
    shipped = build(docs)
    before = len(shipped.rows)
    shipped.insert('handbook.md', split(new))                    # what the "File Updated" path does
    got = [('28 days' in r['text'], '25 days' in r['text']) for _, r in shipped.search(question)]
    fixed = build(docs)
    fixed.delete('handbook.md')                                  # the repair: one line
    fixed.insert('handbook.md', split(new))
    got_fixed = [('28 days' in r['text'], '25 days' in r['text']) for _, r in fixed.search(question)]
    said, _ = answer(question, [], shipped)
    said_fixed, _ = answer(question, [], fixed)
    out = {'before': before, 'shipped_rows': len(shipped.rows), 'fixed_rows': len(fixed.rows),
           'shipped_new': sum(a for a, _ in got), 'shipped_old': sum(b for _, b in got),
           'fixed_new': sum(a for a, _ in got_fixed), 'fixed_old': sum(b for _, b in got_fixed),
           'said': said, 'said_fixed': said_fixed}
    print('1. UPDATE  rows: %d -> %d shipped, %d repaired' % (before, out['shipped_rows'], out['fixed_rows']))
    print('   shipped : the model receives %d piece with the new rule and %d with the old rule' % (out['shipped_new'], out['shipped_old']))
    print('             stand-in said: %s' % said)
    print('   repaired: %d new, %d old. stand-in said: %s' % (out['fixed_new'], out['fixed_old'], said_fixed))
    return out


def test_proof(docs):
    store, flagged, rows = build(docs), [], []
    questions = [q[0] for q in QUESTIONS] + ['How long is the warranty on a battery?']
    for question in questions:
        plain, _ = answer(question, [], store)
        checked, _ = answer(question, [], store, careful(flagged=flagged))
        rows.append({'q': question, 'plain': plain, 'checked': checked})
    right = sum(1 for r, q in zip(rows, QUESTIONS) if q[2] and q[2] in r['checked'])
    print('2. PROOF   %d questions. With the quote check: %d answered with a source, %d stopped.' % (
        len(rows), sum('source:' in r['checked'] for r in rows), len(flagged)))
    print('   shipped : %s -> %s' % (rows[-1]['q'], rows[-1]['plain']))
    print('   repaired: %s -> %s' % (rows[-1]['q'], rows[-1]['checked']))
    print('             stopped because this sentence is not in the documents: "%s"' % flagged[0]['claimed'])
    for r in rows[:-1]:
        print('   %-42s %s' % (r['q'], r['checked'][:90]))
    return {'rows': rows, 'flagged': flagged, 'right': right, 'with_source': sum('source:' in r['checked'] for r in rows)}


def test_private(docs):
    question = 'What is the salary band of a team leader?'
    docs = dict(docs, **{'pay-bands.md': PAY})
    shipped = build(docs)
    said, log = answer(question, [], shipped)
    fixed = build(docs, readers={'pay-bands.md': ['hr']})
    staff, log_staff = answer(question, [], fixed, careful(reader='warehouse'))
    hr, _ = answer(question, [], fixed, careful(reader='hr'))
    out = {'q': question, 'shipped': said, 'shipped_files': [r['file'] for _, r in log['found']],
           'staff': staff, 'staff_files': [r['file'] for _, r in log_staff['found']], 'hr': hr}
    print('3. PRIVATE %s' % question)
    print('   shipped, anyone asks   : %s' % said)
    print('   repaired, warehouse    : %s   (pieces searched from: %s)' % (staff, ', '.join(sorted(set(out['staff_files'])))))
    print('   repaired, HR           : %s' % hr)
    return out


def run():
    docs = {name: read(name) for name in look()}
    start = len(model.CALLS)
    out = {'update': test_update(docs), 'proof': test_proof(docs), 'private': test_private(docs)}
    save(6, calls=len(model.CALLS) - start, **out)


if __name__ == '__main__':
    run()
