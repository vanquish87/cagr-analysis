"""
Point-in-time S&P 500 membership - the US analog of cagr/isin.py's isin_yearly.

The Wikipedia change ledger (sp500_changes.json) only records deltas, so full
membership is reconstructed by starting from today's constituent list
(sp500_current.json) and walking the ledger BACKWARDS: undo each change by
discarding the added ticker and restoring the removed one. A snapshot is
recorded at every effective date; membership ON that date includes that date's
changes, and any date in between resolves to the nearest preceding snapshot -
the same convention as get_target_isin_date() on the India side.

Usage:
    python sp500.py                     summary
    python sp500.py --date 2015-03-24   print membership on a date
    python sp500.py --validate          data quality report
    python sp500.py --write-json        write sp500_snapshots.json
"""

from __future__ import annotations

import argparse
import datetime
import json
from bisect import bisect_right
from pathlib import Path

HERE = Path(__file__).resolve().parent
CURRENT_FILE = HERE / "sp500_current.json"
CHANGES_FILE = HERE / "sp500_changes.json"
SNAPSHOT_FILE = HERE / "sp500_snapshots.json"

# Old ledger symbol -> today's symbol for the SAME continuing listing (pure
# ticker renames). Wikipedia's ledger writes the symbol used on the day of the
# change, while the anchor list uses today's symbols; translating the old ones
# forward keeps the whole map in one dialect (today's tickers), which is also
# what price APIs like Yahoo key their full history under.
# NOTE: never map a recycled symbol (Q was Qwest, QuintilesIMS and Qnity).
RENAMES = {
    "FB": "META",  # Facebook -> Meta Platforms (2022, no index event so no ledger row)
    "HRS": "LHX",  # Harris Corp -> L3Harris (2019 merger kept Harris' listing)
    "PCLN": "BKNG",  # Priceline -> Booking Holdings (2018)
    "CDAY": "DAY",  # Ceridian -> Dayforce (2024, ledger records it as a swap row)
    "WLTW": "WTW",  # Willis Towers Watson ticker change (2022)
    "FLT": "CPAY",  # FLEETCOR -> Corpay (2024)
    "RE": "EG",  # Everest Re -> Everest Group (2023)
    "KORS": "CPRI",  # Michael Kors -> Capri Holdings (2019)
    "DLPH": "APTV",  # Delphi Automotive -> Aptiv (2017)
    "JOYG": "JOY",  # Joy Global dropped the G (2012)
    "COG": "CTRA",  # Cabot Oil & Gas -> Coterra (2021, kept Cabot's listing)
    "JEC": "J",  # Jacobs Engineering -> Jacobs Solutions (2019)
    "TSO": "ANDV",  # Tesoro -> Andeavor (2017)
    "LUK": "JEF",  # Leucadia -> Jefferies (2018)
    "SATS": "ECHO",  # EchoStar ticker change (2026)
}


def _parse_date(value: str) -> datetime.date:
    return datetime.date.fromisoformat(value)


def load_anchor():
    with open(CURRENT_FILE, "r") as file:
        data = json.load(file)
    return _parse_date(data["as_of"]), {c["symbol"] for c in data["constituents"]}


def load_changes() -> list:
    with open(CHANGES_FILE, "r") as file:
        data = json.load(file)
    changes = []
    for row in data["changes"]:
        changes.append(
            {
                **row,
                "date": _parse_date(row["date"]),
                "added": RENAMES.get(row["added"], row["added"]),
                "removed": RENAMES.get(row["removed"], row["removed"]),
            }
        )
    return changes


def _grouped_desc(changes: list, until: datetime.date):
    """One (date, added_set, removed_set) per effective date, newest first.
    Rows dated after `until` (announced but not yet effective vs the anchor)
    are returned separately and skipped during reconstruction."""
    by_date, skipped = {}, []
    for row in changes:
        if row["date"] > until:
            skipped.append(row)
            continue
        added, removed = by_date.setdefault(row["date"], (set(), set()))
        if row["added"]:
            added.add(row["added"])
        if row["removed"]:
            removed.add(row["removed"])
    grouped = [(day, added, removed) for day, (added, removed) in sorted(by_date.items(), reverse=True)]
    return grouped, skipped


