"""
Test which Xeno-canto search tags really support < and > operators,
and whether xcapi's quoting (tag:">X") breaks them.

One API request per row, first page only, nothing downloaded.
Run in a notebook with:  %run test_xc_operators.py
"""
import time
import pandas as pd
from xcapi.client import XenoCantoClient

BASE = "grp:birds"   # broad population so sparse tags still return data

# tag: (threshold used for < and >, an equivalent-ish range as a sanity check)
CASES = {
    "q":        ("C",          "A"),            # quality, letters
    "len":      ("60",         "10-20"),        # seconds
    "year":     ("2018",       "2015-2020"),
    "month":    ("6",          "1-3"),
    "uploaded": ("2022-01-01", "2020-2024"),    # xcapi docs use years here
    "alt":      ("1000",       "100-500"),
    "lat":      ("50",         "40-45"),
    "lon":      ("0",          "0-10"),
    "temp":     ("10",         "20-30"),
    "smp":      ("48000",      "44100-96000"),
    "nr":       ("800000",     "1-799999"),     # known: unsupported, control case
}

client = XenoCantoClient()


def count(query):
    """Return (numRecordings, error text) for a query, using one page."""
    try:
        r = client._fetch_page(query, 1, 50)
        return int(r.get("numRecordings", 0)), (r.get("error") or r.get("message") or "")
    except Exception as e:
        msg = str(e)
        return None, ("HTTP 400" if "400" in msg else msg.split(" for url")[0])  # keep API key out of output


baseline, _ = count(BASE)
print(f"Baseline '{BASE}': {baseline}\n")

rows = []
for tag, (thr, rng) in CASES.items():
    res = {"tag": tag}
    forms = {
        "gt_quoted":   f'{tag}:">{thr}"',   # what xcapi sends today
        "gt_unquoted": f"{tag}:>{thr}",
        "lt_quoted":   f'{tag}:"<{thr}"',
        "lt_unquoted": f"{tag}:<{thr}",
        "range":       f"{tag}:{rng}",
    }
    for name, tagstr in forms.items():
        n, err = count(f"{BASE} {tagstr}")
        res[name] = n if n is not None else err
        time.sleep(0.3)  # be polite to the API

    gq, lq, gu, lu = (res[k] for k in ("gt_quoted", "lt_quoted", "gt_unquoted", "lt_unquoted"))
    ok = lambda v: isinstance(v, int) and v > 0
    if ok(gq) and ok(lq):
        verdict = "OK as xcapi sends it"
    elif ok(gu) or ok(lu):
        verdict = "QUOTING BUG: works unquoted only"
    elif ok(res["range"]):
        verdict = "API does not support < / > (range works)"
    else:
        verdict = "No data / inconclusive"
    res["verdict"] = verdict
    rows.append(res)
    print(f"{tag:9s} {verdict}")

df = pd.DataFrame(rows).set_index("tag")
pd.set_option("display.width", 200)
print()
print(df)
df.to_csv("xc_operator_test.csv")
