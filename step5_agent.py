"""Boxes 9 to 15: chat window, "AI Agent", two "Chat Model" boxes, "Memory", "Vector Store Tool".

How the shipped workflow answers one question:
  call 1  the agent's model reads the question and asks for the tool
          the tool looks up the 4 nearest pieces in the store
  call 2  a second model reads the 4 pieces and writes an answer        (inside the tool)
  call 3  the agent's model reads that answer and replies to the person
The memory keeps the last 5 exchanges and sends them along with every new question.
"""
import json

import model
from save import save
from step4_store import QUESTIONS, fill

REMEMBER = 5        # exchanges; n8n's default for this memory box
AGENT = ('You are a helpful assistant for the staff of a company. Answer questions from the company documents. '
         'Use the tool company_documents_tool to look things up. '
         'If the documents do not hold the answer, say: I cannot find the answer in the available resources.')
READER = ('Use the pieces of company documents below to answer the question at the end. '
          'If the answer is not in the pieces, say: I cannot find the answer in the available resources.')
TOOL = {'type': 'function', 'function': {
    'name': 'company_documents_tool', 'description': 'Retrieve information from any company documents.',
    'parameters': {'type': 'object', 'properties': {'question': {'type': 'string'}}, 'required': ['question']}}}


def pieces_text(found):
    return '\n\n'.join('[%s]\n%s' % (r['file'], r['text']) for _, r in found)


def tool(question, store, log):
    found = store.search(question)
    log['asked'], log['found'] = question, found
    reply = model.chat([{'role': 'system', 'content': READER},
                        {'role': 'user', 'content': pieces_text(found) + '\n\nQuestion: ' + question}])   # call 2
    return reply['content']


def answer(question, memory, store, lookup=tool):
    """One question in, one answer out. memory is the list of earlier messages; it grows by two."""
    log = {}
    messages = [{'role': 'system', 'content': AGENT}] + memory[-2 * REMEMBER:] + [{'role': 'user', 'content': question}]
    reply = model.chat(messages, [TOOL])                                                                    # call 1
    if reply.get('tool_calls'):
        call = reply['tool_calls'][0]
        result = lookup(json.loads(call['function']['arguments'])['question'], store, log)
        messages += [reply, {'role': 'tool', 'tool_call_id': call['id'], 'content': result}]
        reply = model.chat(messages, [TOOL])                                                                # call 3
    memory += [{'role': 'user', 'content': question}, {'role': 'assistant', 'content': reply['content']}]
    return reply['content'], log


TALK = [QUESTIONS[0][0], 'And if I work part time?'] + [q[0] for q in QUESTIONS[1:]]


def run():
    store, memory, rows = fill(), [], []
    for question in TALK:
        start = len(model.CALLS)
        text, log = answer(question, memory, store)
        calls, t_in, t_out = model.used(start)
        each = [c['in'] for c in model.CALLS[start:]]
        print('\nQ: %s' % question)
        if log['asked'] != question:
            print('   the agent asked the tool: %s' % log['asked'])
        print('A: %s' % text)
        print('   %d calls, tokens in %s = %d, tokens out %d' % (calls, each, t_in, t_out))
        rows.append({'q': question, 'asked': log['asked'], 'a': text, 'calls': calls, 'each': each,
                     'in': t_in, 'out': t_out})
    total_in, total_out = sum(r['in'] for r in rows), sum(r['out'] for r in rows)
    print('\n%d questions, %d calls, %d tokens in, %d tokens out' % (len(rows), len(model.CALLS), total_in, total_out))
    print('per question: %d tokens in, %d out' % (total_in / len(rows), total_out / len(rows)))
    save(5, rows=rows, calls=len(model.CALLS), tokens_in=total_in, tokens_out=total_out,
         mean_in=round(total_in / len(rows)), mean_out=round(total_out / len(rows)), remember=REMEMBER)


if __name__ == '__main__':
    run()
