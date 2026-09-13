"""
Test the sp500 snapshot map on random historical dates.

Three layers:
  A. internal - at N random dates the snapshot must agree with the ledger
     (last change applied, next change not yet applied) and have a sane size
  B. known facts - hand-picked membership facts (TSLA joined 2020-12-21, ...)
  C. external - compare against the independent fja05680/sp500 dataset on
     GitHub (skipped silently if it cannot be downloaded)

Run: python test_snapshots.py
"""

from __future__ import annotations

import csv
import datetime
import io
import random
from bisect import bisect_right
from collections import Counter

import sp500
from sp500 import RENAMES, constituents_on

SEED = 42
N_DATES = 50
START = datetime.date(2000, 1, 1)

# tickers with a known, documented gap in the Wikipedia ledger (see README) -
# the map deliberately deviates there, so they are skipped, not failed
KNOWN_GAPS = {"UA", "UAA", "IR", "AGN", "T", "WLP"}

# extra old->current translations used ONLY to compare against the external
# dataset fairly: it writes the symbol of the day (UTX, FB, LB...), our map
# writes today's symbol - these are pure renames with no ledger row involved
TEST_ALIASES = {
    "UTX": "RTX",
    "ANTM": "ELV",
    "WLP": "ELV",
    "ABC": "COR",
    "BLL": "BALL",
    "WRK": "SW",
    "LB": "BBWI",
    "LTD": "BBWI",
    "SYMC": "GEN",
    "NLOK": "GEN",
    "CBS": "PSKY",
    "VIAC": "PSKY",
    "PARA": "PSKY",
    "MMC": "MRSH",
    "BK": "BNY",
    "EQR": "VMRK",
    "PX": "LIN",
    "PKI": "RVTY",
    "CTL": "LUMN",
    "BBT": "TFC",
    "TMK": "GL",
    "HCP": "DOC",
    "PEAK": "DOC",
    "MYL": "VTRS",
    "BHGE": "BKR",
    "YHOO": "AABA",
    "WYN": "WYND",
    "DPS": "KDP",
}


def size_band(day: datetime.date):
    # ~500 tickers before multi-class listings, 503-505 after 2015, 503 today
    if day < datetime.date(2015, 1, 1):
        return 498, 504
    if day < datetime.date(2023, 1, 1):
        return 500, 508
    return 501, 506


def random_dates(end: datetime.date) -> list:
    rng = random.Random(SEED)
    picks = set()
    while len(picks) < N_DATES:
        picks.add(datetime.date.fromordinal(rng.randrange(START.toordinal(), end.toordinal())))
    return sorted(picks)


def part_a(dates: list) -> list:
    grouped_desc, _ = sp500._grouped_desc(sp500.load_changes(), until=sp500._built()["as_of"])
    groups = list(reversed(grouped_desc))
    group_dates = [g[0] for g in groups]

    failures = []
    for day in dates:
        members = constituents_on(day)
        low, high = size_band(day)
        if not low <= len(members) <= high:
            failures.append(f"{day}: size {len(members)} outside [{low}, {high}]")

        idx = bisect_right(group_dates, day)
        if idx > 0:  # the change already in effect at `day`
            when, added, removed = groups[idx - 1]
            for ticker in added - removed - KNOWN_GAPS:
                if ticker not in members:
                    failures.append(f"{day}: {ticker} was added {when} but is absent")
            for ticker in removed - added - KNOWN_GAPS:
                if ticker in members:
                    failures.append(f"{day}: {ticker} was removed {when} but is present")
        if idx < len(groups):  # the next change, not yet in effect at `day`
            when, added, removed = groups[idx]
            for ticker in added - removed - KNOWN_GAPS:
                if ticker in members:
                    failures.append(f"{day}: {ticker} only joins {when} but is already present")
            for ticker in removed - added - KNOWN_GAPS:
                if ticker not in members:
                    failures.append(f"{day}: {ticker} only leaves {when} but is already absent")
    return failures


# (date, ticker, should_be_member) - written in the map's dialect (today's symbols)
FACTS = [
    ("2009-06-01", "LEH", False), ("2009-06-01", "CRM", True), ("2009-06-01", "V", False),
    ("2010-06-15", "NFLX", False), ("2010-06-15", "V", True), ("2010-06-15", "BRK.B", True),
    ("2012-05-01", "PSX", True), ("2012-05-01", "KMI", False),
    ("2014-06-02", "GOOGL", True), ("2014-06-02", "GOOG", True),
    ("2014-06-02", "META", True), ("2014-06-02", "TSLA", False),
    ("2018-08-01", "TWTR", True), ("2018-08-01", "DD", False), ("2018-08-01", "DWDP", True),
    ("2020-06-01", "TSLA", False), ("2020-06-01", "CARR", True),
    ("2020-06-01", "OTIS", True), ("2020-06-01", "M", False),
    ("2021-02-01", "TSLA", True), ("2021-02-01", "ENPH", True), ("2021-02-01", "MRNA", False),
    ("2022-12-01", "TWTR", False), ("2022-12-01", "CEG", True), ("2022-12-01", "META", True),
    ("2023-09-01", "KVUE", True), ("2023-09-01", "ABNB", False), ("2023-09-01", "FRC", False),
    ("2024-11-01", "PLTR", True), ("2024-11-01", "DELL", True),
    ("2024-11-01", "SMCI", True), ("2024-11-01", "AMTM", True),
    ("2025-06-01", "COIN", True), ("2025-06-01", "DFS", False), ("2025-06-01", "HOOD", False),
    ("2026-07-01", "MRVL", True), ("2026-07-01", "CPB", False),
    ("2026-07-01", "CAG", False), ("2026-07-01", "HONA", True),
]

