"""The "Chat Model" box: send a conversation to a language model over the web, get its reply back.

    export MOONSHOT_API_KEY=...     # with a key, chat() calls the rented model (this costs money)

The address below is Kimi's. Most providers accept the same form of request, so to use another model
you change AI_URL and AI_MODEL, and nothing else in this folder.

Without a key, chat() talks to standin.py on this computer. The stand-in answers in the same form,
by simple rules. So every program here runs for free, with no account.
"""
import json
import os
import urllib.request

URL = os.environ.get('AI_URL', 'https://api.moonshot.ai/v1/chat/completions')
MODEL = os.environ.get('AI_MODEL', 'kimi-k2.6')
KEY = os.environ.get('MOONSHOT_API_KEY')
CALLS = []                      # one entry per call: tokens sent in, tokens that came out
_local = None


def chat(messages, tools=None):
    """messages = the conversation so far. tools = what the model may ask us to run. Returns its reply message."""
    global _local
    url, key = URL, KEY
    if not key:
        if _local is None:
            import standin
            _local = standin.start()
        url, key = _local, 'local'
    body = {'model': MODEL, 'messages': messages}
    if tools:
        body['tools'] = tools
    request = urllib.request.Request(url, json.dumps(body).encode(),
                                     {'Content-Type': 'application/json', 'Authorization': 'Bearer ' + key})
    with urllib.request.urlopen(request, timeout=120) as response:
        answer = json.load(response)
    CALLS.append({'in': answer['usage']['prompt_tokens'], 'out': answer['usage']['completion_tokens']})
    return answer['choices'][0]['message']


def used(since=0):
    """Calls, tokens in and tokens out for the calls made after call number `since`."""
    part = CALLS[since:]
    return len(part), sum(c['in'] for c in part), sum(c['out'] for c in part)
