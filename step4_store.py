"""Boxes 7 and 8: the "Vector Store". A table with one row per piece: its numbers, its text, its file.

The real workflow rents this table from a service called Pinecone. The idea fits in one small class:
insert rows, and search for the rows whose numbers are closest to the numbers of a question.
The search always returns the nearest k rows, however far away they are. n8n's default is k = 4.
"""
from save import save
from step3_numbers import closeness, numbers, pieces_of_folder, rarity

K = 4
QUESTIONS = [['How many days of holiday do I get?', 'handbook.md', '25 days'],
             ['How long is the warranty on power tools?', 'customers.md', 'three years'],
             ['Who may drive a forklift?', 'warehouse-safety.md', 'forklift licence'],
             ['What do I do if my laptop is stolen?', 'it-guide.md', 'within one hour'],
             ['When does my pay arrive?', 'handbook.md', 'last working day'],
             ['Can I bring my dog to the office?', None, None]]


class Store:
    def __init__(self, weight):
        self.weight = weight        # the word weights, fixed when the store is set up
        self.rows = []

    def insert(self, file, texts, readers=None):
        for text in texts:
            self.rows.append({'file': file, 'text': text, 'numbers': numbers(text, self.weight),
                              'readers': readers})

    def delete(self, file):
        self.rows = [r for r in self.rows if r['file'] != file]

    def search(self, question, k=K, reader=None):
        """The k nearest rows. With a reader, rows that this person may not read are skipped."""
        q = numbers(question, self.weight)
        rows = [r for r in self.rows if reader is None or not r['readers'] or reader in r['readers']]
        ranked = sorted(rows, key=lambda r: closeness(q, r['numbers']), reverse=True)
        return [(round(closeness(q, r['numbers']), 3), r) for r in ranked[:k]]


def fill():
    pieces = pieces_of_folder()
    store = Store(rarity([p['text'] for p in pieces]))
    for p in pieces:
        store.insert(p['file'], [p['text']])
    return store


def run():
    store = fill()
    print('%d rows in the store' % len(store.rows))
    out = []
    for question, file, proof in QUESTIONS:
        found = store.search(question)
        place = [i for i, (_, r) in enumerate(found) if proof and proof in r['text']]
        sent = sum(len(r['text']) for _, r in found)
        print('\n%s' % question)
        for score, r in found:
            print('  %.3f  %-20s %s' % (score, r['file'], r['text'][:40].replace('\n', ' | ')))
        print('  -> right piece at place %s, %d characters go to the model' % (place[0] + 1 if place else '-', sent))
        out.append({'q': question, 'scores': [s for s, _ in found], 'files': [r['file'] for _, r in found],
                    'heads': [r['text'][:40] for _, r in found], 'place': place[0] + 1 if place else 0, 'chars': sent})
    save(4, rows=len(store.rows), k=K, q=out)


if __name__ == '__main__':
    run()
