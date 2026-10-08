"""Box 6: "Embeddings". Turn a piece of text into a list of numbers, so that a computer can compare texts.

The real workflow rents an embedding model for this. Such a model is trained so that texts with a similar
MEANING get similar numbers, even with no word in common.

Ours is a free stand-in that only counts words. Each word of the documents gets one position in the list.
A rare word counts more than a common one. Two texts are close when they share rare words.
It shows how the search works, and it shows exactly where counting words is not enough.
"""
import math
import re

from save import save
from step2_split import split
from step1_folder import look, read

SKIP = set('a an and are as at be by can do does for from get how i if in is it may me my must of on or '
           'that the them they this to up we what when which who with you your long much many'.split())


def words(text):
    """Lower case, no punctuation, no filler words, and a crude cut of the plural s."""
    found = re.findall(r'[a-z0-9]+', text.lower())
    return [w[:-1] if len(w) > 3 and w.endswith('s') else w for w in found if w not in SKIP]


def rarity(texts):
    """A word that appears in few pieces tells us more. weight = log(pieces / pieces that contain the word)."""
    seen = {}
    for text in texts:
        for w in set(words(text)):
            seen[w] = seen.get(w, 0) + 1
    return {w: math.log(len(texts) / n) + 1 for w, n in seen.items()}


def numbers(text, weight):
    """The list of numbers for one text, kept as word -> number, and scaled to length 1."""
    counts = {}
    for w in words(text):
        if w in weight:
            counts[w] = counts.get(w, 0) + weight[w]
    length = math.sqrt(sum(v * v for v in counts.values())) or 1
    return {w: v / length for w, v in counts.items()}


def closeness(a, b):
    """1 = the same direction, 0 = nothing in common. (The usual name is cosine similarity.)"""
    return sum(v * b.get(w, 0) for w, v in a.items())


def pieces_of_folder():
    return [{'file': name, 'text': text} for name in look() for text in split(read(name))]


def run():
    pieces = pieces_of_folder()
    weight = rarity([p['text'] for p in pieces])
    print('%d pieces, %d different words = %d numbers per piece' % (len(pieces), len(weight), len(weight)))
    out = {}
    for question in ['How many days of holiday do I get?', 'How much vacation do I get?']:
        q = numbers(question, weight)
        scores = sorted(((closeness(q, numbers(p['text'], weight)), i) for i, p in enumerate(pieces)), reverse=True)
        print('\n' + question, '  words kept:', sorted(q))
        for score, i in scores[:4]:
            print('  %.3f  %-20s %s' % (score, pieces[i]['file'], pieces[i]['text'][:40].replace('\n', ' | ')))
        out[question] = {'kept': sorted(q), 'scores': [[round(s, 3), i] for s, i in scores]}
    save(3, words=len(weight), n=len(pieces), q=out,
         rare=sorted(weight, key=weight.get)[-3:], common=sorted(weight, key=weight.get)[:3])


if __name__ == '__main__':
    run()
