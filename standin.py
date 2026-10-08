"""A stand-in for the rented model. It runs on this computer and answers in the same form as a real one.

It is not intelligent. It follows three rules:
  1. It was offered a tool and got a question  -> it asks for the tool, with the question.
  2. It was handed pieces of text and a question -> it copies out the one sentence that shares the most
     words with the question. If no sentence shares two words, it says it cannot find the answer.
  3. It got the tool's result back             -> it passes the result on as its answer
     (or, if the result is raw pieces of text, it applies rule 2 to them).
Two replies are written by hand, and marked below. One of them is wrong on purpose, to test our checks.
"""
import json
import re
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

from meter import tokens
from step3_numbers import words

CANNOT = 'I cannot find the answer in the available resources.'

# Hand-written: a real model reads the earlier messages and turns a short follow-up into a full question.
FOLLOW_UPS = {'And if I work part time?': 'How many days of holiday do part-time staff get?'}
# Hand-written and WRONG on purpose: the documents say one year. A real model can make this kind of mistake.
MADE_UP = {'How long is the warranty on a battery?': 'Batteries have a warranty of two years.'}


def sentences(text):
    lines = [line for line in text.split('\n') if line.strip() and line[0] not in '#[']
    return [s.strip() for line in lines for s in re.split(r'(?<=[.?!])\s+', line) if s.strip()]


def best_sentence(pieces, question):
    asked = set(words(question))
    best, most = None, 1
    for s in sentences(pieces):
        shared = len(asked & set(words(s)))
        if shared > most:
            best, most = s, shared
    return best


def reply(body):
    messages = body['messages']
    last = messages[-1]
    if body.get('tools'):
        if last['role'] == 'tool':                                   # rule 3
            if last['content'].startswith('['):                      # the tool handed over raw pieces: rule 2
                asked = json.loads(messages[-2]['tool_calls'][0]['function']['arguments'])['question']
                return {'role': 'assistant', 'content': best_sentence(last['content'], asked) or CANNOT}
            return {'role': 'assistant', 'content': last['content']}
        question = FOLLOW_UPS.get(last['content'], last['content'])  # rule 1
        name = body['tools'][0]['function']['name']
        return {'role': 'assistant', 'content': '', 'tool_calls': [
            {'id': 'call_1', 'type': 'function',
             'function': {'name': name, 'arguments': json.dumps({'question': question})}}]}
    pieces, _, question = last['content'].rpartition('Question: ')   # rule 2
    question = question.strip()
    found = MADE_UP.get(question) or best_sentence(pieces, question)
    if 'JSON' in messages[0]['content']:
        return {'role': 'assistant', 'content': json.dumps({'answer': found or CANNOT, 'quote': found or ''})}
    return {'role': 'assistant', 'content': found or CANNOT}


class Handler(BaseHTTPRequestHandler):
    def do_POST(self):
        body = json.loads(self.rfile.read(int(self.headers['Content-Length'])))
        message = reply(body)
        sent = ''.join(m.get('content') or '' for m in body['messages']) + json.dumps(body.get('tools') or '')
        out = (message.get('content') or '') + json.dumps(message.get('tool_calls') or '')
        answer = {'choices': [{'message': message}],
                  'usage': {'prompt_tokens': tokens(sent), 'completion_tokens': tokens(out)}}
        data = json.dumps(answer).encode()
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Content-Length', str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def log_message(self, *args):
        pass


def start():
    server = HTTPServer(('127.0.0.1', 0), Handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    return 'http://127.0.0.1:%d/v1/chat/completions' % server.server_port
