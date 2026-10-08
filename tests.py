"""Checks. Each one states a claim from the video and fails loudly if the code stops agreeing with it."""
import step1_folder
import step2_split
import step3_numbers
import step4_store
import step5_agent
import step6_trust
import step7_bill
import model

done = 0


def check(name, ok):
    global done
    assert ok, 'FAILED: ' + name
    done += 1
    print('ok  ' + name)


now = step1_folder.look()
check('a second look into an unchanged folder finds nothing new', step1_folder.changes(now, now) == ([], []))
changed = dict(now, **{'handbook.md': 'x'})
check('a changed file is reported as updated, not as new', step1_folder.changes(changed, now) == ([], ['handbook.md']))

pieces = step3_numbers.pieces_of_folder()
check('no piece is longer than 1,000 characters', max(len(p['text']) for p in pieces) <= 1000)
block = ' '.join(step1_folder.read('handbook.md').split())
cut = step2_split.split(block)
check('text without blank lines gets an overlap of at most 100 characters',
      all(0 < step2_split.shared(a, b) <= 100 for a, b in zip(cut, cut[1:])))
check('every word of the block survives the cut', set(block.split()) == set(' '.join(cut).split()))

weight = step3_numbers.rarity([p['text'] for p in pieces])
check('a text is as close as possible to itself',
      abs(step3_numbers.closeness(*[step3_numbers.numbers(pieces[0]['text'], weight)] * 2) - 1) < 1e-9)
check('a word that is not in the documents gives no numbers', step3_numbers.numbers('vacation', weight) == {})

store = step4_store.fill()
check('the search always returns 4 rows', all(len(store.search(q[0])) == 4 for q in step4_store.QUESTIONS))
check('the right piece is first for the 5 questions that have an answer',
      all(q[2] in store.search(q[0])[0][1]['text'] for q in step4_store.QUESTIONS if q[2]))

start = len(model.CALLS)
text, _ = step5_agent.answer('Who may drive a forklift?', [], store)
check('the shipped design makes 3 model calls for one question', model.used(start)[0] == 3)
memory = []
for i in range(8):
    step5_agent.answer('When does my pay arrive?', memory, store)
sent = len([1 for m in memory[-2 * step5_agent.REMEMBER:]])
check('the memory sends at most 5 exchanges along', sent == 10 and len(memory) == 16)

docs = {name: step1_folder.read(name) for name in now}
flagged = []
out, _ = step5_agent.answer('How long is the warranty on a battery?', [], store, step6_trust.careful(flagged=flagged))
check('a made-up answer is stopped by the quote check', out == step6_trust.CANNOT and len(flagged) == 1)
private = step6_trust.build(dict(docs, **{'pay-bands.md': step6_trust.PAY}), {'pay-bands.md': ['hr']})
check('a reader without permission never gets a private piece',
      all(r['file'] != 'pay-bands.md' for _, r in private.search('salary band of a team leader', reader='warehouse')))
check('the month has 2,640 questions', step7_bill.MONTH == 2640)
print('\n%d checks passed' % done)
