# Company chatbot from scratch

Code for the video **A Company Chatbot Template Has 345,000 Views. I Rebuilt It and Found 3 Holes.**

The n8n template [RAG chatbot for company documents](https://n8n.io/workflows/2753-rag-chatbot-for-company-documents-using-google-drive-and-gemini/) is a workflow of 15 boxes: it
watches a shared folder, cuts each document into pieces, stores them in a table, and lets staff ask questions in a
chat window. This folder rebuilds those 15 boxes in seven small Python programs, runs three tests on the result,
and adds up the monthly bill. Python 3, standard library only. `tiktoken` is optional: with it the token counts are
exact for the `cl100k_base` word list, without it they are estimated as characters / 4.

```bash
./run_all.sh          # the seven steps and 14 checks, a few seconds; expected output is in demo-output.txt
```

**Nothing here calls a real model or costs money.** The chat model and the "numbers" (embedding) box are played by
`standin.py`, a small rule-following program on your own computer that answers in the same form as a rented model.
So the files, the cuts, the table, the three tests, the token counts and the price arithmetic are real; how well a
real model answers is not measured here. n8n itself was not run: the template and the n8n source were read.

| File | Boxes of the workflow | What the run shows |
| --- | --- | --- |
| `step1_folder.py` | File Created, File Updated, Download File | 6 files in `company/`: 9,559 characters, 2,152 tokens. A second look finds 0 new, 0 changed. |
| `step2_split.py` | Data Loader, Text Splitter | 6 files become 13 pieces of 260 to 994 characters. The 100-character overlap only appears when a file has no blank lines. |
| `step3_numbers.py` | Embeddings | Each piece becomes 461 numbers. "holiday" finds the handbook (0.376); "vacation" finds nothing (0.000), because the stand-in compares words, not meaning. |
| `step4_store.py` | Vector Store (save, search) | 13 rows. For 5 of 6 test questions the right piece is at place 1; the sixth (a dog in the office) is not in any file. |
| `step5_agent.py` | Chat, AI Agent, 2 Chat Models, Memory, Documents Tool | 7 questions = 21 calls, 8,133 tokens sent, 581 written back. 3 calls per question. |
| `step6_trust.py` | (three tests, three repairs) | See below. |
| `step7_bill.py` | (the bill) | 60 staff x 2 questions x 22 days = 2,640 questions a month, priced from `prices.json`. |

## The three tests

| Test | As shipped | Repair |
| --- | --- | --- |
| A file changes (holiday goes from 25 to 28 days) | Rows go 13 -> 16. Nothing deletes the old rows, so the model receives both rules. | Delete the file's old rows before saving the new ones (2 lines). Rows stay at 13. |
| A made-up answer ("Batteries have a warranty of two years") | It reaches the employee. Nothing compares the answer with the documents. | The model must return a quote; plain code checks that the quote is in one of the pieces. 5 answers pass with a source, the made-up one is stopped. |
| A private file (`pay-bands.md`) lands in the folder | Anyone who asks gets the pay figures. The table has no column for who may read a row. | Each row gets a list of readers; the search skips rows this person may not read. |

## The bill

List prices read on 2026-10-08 are in `prices.json` (US dollars per million tokens). Put your own model's two prices
there to price it.

| Per question | Calls | Tokens sent | Tokens written | Month at $0.95 / $4.00 | Month at $3.00 / $15.00 |
| --- | --- | --- | --- | --- | --- |
| As shipped | 3 | 1,009 | 81 | $3.38 | $11.19 |
| Two calls (the tool hands the pieces straight to the agent) | 2 | 944 | 63 | $3.03 | $9.98 |
| Send the whole folder, no search | 1 | 2,226 | 18 | $5.77 | $18.33 |

With a folder 100 times larger, sending everything costs $558.59 a month at the lower price; the search still sends
4 pieces and stays at $3.03. With replies 3 times longer, the shipped design costs $5.09 instead of $3.38.

## Use it with your own documents, or a real model

Put your own `.md` files into `company/` and run the steps again. `step3_numbers.py` matches words, not meaning, so
ask with words that are in your documents.

`model.py` sends a standard chat-completions request. Without a key it talks to `standin.py`. With a key it calls a
rented model, which costs money:

```bash
export MOONSHOT_API_KEY=your-key                     # default address and model: Kimi K2.6
export AI_URL=https://api.example.com/v1/chat/completions AI_MODEL=some-model   # or any other provider
```

The run with a real model was not made for the video, so its answers and its exact token counts are untested here.

`meter.py` counts tokens and prices a run. `tests.py` holds the 14 checks. MIT licence.
