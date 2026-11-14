# agentfightclub-nemesis

An experiment with LLM trading agents on [Agent Fight Club](https://agentfightclub.today/): we ran **15 agents (5 strategies × 3 models)** against each other in a Market Game, picked the most promising one, **Nemesis**, and sent it alone into the shared final competition.

It was built at the **AI Agents Munich** meetup, [*Live building of agents s02e02: "Let's practice multi-agent systems!"*](https://www.meetup.com/ai-agents-munich/events/317090453/) (Saturday 14 November 2026, 10:00–13:00 CET, commercetools, Munich). The session is hands-on: you build, run and tweak agents, then combine them into teams. The platform's own reference is in [agent-fight-club-docs](https://github.com/ivpdev/agent-fight-club-docs/tree/main).

## Background

- **Agent Fight Club** is a competition platform with two kinds of games: Escape Games and **Market Games**. In a Market Game, traders negotiate in a shared log, post offers and exchange goods. See the [docs repo](https://github.com/ivpdev/agent-fight-club-docs/tree/main) (including `market-games/`) for the full rules.
- A trader's **goal** in our markets is automatic and personal: 5× its starting amount of one good (500 of a good it starts with 100 of). The goods are dollar, oil and microchips.
- **Sub-traders** are extra traders under one account. One API token can act as any of them, which is what lets one person run many agents.
- Agents here are a single Python file (`agent.py`, standard library only) that talks to the market API and to a model through [OpenRouter](https://openrouter.ai/).

## What we did

1. **Designed a comparison.** 5 strategies × 3 models = 15 agents, named after Greek goddesses, each a sub-trader in a single-player market (only our traders and the market's NPCs).
2. **Ran it, and fixed what broke** (see *Lessons*), then ran it again.
3. **Picked Nemesis** (Haiku 5.5 + hard-haggler prompt) as the best candidate.
4. **Moved to the shared final market** (public, no sub-traders allowed) and ran Nemesis alone as the main trader, with an eager variant of its prompt.

### Models

| Model | Price in/out per 1M tokens | Result in the test |
|---|---|---|
| `anthropic/claude-haiku-5.5` | $0.10 / $0.50 | Best: took the top 4 places |
| `google/gemini-3.7-flash` | $0.75 / $3.75 | Mid-table; hit rate limits |
| `deepseek/deepseek-v4.1-flash` | $0.05 / $0.20 | Weakest: slow, often idle |

Prices are from OpenRouter's model list on 14 Nov 2026 and may change.

### Strategies

| Code | Strategy | Idea |
|---|---|---|
| S0 | Default | The agent's built-in prompt (baseline) |
| S1 | Focused accumulator | Sell everything else for the goal good, never sell it |
| S2 | Market-maker | Post buy and sell offers, earn the spread, use NPCs |
| S3 | **Hard haggler** | Open with strong offers, counter everything, walk away from weak deals |
| S4 | Fair dealer | Propose mutually good deals, build trust |

### The 15 agents

| Strategy | Haiku 5.5 | DeepSeek V4.1 Flash | Gemini 3.7 Flash |
|---|---|---|---|
| S0 Default | Hestia | Gaia | Selene |
| S1 Focused | Artemis | Nike | Eos |
| S2 Market-maker | Athena | Iris | Hecate |
| S3 Hard haggler | **Nemesis** | Eris | Hera |
| S4 Fair dealer | Themis | Demeter | Aphrodite |

The prompts are the `INSTRUCTIONS` constant at the top of each `agents/<name>/agent.py`, the model is the `MODEL` constant next to it.

## How we did it

The work was driven through a coding agent (Claude Code), which created the sub-traders, wrote each agent's folder and configuration, started and stopped agents on request, and reported progress. Rules we followed:

- **Never start an agent without an explicit yes** for a named list: running agents trade live under your account and spend your OpenRouter credit.
- **API calls go through `afc.py`**, which reads the token from `experiment.env`, so keys never appear on a command line.
- **Each agent has its own folder and `.env`**, with its own `agent-report.html` (an annotated explanation of its code, regenerated after every code change).
- **`EXPERIMENT.md`** is the log: the agent table and every change.

### Results

Ranked by progress during the second run (before it ended) and by total goods held. Nobody reached a goal in that run.

- Haiku agents took the top 4 places. The leader was **Nemesis**: total goods 340 against 300 for agents that only swapped goods one for one.
- The picture is **one snapshot of one unfinished run**, not proof that the hard-haggler strategy beats real opponents. Luck and the other agents' behaviour matter.
- In the final shared market, an earlier version of Nemesis ranked first of 11 traders at one check (397 total goods). A later eager-prompt version was started afterwards; see `final/nemesis/logs` (not committed) or the market leaderboard for what happened. No final result is recorded in this repo.

## Lessons

| Problem | Cause | Fix |
|---|---|---|
| Gemini agents crashed | OpenRouter new accounts: 20 requests per minute per model (HTTP 429), and the agent did not retry | Retry with waiting on 429 and 5xx |
| DeepSeek agents stopped early | `MAX_TOKENS = 2000` was used up by reasoning, so the reply had no tool call and the agent read it as "done" | `MAX_TOKENS = 8000`; log `finish_reason` |
| Haiku agents stopped after an empty reply | An empty reply was treated as "done" | Nudge the model up to 2 times before stopping |
| All 15 agents crashed | HTTP 402: the in-flight credit budget was exceeded. Every turn resends the whole history, about 115k tokens per turn | Retry on 402; in the final agent, cut tool results older than the newest 12 to 300 characters |

## Repository layout

```
.
├── afc.py                 # market API helper (reads experiment.env)
├── experiment.env.sample  # template for experiment.env (real file is not committed)
├── EXPERIMENT.md          # agent table, run log, change log
├── SUMMARY.md             # one-page summary
├── agents/<name>/         # the 15 test agents
│   ├── agent.py           #   the agent; MODEL and INSTRUCTIONS at the top
│   ├── agent-report.html  #   annotated explanation of the code
│   ├── AGENTS.md, EXPLAIN_CODE.md, CLAUDE.md
│   └── .env               #   NOT committed (see agents/.env.sample)
└── final/
    ├── afc.py
    └── nemesis/           # the agent in the final market (eager prompt,
                           # 402 retry, history trimming), no sub-trader id
```

`agent.py`, `AGENTS.md` and `EXPLAIN_CODE.md` are the starter files Agent Fight Club generates for a market, plus the changes described above.

## Run it yourself

You need Python 3.8+, an Agent Fight Club account with an API token ([user settings](https://agentfightclub.today/user/settings)), and an OpenRouter key ([keys](https://openrouter.ai/settings/keys)). Set a credit limit on the key: several agents spend from the same one.

1. Copy the samples and fill them in (the real files are git-ignored, the `*.sample` files are committed):

   | Sample | Copy to | Used by |
   |---|---|---|
   | `experiment.env.sample` | `experiment.env` | `afc.py`, the experiment folder |
   | `agents/.env.sample` | `agents/<name>/.env` | one test agent (with its `AFC_SUB_TRADER_ID`) |
   | `final/experiment.env.sample` | `final/experiment.env` | `final/afc.py`, the final market |
   | `final/nemesis/.env.sample` | `final/nemesis/.env` | Nemesis (no sub-trader id) |

   ```bash
   cp experiment.env.sample experiment.env        # then edit it
   ```

   You need three values: the market id, your Agent Fight Club token and your OpenRouter key. Never commit the real files.

2. Create the sub-traders (`python3 afc.py POST /sub-traders '{"name": "<name>"}'`), put each id in its agent's `.env`, then start the agent from its folder:

   ```bash
   cd agents/<name> && python3 agent.py
   ```

   For the final market: `cd final/nemesis && python3 agent.py`.

3. Check the market with `python3 afc.py GET ""`, `python3 afc.py GET /leaderboard` and `python3 afc.py GET /balances`.

The market ids in this repo's docs belong to a meetup session and will not be reusable.

## Caveats

- Costs add up: the 15-agent run used about $4 of OpenRouter credit in under half an hour because histories grow every turn. The 15 test agents do not have the history trimming that `final/nemesis` has.
- Strategy prompts here are untested hypotheses. Single runs mix luck and skill.
- Logs (`logs/`) and each agent's `.env` and `run.out` are not committed.
