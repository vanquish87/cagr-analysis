# us-cagr

US leg of cagr-analysis. This folder holds the point-in-time S&P 500 membership
map - the US equivalent of `cagr/isin.py`'s `isin_yearly` on the India side.

## Files

| File | What it is |
|---|---|
| `fetch_sp500_wiki.py` | Downloads the current constituents + the historical add/remove ledger from Wikipedia. Cached like `instrument_data.json`; rerun with `--force` to refresh. |
| `sp500_current.json` | Today's 503 constituents (symbol, security name, CIK, date first added). The reconstruction anchor. |
| `sp500_changes.json` | The add/remove ledger (407 rows, 1976 to today) from [Historical components of the S&P 500](https://en.wikipedia.org/wiki/Historical_components_of_the_S%26P_500). |
| `sp500.py` | Reconstruction engine + the API the analyzer will use. |
| `sp500_snapshots.json` | **The snapshot map**: 308 dates, one at every membership change, each with the full sorted ticker list in effect ON that date. |
| `test_snapshots.py` | Tests the map on 50 random dates: ledger consistency, hand-picked known facts, and a cross-check against the independent fja05680/sp500 dataset. |

## How it works

Wikipedia's ledger only records deltas, so membership is rebuilt by starting
from today's constituent list and walking the ledger backwards - each change is
undone (drop the added ticker, restore the removed one) and a snapshot is
recorded at every effective date. For any date in between, the nearest
preceding snapshot applies - same convention as `get_target_isin_date()`.

```python
import datetime
from sp500 import constituents_on, snapshot_map

tickers = constituents_on(datetime.date(2015, 3, 24))   # frozenset of ~502 tickers
full_map = snapshot_map()                               # {date: frozenset}, like isin_yearly
```

CLI:

```
python sp500.py --date 2015-03-24    # print membership on a date
python sp500.py --validate           # data quality report
python sp500.py --write-json         # regenerate sp500_snapshots.json
```

Refresh after a rebalance: `python fetch_sp500_wiki.py --force && python sp500.py --write-json`

## Ticker dialect (important)

Snapshots use **today's symbols**, not the symbol that traded on the day:

- Pure renames never touch the ledger (membership didn't change), so the current
  symbol is carried backwards: pre-2022 snapshots say `META` not `FB`, pre-2020
  say `RTX` not `UTX`, `TT` not `IR`, etc.
- Where the ledger wrote an old symbol, the `RENAMES` table in `sp500.py`
  translates it forward (FB->META, KORS->CPRI, COG->CTRA, JEC->J, ...) so the
  whole map stays in one dialect.

This is deliberate: price APIs in the Yahoo mold key a company's *entire*
history under its current symbol, so a backtest can fetch 2015 data for `META`
directly. The exception is Wikipedia's dot notation (`BRK.B`, `BF.B`) - Yahoo
wants `BRK-B`, so the fetch layer should do `ticker.replace(".", "-")`.

## Data quality (measured, `--validate`)

Jan-1 ticker counts land almost exactly on truth: 500 through the single-class
era (2000-2014), 504-505 in the multi-class years (GOOG/GOOGL, FOX/FOXA,
NWS/NWSA, DISCA/DISCK, UA/UAA), 503 today. But the count alone overstates
early-era quality:

`test_snapshots.py` (50 random dates, seed 42) passes all internal ledger
checks and all 39 hand-picked membership facts, and agrees with the
independent fja05680/sp500 reconstruction as follows:

| Era | Agreement (Jaccard) | Verdict |
|---|---|---|
| 2013 -> today | avg 99.1%, min 95.5% | Solid. Residual diffs are ticker-dialect choices and the two documented gaps below. Use freely. |
| 2008 - 2012 | avg 92.0% | Good. Minor known gaps (e.g. BRK.B's 2010 entry and GM's 2009 exit are missing rows, IR's 2009 Ireland-removal gap). |
| 2000 - 2007 | avg 57.7% | **Composition not trustworthy.** Wikipedia records only ~11 changes for 2000-2006 vs ~150 real ones, so these snapshots are basically the 2007 membership projected backwards. Counts look fine because missing adds and removes cancel out. |

Remaining `--validate` inconsistencies (10) are benign: recycled tickers
(AGN, T, MCK...), the UA/UAA share-class swap, and pre-2000 rows.

If pre-2008 accuracy ever matters, the fix is a proper constituent dataset
(CRSP, Compustat, or one of the reconstructed GitHub datasets) - not more
Wikipedia scraping.

## The US pipeline

| File | What it is |
|---|---|
| `us_analyzer.py` | `UsAnalyzer(DefaultAnalyzer)` - same Protocol as the India analyzers. Universe from `constituents_on(date)` (BRK.B -> BRK-B for Yahoo), candles via yfinance batched 100 tickers at a time, split+dividend adjusted. |
| `main_us.py` | Mirrors `cagr/main.py`: rank by 9-month return, expanding avg of the 1-yr-forward return, Excel per date; `get_analytics` here only reads `stock-returns-*.xlsx`, so a leftover `aaaa.xlsx` can't crash a rerun. |
| `run.py` | Entry point. `python run.py` does yearly starts 2013 -> today (the trustworthy era). Options: `--start`, `--back`, `--forward`, `--max-dates`, `--limit-tickers`, `--folder`. |

```
python run.py --max-dates 1 --limit-tickers 10 --folder research/smoke   # smoke test
python run.py --start 2019-01-10 --max-dates 1                          # one full date
python run.py                                                           # full 2013->today sweep
```

Proven on 2019-01-10 (full 505-ticker universe, 202s): 442 fetched, and the
resulting ranks check out against history (AMD #1 with +95.6% momentum then
+144% forward; AAPL's forward year +104.8%).

### Survivorship bias - read this before trusting any backtest

Yahoo drops price history at delisting, so every acquired/bankrupt member is
unfetchable: 63 of 505 tickers (12.5%) failed for the 2019 universe (CELG,
RTN, TWTR, ATVI, SIVB, STI, PXD...). These are disproportionately companies
that *left* the index, so the computed forward returns skew optimistic.
Every run writes `fetch-failures-<date>.txt` next to the Excel so the gap is
on the record. The clean fix is paid survivorship-free data (Norgate, CRSP,
EODHD); the Stooq fallback in `us_analyzer.py` is currently useless - Stooq
put its CSV endpoint behind a JavaScript bot check (the code self-disables
after 3 non-CSV replies and will start working again if they lift it).

### Later, if fundamentals enter the picture

CIK is already in `sp500_current.json` for current members - it identifies
the SEC filer, not the security, which is why it's carried as metadata
rather than used as the key.
