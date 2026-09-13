"""
US entry point - mirrors cagr/run.py.

    python run.py                                # yearly starts 2013 -> today
    python run.py --start 2019-01-10 --max-dates 1
    python run.py --max-dates 1 --limit-tickers 10   # quick smoke test

Snapshot map is trustworthy 2013+, decent to 2008, unusable before
(see README) - hence the 2013 default start.
"""

from __future__ import annotations

import argparse
import datetime
import os
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.append(str(HERE.parent / "cagr"))

from models import ModVar  # noqa: E402

from main_us import main_process  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(description="US S&P 500 momentum research run")
    parser.add_argument("--start", default="2013-01-10", help="first candidate start date (YYYY-MM-DD)")
    parser.add_argument("--back", type=int, default=30 * 9, help="look-back window in days")
    parser.add_argument("--forward", type=int, default=365, help="look-ahead window / stride in days")
    parser.add_argument("--folder", default="research/1yr-9mnth-back", help="output folder inside us-cagr/")
    parser.add_argument("--max-dates", type=int, default=None, help="only process the first N start dates")
    parser.add_argument("--limit-tickers", type=int, default=None, help="only first N tickers (smoke test)")
    args = parser.parse_args()

    folder_path = HERE / args.folder
    os.makedirs(folder_path, exist_ok=True)

    # api slot is None: yfinance needs no session, ModVar only carries the dates
    modvar = ModVar(None, str(folder_path), args.back, args.forward, datetime.date.fromisoformat(args.start))

    main_process(modvar, max_dates=args.max_dates, limit_tickers=args.limit_tickers)


if __name__ == "__main__":
    main()
