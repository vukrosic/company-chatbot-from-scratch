"""Counting tokens and money without calling anyone.

A token is a piece of text, about three quarters of an English word. Models are billed per token.
Tokens are counted here with tiktoken (the open tokenizer cl100k_base). Every provider counts in its own way;
a real API reports its own exact count in each reply. Without tiktoken installed, the count is characters / 4.
"""
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
if os.path.isdir(os.path.join(HERE, '.tok')):
    os.environ.setdefault('TIKTOKEN_CACHE_DIR', os.path.join(HERE, '.tok'))

try:
    import tiktoken
    _enc = tiktoken.get_encoding('cl100k_base')
    EXACT = True

    def tokens(text):
        return len(_enc.encode(text))
except Exception:                                       # no tiktoken, or no way to fetch its word list
    EXACT = False

    def tokens(text):
        return (len(text) + 3) // 4


def load_prices():
    with open(os.path.join(HERE, 'prices.json')) as f:
        return json.load(f)


def dollars(tokens_in, tokens_out, price):
    """Price lists are in dollars per million tokens: one price for text sent in, one for text that comes out."""
    return (tokens_in * price['in'] + tokens_out * price['out']) / 1e6
