# Experiment summary

## In short
We tested 15 trading agents (5 strategies × 3 models) in a single-player market, picked the best, **Nemesis**, and ran it alone in the shared final competition, where it won.

## Models
| Model | Price in/out per 1M tokens | Result in the test |
|---|---|---|
| `anthropic/claude-haiku-5.5` | $0.10 / $0.50 | Best: took the top 4 places |
| `google/gemini-3.7-flash` | $0.75 / $3.75 | Mid-table; hit rate limits |
| `deepseek/deepseek-v4.1-flash` | $0.05 / $0.20 | Weakest: slow, often idle |

## Strategies
| Code | Strategy | Idea |
|---|---|---|
| S0 | Default | The agent's built-in prompt (baseline) |
| S1 | Focused accumulator | Sell everything else for the goal good, never sell it |
| S2 | Market-maker | Post buy and sell offers, earn the spread, use NPCs |
| S3 | **Hard haggler** | Open with strong offers, counter everything, walk away from weak deals |
| S4 | Fair dealer | Propose mutually good deals, build trust |

## The 15 agents
| Strategy | Haiku 5.5 | DeepSeek V4.1 Flash | Gemini 3.7 Flash |
|---|---|---|---|
| S0 Default | Hestia | Gaia | Selene |
| S1 Focused | Artemis | Nike | Eos |
| S2 Market-maker | Athena | Iris | Hecate |
| S3 Hard haggler | **Nemesis** | Eris | Hera |
| S4 Fair dealer | Themis | Demeter | Aphrodite |

## How we ran it
1. Set up the market, one sub-trader and one folder per agent, with `afc.py` for all API calls and `EXPERIMENT.md` as the log.
2. Run 1 failed for fixable reasons: Gemini hit the OpenRouter rate limit (429), DeepSeek's replies were cut off at 2000 tokens, and empty replies were treated as "done". We patched all 15 identically and restarted.
3. Run 2 was cut short when all 15 crashed on HTTP 402 (OpenRouter in-flight credit budget). Every agent resends its whole history each turn, so cost grows (about $4.34 in total).
4. Agents start only after an explicit yes, and can be stopped any time.

## Why Nemesis
- It was the only agent whose total goods grew above 300; the others only swapped goods 1:1 (340 vs 300 at the time).
- Caveat: this was a snapshot of one unfinished run, not proof that the strategy beats real opponents.

## Final market (shared, public): Nemesis won
- Nemesis ran as the main trader (this market allows no sub-traders): Haiku 5.5 with the S3 hard-haggler prompt (eager variant), a retry on 402, and a trimmed history.
- It reached its goal (300 dollars, total wealth 375) in **8 min 41 s** and closed the trade. The goal had been lowered from 500 during the competition (admin change, goal multiplier now 3).
- While trading it led with 427 total goods against 208–331 for the others.

![Final market while trading](docs/images/final-market-trading.png)
![Final market closed, Nemesis reached its goal](docs/images/final-market-closed-nemesis-won.png)

## Files
- `experiment.env`, `afc.py`: keys and API helper
- `agents/<name>/`: the 15 test agents
- `final/nemesis/`: the agent in the final market
- `docs/images/`: screenshots of the final market
- `EXPERIMENT.md`: agent table and change log
