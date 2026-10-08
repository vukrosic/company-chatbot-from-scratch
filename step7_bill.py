"""The bill. Three ways to answer the same questions, measured in tokens, then priced from the public list.

  shipped      3 calls per question (agent, reader inside the tool, agent again)
  two calls    the tool hands the 4 pieces straight to the agent; no second model
               (n8n's vector store boxes have a mode for this: "Retrieve Documents (As Tool for AI Agent)")
  whole folder no search at all: every question carries every document

Prices are in prices.json, read from the provider's own page. No call in this file costs anything.
"""
import model
from meter import dollars, load_prices
from save import save
from step1_folder import look, read
from step4_store import QUESTIONS, fill
from step5_agent import READER, answer, pieces_text

STAFF, PER_DAY, DAYS = 60, 2, 22            # 60 people, 2 questions each per working day, 22 working days
MONTH = STAFF * PER_DAY * DAYS


def direct(question, store, log):
    found = store.search(question)
    log['asked'], log['found'] = question, found
    return pieces_text(found)


def whole_folder(question, folder):
    reply = model.chat([{'role': 'system', 'content': READER},
                        {'role': 'user', 'content': folder + '\n\nQuestion: ' + question}])
    return reply['content']


def measure(ask):
    start = len(model.CALLS)
    answers = [ask(q[0]) for q in QUESTIONS]
    calls, t_in, t_out = model.used(start)
    n = len(QUESTIONS)
    return {'calls': calls / n, 'in': t_in / n, 'out': t_out / n, 'answers': answers}


def run():
    store = fill()
    folder = '\n\n'.join('[%s]\n%s' % (name, read(name)) for name in look())
    ways = {'shipped': measure(lambda q: answer(q, [], store)[0]),
            'two calls': measure(lambda q: answer(q, [], store, direct)[0]),
            'whole folder': measure(lambda q: whole_folder(q, folder))}
    prices = {m['id']: m for m in load_prices()['models']}
    print('%d staff x %d questions a day x %d days = %d questions a month\n' % (STAFF, PER_DAY, DAYS, MONTH))
    print('%-13s %5s %9s %10s' % ('per question', 'calls', 'tokens in', 'tokens out') + ''.join('%14s' % m for m in prices))
    table = {}
    for name, w in ways.items():
        cost = {m: dollars(w['in'], w['out'], p) for m, p in prices.items()}
        table[name] = {'calls': w['calls'], 'in': round(w['in']), 'out': round(w['out']),
                       'cents': {m: round(c * 100, 4) for m, c in cost.items()},
                       'month': {m: round(c * MONTH, 2) for m, c in cost.items()}}
        print('%-13s %5.0f %9.0f %10.0f' % (name, w['calls'], w['in'], w['out'])
              + ''.join('  $%.2f a month' % (c * MONTH) for c in cost.values()))
    same = all(ways['shipped']['answers'] == w['answers'] for w in ways.values())
    print('\nall three ways gave the same %d answers: %s' % (len(QUESTIONS), same))

    # What happens when the folder grows? Search keeps sending 4 pieces. "Whole folder" sends everything.
    base = ways['whole folder']
    folder_tokens = round(base['in'])
    grow = []
    print('\nfolder size      whole folder, per month           search (two calls), per month')
    for times in (1, 10, 100):
        t_in = base['in'] * times
        row = {'times': times, 'tokens': round(t_in)}
        for m, p in prices.items():
            row[m] = round(dollars(t_in, base['out'], p) * MONTH, 2)
            row[m + ' fits'] = t_in <= p['context']
        row['search'] = table['two calls']['month']
        grow.append(row)
        print('x%-4d %9d tokens  ' % (times, t_in) + '  '.join(
            '%s $%.2f%s' % (m, row[m], '' if row[m + ' fits'] else ' (does not fit)') for m in prices)
            + '   ' + '  '.join('$%.2f' % v for v in row['search'].values()))
    longer = {m: round(dollars(ways['shipped']['in'], ways['shipped']['out'] * 3, p) * MONTH, 2) for m, p in prices.items()}
    print('\nshipped way, if every reply were 3 times longer:', longer)
    save(7, staff=STAFF, per_day=PER_DAY, days=DAYS, month=MONTH, ways=table, same=same, grow=grow, longer=longer,
         prices=prices, folder_tokens=folder_tokens)


if __name__ == '__main__':
    run()
