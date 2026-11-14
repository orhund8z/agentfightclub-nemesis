"""python3 afc.py METHOD PATH [JSON_BODY] — call this market's API with the AFC token from experiment.env.
PATH is relative to the market, e.g. "" for the market itself, or "/sub-traders"."""
import os, sys, urllib.error, urllib.request

here = os.path.dirname(os.path.abspath(__file__))
env = dict(l.strip().split("=", 1) for l in open(os.path.join(here, "experiment.env"))
           if "=" in l and not l.lstrip().startswith("#"))
method, path = sys.argv[1].upper(), sys.argv[2]
body = sys.argv[3].encode("utf-8") if len(sys.argv) > 3 else None
request = urllib.request.Request(
    env["AFC_SERVER_URL"] + "/market/api/markets/" + env["AFC_MARKET_ID"] + path,
    data=body, method=method,
    headers={"Authorization": "Bearer " + env["AFC_API_KEY"], "Content-Type": "application/json"},
)
try:
    with urllib.request.urlopen(request) as response:
        print(response.read().decode("utf-8"))
except urllib.error.HTTPError as error:
    raise SystemExit(str(error.code) + " " + error.read().decode("utf-8"))
