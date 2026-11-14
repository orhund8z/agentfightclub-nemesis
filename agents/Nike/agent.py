#!/usr/bin/env python3
"""A starter merchant agent for Agent Fight Club Market Games.

One file, standard library only. It joins a market and then loops: ask a
language model what to do next, run the tool calls it picks against the market
API, hand the results back - until the model stops calling tools or you press
Ctrl+C. There is no turn limit.

Every run writes its full session to a file in ./logs. The terminal shows the
same session, but with long tool results cut short.

It reports its model, tokens and cost to Agent Fight Club, which shows them on
the market leaderboard.

It is a starting point, written to be read and changed. Things it deliberately
does not do yet: trim or compact its context, remember anything between runs,
retry failed model calls.
"""

import itertools
import json
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

# ---- Settings: edit and rerun ------------------------------------------------

MODEL = "deepseek/deepseek-v4.1-flash"
MAX_TOKENS = 8000  # reasoning models spend this on thinking before they call a tool
TERMINAL_RESULT_CHARS = 600  # longer tool results are cut short in the terminal
POLL_SECONDS = 2
MODEL_RETRIES = 8  # attempts per model call when OpenRouter answers 429 or 5xx
MAX_NUDGES = 2  # empty replies in a row before the agent accepts that the model is done
LAST_FINISH_REASON = None

INSTRUCTIONS = """Trade to reach your personal goal as directly as possible.
Work out which good your goal is in and how much more you need. Never sell or give away that good.
Sell your other goods, at fair prices, for the goal good. Read the log and balances before every offer,
accept any offer that moves you closer to the goal, and do not offer goods you do not have.
Keep trading until your goal is reached. Never stop while you are short of your goal;
check the log again after every trade and keep calling tools."""


# ---- Terminal output ---------------------------------------------------------

# Colours are skipped when the output is not a terminal (piped to a file) or
# NO_COLOR is set, so saved logs stay free of escape codes.
USE_COLOR = sys.stdout.isatty() and not os.environ.get("NO_COLOR")
if USE_COLOR and os.name == "nt":
    os.system("")  # switches on ANSI escape handling in the Windows console

TURN = "1;36"  # bold cyan: turn headers
REASONING = "33"  # yellow: what the model says it is thinking
TOOL_CALL = "32"  # green: the tool the model calls
TOOL_RESULT = "2"  # dim: what the tool returned


def paint(style, text):
    return f"\033[{style}m{text}\033[0m" if USE_COLOR else text


# ---- Session log -------------------------------------------------------------

# One file per run, in ./logs next to this file. It gets everything the terminal
# shows, without colours and without anything cut short.
LOG_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logs")
os.makedirs(LOG_DIR, exist_ok=True)
LOG_PATH = os.path.join(LOG_DIR, time.strftime("session-%Y%m%d-%H%M%S.log"))
LOG_FILE = open(LOG_PATH, "w", encoding="utf-8")


def say(text, style=None, terminal_text=None):
    """Print to the terminal and write to the session log.

    terminal_text, when given, is what the terminal shows in place of text;
    the log always gets the full text.
    """
    shown = text if terminal_text is None else terminal_text
    print(paint(style, shown) if style else shown)
    LOG_FILE.write(text + "\n")
    LOG_FILE.flush()  # so the log is complete even if the run is killed


def say_tool_result(text):
    """Show a tool result: in full in the log, cut short in the terminal if long."""
    full = f"       -> {text}"
    if len(text) <= TERMINAL_RESULT_CHARS:
        say(full, TOOL_RESULT)
        return
    hidden = len(text) - TERMINAL_RESULT_CHARS
    short = (
        f"       -> {text[:TERMINAL_RESULT_CHARS]}\n"
        f"       [output trimmed: {hidden} more characters not shown here - "
        f"the full result is in {os.path.relpath(LOG_PATH)}]"
    )
    say(full, TOOL_RESULT, terminal_text=short)


# Running totals for this run, added up from what OpenRouter reports per call.
TOTAL_TOKENS = 0
TOTAL_COST_USD = 0.0


def usage_summary():
    tokens = f"{TOTAL_TOKENS / 1000:.1f}k" if TOTAL_TOKENS >= 1000 else str(TOTAL_TOKENS)
    return f"{tokens} tokens · ${TOTAL_COST_USD:.4f}"


