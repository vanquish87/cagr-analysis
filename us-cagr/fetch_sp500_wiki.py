"""
Fetch S&P 500 membership data from Wikipedia into local JSON files.

Produces, next to this script:
    sp500_current.json - today's constituents (symbol, security, CIK, date first added)
    sp500_changes.json - the add/remove ledger from 'Historical components of the S&P 500'

Same caching idea as instrument_data.json / NSE.json on the India side:
files are only downloaded when missing, re-run with --force after a rebalance.
"""

from __future__ import annotations

import argparse
import datetime
import json
import re
from io import StringIO
from pathlib import Path

import pandas as pd
import requests

HERE = Path(__file__).resolve().parent
CURRENT_FILE = HERE / "sp500_current.json"
CHANGES_FILE = HERE / "sp500_changes.json"

CURRENT_URL = "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies"
CHANGES_URL = "https://en.wikipedia.org/wiki/Historical_components_of_the_S%26P_500"
HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; cagr-analysis-research/1.0)"}


def _get(url: str) -> str:
    response = requests.get(url, headers=HEADERS, timeout=60)
    response.raise_for_status()
    return response.text


def _clean_ticker(value):
    # NaN / footnote brackets / stray wiki markup -> 'BRK.B' style ticker, or None
    if value is None or pd.isna(value):
        return None
    ticker = re.sub(r"\[.*?\]", "", str(value)).upper()
    ticker = re.sub(r"[^A-Z0-9.\-]", "", ticker)
    return ticker or None


def _clean_text(value):
    if value is None or pd.isna(value):
        return None
    text = re.sub(r"\[.*?\]", "", str(value)).strip()
    return text or None


def parse_changes(html: str) -> list:
    """Every add/remove row found on the page. The wikitable header is two rows
    deep (Added/Removed, then Ticker/Security), hence header=[0, 1]."""
    try:
        tables = pd.read_html(StringIO(html), header=[0, 1])
    except ValueError:
        return []

    rows = []
    for table in tables:
        level0 = [str(col[0]).strip().lower() for col in table.columns]
        level1 = [str(col[1]).strip().lower() for col in table.columns]
        if "added" not in level0 or "removed" not in level0:
            continue

        date_col = table.columns[0]
        added_idx = level0.index("added")  # first Added column = its Ticker column
        removed_idx = level0.index("removed")

        reason_col = None
        for i, name in enumerate(level0):
            if "reason" in name:
                reason_col = table.columns[i]
                break

        def name_col(idx):
            # the Security column sits right after its Ticker column
            if idx + 1 < len(level1) and "security" in level1[idx + 1]:
                return table.columns[idx + 1]
            return None

        added_name_col = name_col(added_idx)
        removed_name_col = name_col(removed_idx)

        for _, row in table.iterrows():
            when = pd.to_datetime(_clean_text(row[date_col]), errors="coerce")
            if pd.isna(when):
                continue
            added = _clean_ticker(row[table.columns[added_idx]])
            removed = _clean_ticker(row[table.columns[removed_idx]])
            if added is None and removed is None:
                continue
            rows.append(
                {
                    "date": when.date().isoformat(),
                    "added": added,
                    "added_name": _clean_text(row[added_name_col]) if added_name_col is not None else None,
                    "removed": removed,
                    "removed_name": _clean_text(row[removed_name_col]) if removed_name_col is not None else None,
                    "reason": _clean_text(row[reason_col]) if reason_col is not None else None,
                }
            )
    return rows


def parse_current(html: str) -> list:
    """The constituents table (the one carrying Symbol + CIK columns)."""
    for table in pd.read_html(StringIO(html)):
        columns = {str(col).strip().lower(): col for col in table.columns}
        if "symbol" not in columns or "cik" not in columns:
            continue

        records = []
        for _, row in table.iterrows():
            symbol = _clean_ticker(row[columns["symbol"]])
            if not symbol:
                continue
            cik_raw = row[columns["cik"]]
            try:
                cik = str(int(cik_raw)).zfill(10)
            except (TypeError, ValueError):
                digits = re.sub(r"\D", "", str(cik_raw))
                cik = digits.zfill(10) if digits else None
            records.append(
                {
                    "symbol": symbol,
                    "security": _clean_text(row[columns["security"]]) if "security" in columns else None,
                    "cik": cik,
                    "date_added": _clean_text(row[columns["date added"]]) if "date added" in columns else None,
                }
            )
        return records
    raise RuntimeError("No table with Symbol + CIK columns found on the constituents page")


def main() -> None:
    parser = argparse.ArgumentParser(description="Fetch S&P 500 constituents + change ledger from Wikipedia")
    parser.add_argument("--force", action="store_true", help="refetch even if the JSON files already exist")
    args = parser.parse_args()

    if CURRENT_FILE.exists() and CHANGES_FILE.exists() and not args.force:
        print(f"{CURRENT_FILE.name} and {CHANGES_FILE.name} already exist, use --force to refetch")
        return

    today = datetime.date.today().isoformat()

    print(f"Fetching {CURRENT_URL}")
    current_html = _get(CURRENT_URL)
    constituents = parse_current(current_html)

    print(f"Fetching {CHANGES_URL}")
    changes_html = _get(CHANGES_URL)

    # the historical page is the main ledger; the constituents page also carries a
    # 'selected changes' table with the freshest rows - merge both and dedupe
    changes, seen = [], set()
    for row in parse_changes(changes_html) + parse_changes(current_html):
        key = (row["date"], row["added"], row["removed"])
        if key in seen:
            continue
        seen.add(key)
        changes.append(row)
    changes.sort(key=lambda r: (r["date"], r["added"] or "", r["removed"] or ""), reverse=True)

    with open(CURRENT_FILE, "w") as file:
        json.dump(
            {"as_of": today, "source": CURRENT_URL, "count": len(constituents), "constituents": constituents},
            file,
            indent=1,
        )
    with open(CHANGES_FILE, "w") as file:
        json.dump(
            {"fetched": today, "source": CHANGES_URL, "count": len(changes), "changes": changes},
            file,
            indent=1,
        )

    print(f"{CURRENT_FILE.name}: {len(constituents)} constituents as of {today}")
    print(f"{CHANGES_FILE.name}: {len(changes)} change rows, {changes[-1]['date']} to {changes[0]['date']}")


if __name__ == "__main__":
    main()
