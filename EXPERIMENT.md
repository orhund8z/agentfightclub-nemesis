# Experiment: strategy x model

Market: **Meetup 14.11.2026 Multi-agents (Orhun)** (`7922ef0f-29a8-4e88-a1e5-e04a781dbe7c`)
Goods: dollar, oil, microchips (100 each). Goal mode: auto-personal, multiplier 5.

Design: 5 strategies x 3 models = 15 agents. Each strategy runs once per model.

| Agent | Sub-trader id | Model | Strategy |
|---|---|---|---|
| Hestia | c11d7451-f355-4d25-befc-15c9c53a6a0b | anthropic/claude-haiku-5.5 | S0 Default (built-in) |
| Gaia | 5303501a-aca5-4ea1-881e-88ade884a5b4 | deepseek/deepseek-v4.1-flash | S0 Default (built-in) |
| Selene | f7734b74-a246-4fda-8fae-009ce1a1ad74 | google/gemini-3.7-flash | S0 Default (built-in) |
| Artemis | 28560fde-ab43-453a-b440-184db92e3d30 | anthropic/claude-haiku-5.5 | S1 Focused accumulator |
| Nike | 43c7df6d-6262-4b53-ba93-67787c7437e6 | deepseek/deepseek-v4.1-flash | S1 Focused accumulator |
| Eos | ae417b36-8886-48d7-940a-5d3197aa24f1 | google/gemini-3.7-flash | S1 Focused accumulator |
| Athena | 390efc4e-6271-4182-8ac3-6d52c81d619e | anthropic/claude-haiku-5.5 | S2 Market-maker |
| Iris | 35e8cfd0-65fd-4c52-8db4-f6823ce1eb31 | deepseek/deepseek-v4.1-flash | S2 Market-maker |
| Hecate | d64864fc-0415-4e99-a964-5454ec3e3b9e | google/gemini-3.7-flash | S2 Market-maker |
| Nemesis | e53d836e-2c27-41f9-b401-3df2317510e8 | anthropic/claude-haiku-5.5 | S3 Hard haggler |
| Eris | d7a842c4-e701-4031-b845-06f195c7b7e4 | deepseek/deepseek-v4.1-flash | S3 Hard haggler |
| Hera | 0a7e6cbb-4ad6-4b59-90e2-35871fc4dc05 | google/gemini-3.7-flash | S3 Hard haggler |
| Themis | a580c153-1765-4bc6-a54b-3ea655455fee | anthropic/claude-haiku-5.5 | S4 Fair dealer |
| Demeter | b4775954-0abf-4a0c-8c77-505c92da226a | deepseek/deepseek-v4.1-flash | S4 Fair dealer |
| Aphrodite | 22d92b02-b13e-42f8-b63e-557b2fb890eb | google/gemini-3.7-flash | S4 Fair dealer |

## Runs

(none yet)

## Changes

- 2026-11-14: first attempt ended early (Gemini 429 rate limits, DeepSeek truncated at MAX_TOKENS=2000, Haiku empty replies). Patched all 15 agents identically: MAX_TOKENS 8000, retry on 429/5xx, up to 2 nudges on a reply without tool call, and a "keep trading until your goal" line added to every strategy prompt. First attempt is not counted as a run.

- 2026-11-14 (final market c1940468-…): final/nemesis = Nemesis agent without sub-trader id; added 402 retry and tool-result trimming (newest 12 full, older cut to 300 chars).
- 2026-11-14: final/nemesis prompt changed to an eager variant (post several offers at once, accept small-margin deals, never wait). Takes effect on the next start.
