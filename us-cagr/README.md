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

| Era | Verdict |
|---|---|
| 2013 -> today | Solid. Ledger density matches real index turnover (~20-25 changes/yr). Use freely. |
| 2008 - 2012 | Good. Minor known gaps (e.g. BRK.B's 2010 entry and GM's 2009 exit are missing rows, IR's 2009 Ireland-removal gap). |
| 2000 - 2007 | **Composition not trustworthy.** Wikipedia records only ~11 changes for 2000-2006 vs ~150 real ones, so these snapshots are basically the 2007 membership projected backwards. Counts look fine because missing adds and removes cancel out. |

Remaining `--validate` inconsistencies (10) are benign: recycled tickers
(AGN, T, MCK...), the UA/UAA share-class swap, and pre-2000 rows.

If pre-2008 accuracy ever matters, the fix is a proper constituent dataset
(CRSP, Compustat, or one of the reconstructed GitHub datasets) - not more
Wikipedia scraping.

## Next steps

1. A `UsAnalyzer` implementing the same Protocol as `AngleAnalyzer` /
   `UpstoxAnalyzer` (`args_for_api`, `get_market_open_dates`,
   `get_df_from_date_back_to_date_ahead`, ...), with `get_target_scripts(date)`
   = `sorted(constituents_on(date))`.
2. Pick a US daily-candle source (yfinance is the obvious first try; Stooq as
   fallback). Delisted names (LEH, TWTR, SIVB...) won't resolve there - expect
   and tolerate per-ticker fetch failures like the India pipeline already does,
   but count them per run so survivorship bias stays visible.
3. CIK is already in `sp500_current.json` for current members if fundamentals
   (SEC filings) enter the picture later - it identifies the filer, not the
   security, which is why it's carried as metadata rather than used as the key.
