"""
US analyzer - same Protocol as AngleAnalyzer / UpstoxAnalyzer on the India side.

Data source: yfinance (Yahoo Finance), batched per ~100 tickers, with a
per-ticker Stooq CSV fallback. Prices are split+dividend adjusted
(auto_adjust=True) so multi-month returns survive stock splits.

Universe per date comes from sp500.constituents_on() - the point-in-time
snapshot map - translated to Yahoo's hyphen dialect (BRK.B -> BRK-B).

Fetch failures are counted per run and kept on `last_failures` so
survivorship bias stays visible: delisted names (TWTR, CELG, RTN...) have
no Yahoo data and silently vanish from the ranking otherwise.
"""

from __future__ import annotations

import datetime
import io
import logging
import sys
import time
from pathlib import Path

import pandas as pd
import requests
import yfinance as yf

HERE = Path(__file__).resolve().parent
sys.path.append(str(HERE.parent / "cagr"))

from analyzer import DefaultAnalyzer  # noqa: E402 - inherit df sorting/rolling helpers
from df_helper import build_df  # noqa: E402 - identical return math as the India pipeline
from sp500 import constituents_on  # noqa: E402

logging.getLogger("yfinance").setLevel(logging.CRITICAL)

CHUNK_SIZE = 100
CALENDAR_TICKER = "SPY"  # used only to find market-open dates


def to_yahoo(ticker: str) -> str:
    return ticker.replace(".", "-")


def _rows_from_frame(frame: pd.DataFrame):
    """OHLCV frame -> the positional row list build_df expects:
    [date, open, high, low, close, volume], oldest first."""
    try:
        frame = frame.dropna(subset=["Close"])
    except KeyError:
        return None
    if frame.empty:
        return None
    rows = []
    for idx, row in frame.iterrows():
        day = idx.date() if hasattr(idx, "date") else idx
        rows.append([day, row.get("Open"), row.get("High"), row.get("Low"), row["Close"], row.get("Volume", 0)])
    return rows


def _extract(batch: pd.DataFrame, ticker: str):
    """Pull one ticker's OHLCV frame out of a (possibly multi-ticker) download."""
    if batch is None or batch.empty:
        return None
    if isinstance(batch.columns, pd.MultiIndex):
        if ticker in batch.columns.get_level_values(0):
            frame = batch[ticker]
        elif ticker in batch.columns.get_level_values(1):
            frame = batch.xs(ticker, axis=1, level=1)
        else:
            return None
    else:
        frame = batch
    return _rows_from_frame(frame)


_stooq_strikes = 0  # stooq sits behind a JS bot-check as of Sep 2026; give up after 3 non-CSV replies


def fetch_stooq(ticker: str, fromdate: datetime.date, todate: datetime.date):
    """Fallback daily candles from stooq.com (free CSV, no key). Split-adjusted
    only, but it sometimes still carries names Yahoo has dropped."""
    global _stooq_strikes
    if _stooq_strikes >= 3:
        return None
    url = (
        f"https://stooq.com/q/d/l/?s={ticker.lower()}.us"
        f"&d1={fromdate:%Y%m%d}&d2={todate:%Y%m%d}&i=d"
    )
    try:
        response = requests.get(url, timeout=30)
        time.sleep(0.3)  # stooq enforces a daily hit limit, be polite
        if response.status_code != 200 or not response.text.startswith("Date"):
            _stooq_strikes += 1
            if _stooq_strikes == 3:
                print("Stooq is not serving CSV (bot check / limit), disabling fallback for this run")
            return None
        _stooq_strikes = 0
        frame = pd.read_csv(io.StringIO(response.text))
        if frame.empty or "Close" not in frame.columns:
            return None
        rows = []
        for record in frame.itertuples():
            rows.append(
                [
                    datetime.date.fromisoformat(record.Date),
                    record.Open,
                    record.High,
                    record.Low,
                    record.Close,
                    getattr(record, "Volume", 0),
                ]
            )
        return rows
    except Exception:
        return None


class UsAnalyzer(DefaultAnalyzer):
    def __init__(self):
        self.last_failures = []
        self.stooq_rescues = []

    def args_for_api(self):
        print("Using YFINANCE API (Stooq fallback)")
        return None, None  # no session / instrument dict needed

    def get_market_open_dates(self, *, start: datetime.date, duration: int, instrument_dict: dict = None, obj=None) -> list:
        """One SPY download gives the whole trading calendar - no per-day
        probing like the India side needs. First open day at/after each
        candidate, stepping `duration` days; a 7-day window covers weekends
        and holiday clusters (same intent as the 4-day probe on INFY)."""
        today = datetime.date.today()
        spy = yf.download(
            CALENDAR_TICKER,
            start=start.isoformat(),
            end=(today + datetime.timedelta(days=1)).isoformat(),
            progress=False,
            auto_adjust=True,
        )
        trading_days = sorted({idx.date() if hasattr(idx, "date") else idx for idx in spy.index})

        dates, candidate = [], start
        while candidate <= today:
            open_day = next((day for day in trading_days if day >= candidate), None)
            if open_day is not None and (open_day - candidate).days <= 7:
                dates.append(open_day)
            candidate += datetime.timedelta(days=duration)
        return dates

    def get_target_scripts(self, date: datetime.date) -> list:
        tickers = sorted(to_yahoo(ticker) for ticker in constituents_on(date))
        print(f"Universe on {date} from snapshot map: {len(tickers)} tickers")
        return tickers

    def get_df_from_date_back_to_date_ahead(
        self, scripts: list, start: datetime.date, fromdate: datetime.date, todate: datetime.date,
        instrument_dict: dict = None, obj=None,
    ) -> pd.DataFrame:
        self.last_failures, self.stooq_rescues = [], []
        df_new = pd.DataFrame()
        total = len(scripts)

        for position in range(0, total, CHUNK_SIZE):
            chunk = scripts[position : position + CHUNK_SIZE]
            print(f"AI analyzing {position + 1}-{position + len(chunk)} of {total}")
            try:
                batch = yf.download(
                    chunk,
                    start=fromdate.isoformat(),
                    end=(todate + datetime.timedelta(days=1)).isoformat(),  # yfinance end is exclusive
                    group_by="ticker",
                    auto_adjust=True,
                    progress=False,
                    threads=True,
                )
            except Exception as error:
                print(f"yfinance batch failed ({error}), trying Stooq per ticker for this chunk")
                batch = pd.DataFrame()

            for ticker in chunk:
                rows = _extract(batch, ticker)
                if rows is None:
                    rows = fetch_stooq(ticker, fromdate, todate)
                    if rows is not None:
                        self.stooq_rescues.append(ticker)

                new_data = build_df(rows, start, ticker, fromdate, todate) if rows is not None else None
                if new_data is not None:
                    df_new = pd.concat([df_new, new_data], axis=0, ignore_index=True)
                else:
                    self.last_failures.append(ticker)

            time.sleep(1)  # keep Yahoo happy between chunks

        fetched = total - len(self.last_failures)
        print(
            f"fetched {fetched} of {total} tickers "
            f"({len(self.stooq_rescues)} rescued via Stooq); "
            f"{len(self.last_failures)} failed - survivorship bias, keep visible: {self.last_failures}"
        )
        return df_new