def build() -> dict:
    as_of, anchor = load_anchor()
    grouped, skipped_future = _grouped_desc(load_changes(), until=as_of)

    snapshots = {as_of: frozenset(anchor)}
    issues = []
    working = set(anchor)

    for day, added, removed in grouped:
        # membership ON `day` = current working set (day's changes still applied)
        snapshots.setdefault(day, frozenset(working))

        # undo the change; inconsistencies point at gaps elsewhere in the ledger
        add_not_found = sorted(added - working)
        working -= added
        remove_still_present = sorted(removed & working)
        working |= removed

        if add_not_found or remove_still_present:
            issues.append({"date": day, "add_not_found": add_not_found, "remove_still_present": remove_still_present})

    return {
        "as_of": as_of,
        "snapshots": snapshots,
        "pre_history": frozenset(working),  # before the oldest ledger row - rough, do not trust
        "issues": issues,
        "skipped_future": skipped_future,
    }


_CACHE = None


def _built() -> dict:
    global _CACHE
    if _CACHE is None:
        _CACHE = build()
    return _CACHE


def constituents_on(day: datetime.date) -> frozenset:
    """Tickers in the index on `day` (nearest snapshot on or before it)."""
    built = _built()
    keys = sorted(built["snapshots"])
    idx = bisect_right(keys, day)
    if idx == 0:
        return built["pre_history"]
    return built["snapshots"][keys[idx - 1]]


def snapshot_map() -> dict:
    """date -> frozenset of tickers, ascending - the shape isin_yearly has."""
    built = _built()
    return dict(sorted(built["snapshots"].items()))


def validate() -> None:
    built = _built()
    snapshots = built["snapshots"]
    anchor_date = built["as_of"]

    print(f"anchor: {anchor_date}, {len(snapshots[anchor_date])} tickers")
    print(f"snapshots: {len(snapshots)} dates, {min(snapshots)} to {max(snapshots)}")
    for row in built["skipped_future"]:
        print(f"ignored future-dated change {row['date']}: +{row['added']} -{row['removed']}")

    # the index holds ~500 companies (503 tickers today, with multi-class
    # shares); a drifting count means missing ledger rows in that era
    print("\nJan-1 ticker count by year (should hover around 500-503):")
    for year in range(2000, anchor_date.year + 1):
        count = len(constituents_on(datetime.date(year, 1, 1)))
        print(f"  {year}  {count}")

    issues = built["issues"]
    print(f"\nunwind inconsistencies: {len(issues)} dates (each one = a gap somewhere later in the ledger)")
    for issue in issues:
        parts = []
        if issue["add_not_found"]:
            parts.append(f"added-but-absent {','.join(issue['add_not_found'])}")
        if issue["remove_still_present"]:
            parts.append(f"removed-but-present {','.join(issue['remove_still_present'])}")
        print(f"  {issue['date']}: {'; '.join(parts)}")


def write_snapshots() -> None:
    built = _built()
    meta = {
        "as_of": built["as_of"].isoformat(),
        "built": datetime.date.today().isoformat(),
        "dates": len(built["snapshots"]),
        "note": "tickers in the index ON the key date; for other dates use the nearest preceding key",
    }
    lines = [
        f'  "{day.isoformat()}": {json.dumps(sorted(tickers))}'
        for day, tickers in sorted(built["snapshots"].items())
    ]
    with open(SNAPSHOT_FILE, "w") as file:
        file.write('{\n "meta": ' + json.dumps(meta) + ',\n "snapshots": {\n')
        file.write(",\n".join(lines))
        file.write("\n }\n}\n")
    print(f"{SNAPSHOT_FILE.name}: {len(lines)} snapshot dates written")


def main() -> None:
    parser = argparse.ArgumentParser(description="Point-in-time S&P 500 membership")
    parser.add_argument("--date", help="print membership on a date (YYYY-MM-DD)")
    parser.add_argument("--validate", action="store_true", help="data quality report")
    parser.add_argument("--write-json", action="store_true", help=f"write {SNAPSHOT_FILE.name}")
    args = parser.parse_args()

    if args.date:
        day = _parse_date(args.date)
        members = constituents_on(day)
        print(f"{len(members)} tickers on {day}:")
        print(" ".join(sorted(members)))
    if args.validate:
        validate()
    if args.write_json:
        write_snapshots()
    if not (args.date or args.validate or args.write_json):
        built = _built()
        snapshots = built["snapshots"]
        print(
            f"{len(snapshots)} snapshots, {min(snapshots)} to {max(snapshots)} "
            f"(anchor {built['as_of']}, {len(snapshots[built['as_of']])} tickers)"
        )
        print(f"unwind inconsistencies: {len(built['issues'])} dates (--validate for details)")


if __name__ == "__main__":
    main()
