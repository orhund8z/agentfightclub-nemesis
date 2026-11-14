# Explain my agent's code — write an annotated HTML report

You are my coding agent. I have an AI agent in the current folder that trades in an Agent Fight Club
market through its API. Read its code and write a report that shows me how it works: the code
itself, with the parts that matter highlighted and briefly explained.

This is a read-only job. **Do not change, reformat or run the agent's code.** The only file you
create is the report.

## Step 1 — Find the agent

Look in the current folder for the agent's source. A starter agent from Agent Fight Club is a single
`agent.py`, but I may have rewritten it, split it into several files, or used another language.
Read every source file that is part of the agent. Skip dependencies, virtualenvs, build output,
logs and `.env`.

If you cannot tell which files make up the agent, or the folder holds no agent, **stop and ask me**.

Never read out, copy or include the contents of `.env` or any API key you come across. If a key is
hard-coded in the source, replace it with `<redacted>` in the report and tell me about it.

## Step 2 — Find these aspects in the code

For each aspect, find the exact lines that implement it. An aspect may be spread over several
places, and one line may belong to more than one aspect.

1. **Agent loop** — the core construction of the agent. Mark only these lines, and only inside the
   loop's own body:
   - the loop start — the `for` / `while` (or equivalent) statement;
   - the call that sends the message history to the model and gets its response;
   - the line that appends the model's response message to the message history;
   - the line that takes the tool calls out of that response;
   - the call that runs each tool;
   - the line that appends the tool result to the message history.

   Mark the call site in the loop, not the function behind it: do not highlight the bodies of
   helpers such as the model client, the tool dispatcher or the tools themselves, and do not
   highlight logging, usage reporting, argument parsing, error handling or end conditions as part
   of this aspect.
2. **Context optimization** — anything that keeps the model's context small or relevant:
   - context compaction (summarising or dropping old turns);
   - tool-result trimming (truncating or filtering what a tool returns before the model sees it);
   - tool-definition optimization (how many tools, how long their descriptions and schemas are,
     whether they are selected per turn);
   - RAG and search (retrieving only the relevant pieces of the log, documents or memory).
3. **Memory** — anything that survives beyond the message list: notes kept during a run, state
   saved to disk, anything loaded from a previous run.

**Report only what the code does.** Leave out any aspect or sub-aspect the code does not implement:
do not list it, mark it "not present", explain what its absence costs, or suggest adding it. Finding
what is missing is up to me. Do not invent an implementation, and do not stretch unrelated code to
fit an aspect.

## Step 3 — Write the report

Write one self-contained file, `agent-report.html`, in the current folder. It must open correctly
from disk with no network access: all CSS and any JavaScript inline in this one file, no CDN links,
no external fonts or images.

Contents, in this order:

1. **Header** — the agent's folder name, the files covered, the date, and the source fingerprint
   (see below).
2. **Summary** — one short paragraph on how the agent works, then a table with one row per aspect
   and sub-aspect from Step 2 that the code implements, with a one-line note on how.
3. **Legend** — one colour per aspect the code implements (from agent loop, context optimization,
   memory). Each legend entry toggles that aspect's highlighting on and off.
4. **The code** — every agent source file in full, with line numbers, in a monospace block:
   - highlight the lines that belong to an aspect with that aspect's background colour; lines that
     belong to two aspects must show both (for example a second-colour left border);
   - beside or directly above each highlighted region, put a **concise comment** — one or two
     sentences saying what this code does for the aspect and, where it matters, why. Comment only
     where it helps; do not paraphrase code that is self-explanatory;
   - the code must be exactly what is in the files — HTML-escaped, otherwise unchanged. Your comments
     must be visually distinct from the code and never be inserted into it as source comments.

**Source fingerprint.** So that anyone can later tell whether the report still matches the code,
compute a SHA-256 over the agent's source files, concatenated in the order you list them in the
header, and store it in the report's `<head>`:

```html
<meta name="agent-source-files" content="agent.py">
<meta name="agent-source-sha256" content="<the hash>">
```

List several files comma-separated, in the order they were hashed. With Python available:

```bash
python3 -c "import hashlib,sys; print(hashlib.sha256(b''.join(open(f,'rb').read() for f in sys.argv[1:])).hexdigest())" agent.py
```

If `agent-report.html` already exists, replace it completely — do not patch the old one.

Keep it readable: sufficient contrast for the highlight colours in both light and dark colour
schemes, a layout that works on a laptop screen, long lines scroll horizontally and do not wrap
mid-token.

## Step 4 — Check and hand over

- Every line number and code line in the report matches the source files.
- Every row of the summary table agrees with what is highlighted in the code.
- Nothing in the report names an aspect the code lacks or suggests what to add.
- No API key or `.env` content appears anywhere in the report.
- The stored fingerprint matches a fresh computation over the listed files.

Then tell me where the report is and how to open it (for example `open agent-report.html` on macOS,
`xdg-open agent-report.html` on Linux, `start agent-report.html` on Windows), and give me the
summary table in your message. Then stop — do not start changing the agent unless I ask.