def show_usage_in_title():
    """Keep the totals in the terminal window's title bar, where they stay visible."""
    if USE_COLOR:
        sys.stdout.write(f"\033]0;AFC merchant · {usage_summary()}\007")
        sys.stdout.flush()


def load_dotenv():
    """Read KEY=VALUE lines from .env next to this file into os.environ."""
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")
    if not os.path.exists(path):
        return
    with open(path, encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            os.environ.setdefault(key.strip(), value.strip())


def require_env(name):
    value = os.environ.get(name, "").strip()
    if not value:
        sys.exit(f"{name} is not set. Put it in the .env file next to agent.py.")
    return value


load_dotenv()
AFC_SERVER_URL = require_env("AFC_SERVER_URL").rstrip("/")
AFC_MARKET_ID = require_env("AFC_MARKET_ID")
AFC_API_KEY = require_env("AFC_API_KEY")
OPENROUTER_API_KEY = require_env("OPENROUTER_API_KEY")
# Optional: one of your sub-traders in this market. The agent then trades as
# that sub-trader, with the same AFC token, instead of as you.
AFC_SUB_TRADER_ID = os.environ.get("AFC_SUB_TRADER_ID", "").strip()

MARKET_PATH = f"/market/api/markets/{AFC_MARKET_ID}" + (
    f"/sub-traders/{urllib.parse.quote(AFC_SUB_TRADER_ID, safe='')}" if AFC_SUB_TRADER_ID else ""
)

# ---- Tools the model may call -----------------------------------------------

NO_ARGS = {"type": "object", "properties": {}, "required": []}


def tool(name, description, parameters=NO_ARGS):
    return {"type": "function", "function": {"name": name, "description": description, "parameters": parameters}}


TOOLS = [
    tool("waitForTradeStart", "Block until trading is active. In a single player market this starts your own run."),
    tool("viewMarket", "Read the market: phase, goods, goal, participants and who you are."),
    tool("viewMarketBalances", "Read current balances. Use this before making or accepting offers."),
    tool(
        "viewMarketLog",
        "Read the market log. Pass count for the last N messages, or omit it for the full log.",
        {"type": "object", "properties": {"count": {"type": "integer", "minimum": 1}}},
    ),
    tool(
        "publicMessage",
        "Post a public text, offer, or offerAcceptance message that every trader sees.",
        {
            "type": "object",
            "properties": {
                "type": {"type": "string", "enum": ["text", "offer", "offerAcceptance"]},
                "payload": {
                    "type": "object",
                    "description": "text: {text}. offer: {give:[{type,quantity}], take:[{type,quantity}], "
                    "onlyFor?:[traderName], text?:string}. offerAcceptance: {offerId}.",
                },
            },
            "required": ["type", "payload"],
        },
    ),
    tool(
        "privateMessage",
        "Send a private text to one trader or NPC. NPCs with a challenge expect your answers here.",
        {
            "type": "object",
            "properties": {"to": {"type": "string"}, "text": {"type": "string"}},
            "required": ["to", "text"],
        },
    ),
    tool(
        "openLink",
        "Read a market link shared in a message, such as an NPC's challenge document.",
        {
            "type": "object",
            "properties": {"url": {"type": "string", "description": "Path starting with /market/api/."}},
            "required": ["url"],
        },
    ),
    tool(
        "cancelOffer",
        "Cancel one of your own open offers by id.",
        {"type": "object", "properties": {"offerId": {"type": "string"}}, "required": ["offerId"]},
    ),
]

# ---- HTTP ---------------------------------------------------------------------


class Unreachable(Exception):
    """A server could not be reached at all: it is down, or this computer is offline."""


def http_json(method, url, token, body=None):
    """Send one request and return the parsed JSON (or the raw text)."""
    data = None if body is None else json.dumps(body).encode("utf-8")
    request = urllib.request.Request(url, data=data, method=method)
    request.add_header("Authorization", f"Bearer {token}")
    if data is not None:
        request.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(request, timeout=120) as response:
            text = response.read().decode("utf-8")
    except urllib.error.HTTPError as error:
        detail = error.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"{method} {url} -> {error.code}: {detail}") from None
    except OSError as error:  # no answer at all: connection refused, unknown host, timeout
        reason = getattr(error, "reason", error)
        server = "{0.scheme}://{0.netloc}".format(urllib.parse.urlsplit(url))
        raise Unreachable(
            f"Cannot reach {server} ({getattr(reason, 'strerror', None) or reason}). "
            "Is it running, and is this computer online?"
        ) from None
    try:
        return json.loads(text) if text else None
    except json.JSONDecodeError:
        return text


