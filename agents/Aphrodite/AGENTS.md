# Working on this agent

This folder holds a trading agent for Agent Fight Club Market Games. `agent-report.html` explains
its code: the source with the agent loop, context optimization and memory highlighted and commented.

## Keep agent-report.html up to date

- **After every change to the agent's source code**, regenerate `agent-report.html` by following
  `EXPLAIN_CODE.md`. Do it in the same turn as the change, before you tell me the change is done.
- **At the start of a session, before any other work**, check that the report is current:
  recompute the source fingerprint as `EXPLAIN_CODE.md` describes and compare it with the
  `agent-source-sha256` value stored in `agent-report.html`. If they differ, regenerate it first
  and tell me it was out of date — I may have edited the code by hand.
- **No report yet** is how a fresh setup starts: the code is still exactly as Agent Fight Club
  shipped it. Write the first report together with the first change to the code, or when I ask
  for one — not at the start of a session.
- Changes to `.env`, to this file or to `EXPLAIN_CODE.md` do not need a new report.

## Keep the leaderboard reporting working

The agent sends its model, its token total and its cost total to Agent Fight Club
(`POST /market/api/markets/{marketId}/stats`, in `report_usage`). The market leaderboard shows them
next to my result; without them my entry has no model, tokens or cost. Whatever you change in the
code, before you tell me the change is done check that:

- **every model call is counted** in the totals — including calls you add for compaction,
  summaries, retries or sub-agents. If a call uses a different model, its tokens and cost still
  go into the same totals, and the reported model stays the one that drives the main loop;
- **the totals are still sent** after each turn and once more when the run ends, whichever way it
  ends: the model stops, I press Ctrl+C, or the agent crashes;
- a failed report still does not stop the agent, and the last line of a run still says whether the
  usage was reported (a run that made no model call has nothing to report and says nothing).

If I ask for a rewrite that drops this code, or a port to another language, carry the reporting
over.

## Uploading the code report

After my agent wins a run in this market, the leaderboard can link the materials behind the win next
to my result. Whenever you learn of a win — I tell you, or the newest log in `logs/` shows the goal
was reached — offer to upload them, naming the files. Only when I ask you to upload, attach or share
my code report, or say yes to that offer, attach these files to my latest won run in this market:

- `agent-report.html` — the code report.
- `prompt.md` — what the agent was told: the `MODEL` and the `INSTRUCTIONS` from `agent.py`, and
  any other prompt text the code sends to the model (a system prompt, a summary prompt), each under
  a short heading. Write it fresh from the current `agent.py` before every upload.
- `write-up.md` — only if this folder has one (an experiment writes it for the agent that won).

Do it in this order:

1. Check that `agent-report.html` exists and is current, as described above; write or regenerate it
   first if not. Write `prompt.md`.
2. Check that each file — the report, `prompt.md` and `write-up.md` — contains no API key, token or value from `.env`.
   If one does, do not upload; tell me and fix that file.
3. Upload them in one call — each upload replaces all files attached before. This reads `.env`
   without printing it:

```bash
python3 - <<'PY'
import json, os, urllib.error, urllib.request
env = dict(l.strip().split("=", 1) for l in open(".env") if "=" in l and not l.lstrip().startswith("#"))
files = [{"name": "agent-report.html", "content": open("agent-report.html", encoding="utf-8").read()}]
for name in ["prompt.md", "write-up.md"]:
    if os.path.exists(name):
        files.append({"name": name, "content": open(name, encoding="utf-8").read()})
body = json.dumps({"files": files})
request = urllib.request.Request(
    env["AFC_SERVER_URL"] + "/market/api/markets/" + env["AFC_MARKET_ID"]
    + ("/sub-traders/" + env["AFC_SUB_TRADER_ID"] if env.get("AFC_SUB_TRADER_ID") else "") + "/attachments",
    data=body.encode(), method="POST",
    headers={"Authorization": "Bearer " + env["AFC_API_KEY"], "Content-Type": "application/json"},
)
try:
    with urllib.request.urlopen(request) as response:
        print(response.status, response.read().decode())
except urllib.error.HTTPError as error:
    print(error.code, error.read().decode())
PY
```

`200` means the files are attached. `409` means I have not won a run in this market yet — tell me the
files can be uploaded once my agent reaches the goal. Any other status: tell me what it said.

Then tell me that anyone who can see the market leaderboard can open the report and the other files,
and give me the leaderboard link: `<AFC_SERVER_URL>/market/ui/markets/<AFC_MARKET_ID>/leaderboard`,
with the real values filled in. The files belong to my latest win, so after a later win or a code
change I can ask you to upload again.

Do not upload anything unless I ask or say yes, and never upload `.env`, logs or the agent's code
itself.

## The run command

I start the agent myself, in my own terminal. Whenever you give me the command for that, write it
with the absolute path of this folder, in quotes: `cd "<absolute path>" && python3 agent.py`. Never
give me a relative `cd`.

Whenever your message leaves me something to do — run the agent, open a file, make a choice — end
it with an extremely concise summary of those action points, the run command included, one short
line each. Nothing comes after that summary, so I see it without scrolling up.

## Run logs

Every run of the agent writes its full session to a new file in `logs/`. When I ask about a run,
read the newest file there. Logs do not need a new report.

## Secrets

`.env` holds my API keys. Never print it, copy it into another file, or include it in the report.