ALWAYS_IN = ["AAPL", "MSFT", "JNJ", "PG", "KO", "XOM", "WMT", "MCD", "PEP"]


def part_b(dates: list) -> list:
    failures = []
    for date_str, ticker, expected in FACTS:
        day = datetime.date.fromisoformat(date_str)
        actual = ticker in constituents_on(day)
        if actual != expected:
            failures.append(f"{day}: {ticker} expected {'IN' if expected else 'OUT'}, got {'IN' if actual else 'OUT'}")
    for day in dates:
        members = constituents_on(day)
        for ticker in ALWAYS_IN:
            if ticker not in members:
                failures.append(f"{day}: mega-cap {ticker} missing")
    return failures


def _normalize(ticker: str) -> str:
    ticker = ticker.strip().upper().replace("-", ".")
    ticker = RENAMES.get(ticker, ticker)
    return TEST_ALIASES.get(ticker, ticker)


def part_c(dates: list) -> None:
    import requests

    headers = {"User-Agent": "cagr-analysis-test/1.0"}
    try:
        listing = requests.get("https://api.github.com/repos/fja05680/sp500/contents/", headers=headers, timeout=30)
        listing.raise_for_status()
        entry = next(
            e for e in listing.json() if "Historical Components" in e["name"] and e["name"].endswith(".csv")
        )
        text = requests.get(entry["download_url"], headers=headers, timeout=120).text
    except Exception as error:
        print(f"\nC. external cross-check SKIPPED (could not download): {error}")
        return

    rows = []
    for record in csv.reader(io.StringIO(text)):
        try:
            day = datetime.date.fromisoformat(record[0])
        except (ValueError, IndexError):
            continue
        rows.append((day, {_normalize(t) for t in record[1].split(",") if t.strip()}))
    rows.sort()
    row_dates = [r[0] for r in rows]
    print(f"\nC. external cross-check vs fja05680/sp500 ({entry['name']}, {len(rows)} rows)")

    eras = {"2000-2007": [], "2008-2012": [], "2013-today": []}
    disagreements = Counter()
    for day in dates:
        idx = bisect_right(row_dates, day)
        if idx == 0:
            continue
        theirs = rows[idx - 1][1]
        ours = {_normalize(t) for t in constituents_on(day)}
        jaccard = 100 * len(ours & theirs) / len(ours | theirs)
        for ticker in ours ^ theirs:
            disagreements[ticker] += 1
        if day.year <= 2007:
            eras["2000-2007"].append(jaccard)
        elif day.year <= 2012:
            eras["2008-2012"].append(jaccard)
        else:
            eras["2013-today"].append(jaccard)

    for era, values in eras.items():
        if values:
            print(f"   {era}: avg {sum(values) / len(values):5.1f}%  min {min(values):5.1f}%  (n={len(values)})")
    top = ", ".join(f"{t}({n})" for t, n in disagreements.most_common(15))
    print(f"   most frequent disagreements: {top}")


def main() -> None:
    built = sp500._built()
    dates = random_dates(built["as_of"])
    print(f"testing {len(dates)} random dates, seed {SEED}, {dates[0]} to {dates[-1]}")

    for day in (dates[0], dates[len(dates) // 2], dates[-1]):
        members = sorted(constituents_on(day))
        print(f"   sample {day}: {len(members)} tickers, e.g. {' '.join(members[:8])} ...")

    failures_a = part_a(dates)
    print(f"\nA. ledger consistency: {'PASS' if not failures_a else f'{len(failures_a)} FAILURES'}")
    for line in failures_a:
        print(f"   {line}")

    failures_b = part_b(dates)
    print(f"\nB. known facts ({len(FACTS)} facts + {len(ALWAYS_IN)} mega-caps x {len(dates)} dates): "
          f"{'PASS' if not failures_b else f'{len(failures_b)} FAILURES'}")
    for line in failures_b:
        print(f"   {line}")

    part_c(dates)


if __name__ == "__main__":
    main()