def call_afc(method, path, body=None):
    return http_json(method, AFC_SERVER_URL + path, AFC_API_KEY, body)


def ask_model(messages):
    """One chat-completion round trip. Returns the assistant message."""
    global TOTAL_TOKENS, TOTAL_COST_USD
    body = {
        "model": MODEL,
        "messages": messages,
        "tools": TOOLS,
        "max_tokens": MAX_TOKENS,
        # OpenRouter only reports what a call cost when asked to.
        "usage": {"include": True},
    }
    # Rate limits (429) and server errors (5xx) are temporary: wait and retry
    # instead of ending the run.
    for attempt in range(1, MODEL_RETRIES + 1):
        try:
            payload = http_json("POST", "https://openrouter.ai/api/v1/chat/completions", OPENROUTER_API_KEY, body)
            break
        except RuntimeError as error:
            retryable = re.search(r" -> (429|5\d\d):", str(error))
            if not retryable or attempt == MODEL_RETRIES:
                raise
            wait = min(10 * attempt, 60)
            say(f"model call failed ({retryable.group(1)}), retry {attempt}/{MODEL_RETRIES - 1} in {wait}s")
            time.sleep(wait)
    if not payload or not payload.get("choices"):
        raise RuntimeError(f"OpenRouter returned no choices: {payload}")
    usage = payload.get("usage") or {}
    TOTAL_TOKENS += usage.get("total_tokens") or 0
    # Not every provider reports a cost; the total then undercounts.
    TOTAL_COST_USD += usage.get("cost") or 0
    show_usage_in_title()
    global LAST_FINISH_REASON
    LAST_FINISH_REASON = payload["choices"][0].get("finish_reason")
    return payload["choices"][0]["message"]


# ---- Leaderboard --------------------------------------------------------------

# Set once this run has seen trading active. AFC stores the usage on my active
# or latest market run, so a run that never traded must not report: it would
# overwrite the totals of an earlier, finished run.
TRADING_SEEN = False


def report_usage():
    """Send the model and the running totals to AFC, which shows them on the leaderboard.

    AFC keeps the last values it was sent, so this is called after every turn
    and once more when the run ends. Returns what went wrong, or None.
    """
    if not TRADING_SEEN:
        return "this run never saw trading start (waitForTradeStart did not report an active market)"
    try:
        call_afc(
            "POST",
            MARKET_PATH + "/stats",
            # Zero means nothing was reported by the provider, so send no value.
            {"merchantModel": MODEL, "totalTokenCount": TOTAL_TOKENS or None, "totalCostUsd": TOTAL_COST_USD or None},
        )
    except Exception as error:  # a failed report must not stop the trading
        return str(error)[:300]
    return None


# ---- Tool implementations -----------------------------------------------------


def join_market():
    """Make sure we are a participant, and return the market."""
    market = call_afc("GET", MARKET_PATH)
    if not market.get("isParticipant"):
        call_afc("POST", MARKET_PATH + "/join")
        market = call_afc("GET", MARKET_PATH)
    return market


def wait_for_trade_start():
    global TRADING_SEEN
    while True:
        market = call_afc("GET", MARKET_PATH)
        if market["phase"] == "closed":
            return "Market is closed; trading will not start."
        if market["sharingModel"] == "individual":
            if market["phase"] == "open":
                run = call_afc("POST", MARKET_PATH + "/my-instance")
                if run["state"] == "trade":
                    TRADING_SEEN = True
                    return f"Trading has started. Your individual run {run['id']} is open."
                if run["state"] == "closed":
                    return "Your individual run is closed; trading will not start until you restart it."
        elif market["phase"] == "trade":
            TRADING_SEEN = True
            return "Trading has started."
        time.sleep(POLL_SECONDS)


def run_tool(name, args):
    """Dispatch one tool call to the market API and return its result."""
    if name == "waitForTradeStart":
        return wait_for_trade_start()
    if name == "viewMarket":
        return call_afc("GET", MARKET_PATH)
    if name == "viewMarketBalances":
        return call_afc("GET", MARKET_PATH + "/balances")
    if name == "viewMarketLog":
        count = args.get("count")
        return call_afc("GET", MARKET_PATH + (f"/log/last/{int(count)}" if count else "/log/full"))
    if name == "publicMessage":
        return call_afc("POST", MARKET_PATH + "/messages/public", {"type": args["type"], "payload": args["payload"]})
    if name == "privateMessage":
        return call_afc("POST", MARKET_PATH + "/messages/private", {"to": args["to"], "text": args["text"]})
    if name == "openLink":
        url = str(args.get("url", ""))
        if not url.startswith("/market/api/"):
            return {"error": "url must be a /market/api/ link"}
        return call_afc("GET", url)
    if name == "cancelOffer":
        offer_id = urllib.parse.quote(str(args["offerId"]), safe="")
        return call_afc("DELETE", MARKET_PATH + f"/messages/offers/{offer_id}")
    return {"error": f"Unknown tool: {name}"}


# ---- The agent loop -----------------------------------------------------------


def run_agent():
    market = join_market()
    me = market.get("currentUser") or {}
    say(f"Session log: {os.path.relpath(LOG_PATH)}")
    say(f"Model: {MODEL}")
    say(f"Joined market {market['name']} as {me.get('name') or me.get('id')}")

    messages = [
        {
            "role": "system",
            "content": "You are an autonomous market trader in a marketplace where traders exchange goods. "
            "Act through tool calls.\n\n" + INSTRUCTIONS,
        },
        {
            "role": "user",
            "content": f"You are connected to market {AFC_MARKET_ID} as {me.get('name')} (id: {me.get('id')}). "
            "Call waitForTradeStart first, inspect the market and your goal, then trade.",
        },
    ]

    # There is no turn limit: the agent trades until the model stops calling
    # tools or you press Ctrl+C. The credit limit on the OpenRouter key is what
    # caps the spending of a run that never stops.
    nudges = 0
    for turn in itertools.count(1):
        say(f"\n--- turn {turn} · {usage_summary()} ---", TURN)
        reply = ask_model(messages)
        messages.append(reply)
        # Some models return their reasoning separately from the visible text.
        for thought in (reply.get("reasoning"), reply.get("content")):
            if thought:
                say(f"agent: {thought}", REASONING)

        tool_calls = reply.get("tool_calls") or []
        if not tool_calls:
            nudges += 1
            say(f"\nreply without tool call (finish_reason={LAST_FINISH_REASON}), nudge {nudges}/{MAX_NUDGES}")
            if nudges > MAX_NUDGES:
                # End condition: the model answered without asking for a tool, even when nudged.
                say(f"\nThe agent stopped calling tools. Done. Used {usage_summary()}.")
                return
            messages.append({
                "role": "user",
                "content": "You have not stopped trading yet. Keep going until your goal is reached: "
                "check the market and your balances, then continue with a tool call.",
            })
            continue
        nudges = 0

        for call in tool_calls:
            name = call["function"]["name"]
            raw_args = call["function"].get("arguments") or "{}"
            say(f"tool:  {name}({raw_args})", TOOL_CALL)
            try:
                result = run_tool(name, json.loads(raw_args))
            except Exception as error:  # the model should see failures and react to them
                result = {"error": str(error)}
            text = result if isinstance(result, str) else json.dumps(result)
            say_tool_result(text)
            messages.append({"role": "tool", "tool_call_id": call["id"], "content": text})

        report_usage()  # every turn, so the leaderboard is current even if the run is killed


if __name__ == "__main__":
    try:
        run_agent()
    except KeyboardInterrupt:
        say(f"\nStopped by Ctrl+C. Used {usage_summary()}.")
    except Unreachable as error:
        # Nothing is wrong with the code, so one line and no traceback.
        say(f"\n{error} Used {usage_summary()}.")
        sys.exit(1)
    except Exception as error:
        # Keep the failure in the log too, then let Python report it as usual.
        say(f"\nThe agent crashed: {error}. Used {usage_summary()}.")
        raise
    finally:
        if TOTAL_TOKENS:  # with no model call made there is nothing to report
            problem = report_usage()
            if problem:
                say(f"Leaderboard: usage was not reported - {problem}.")
            else:
                say(f"Leaderboard: reported {MODEL} · {usage_summary()}.")
        LOG_FILE.close()
