"""
US pipeline driver - mirrors cagr/main.py, run via run.py.

Per start date: universe from the snapshot map -> candles via yfinance ->
build_df math -> rank by 9-month return -> expanding avg of the 1-yr-forward
return -> Excel. Fetch failures land in fetch-failures-<date>.txt so
survivorship bias is on the record for every run.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

import pandas as pd

HERE = Path(__file__).resolve().parent
sys.path.append(str(HERE.parent / "cagr"))

from utils import calculate_execution_time  # noqa: E402

from us_analyzer import UsAnalyzer  # noqa: E402


def get_analytics(*, folder_path: str, from_to: list) -> pd.DataFrame:
    """Same shape as cagr/df_helper.get_analytics, but only reads the
    stock-returns-*.xlsx result files - a leftover aaaa.xlsx from an earlier
    run can therefore never crash a rerun."""
    result_df = pd.DataFrame()

    for file_name in sorted(os.listdir(folder_path)):
        if not (file_name.startswith("stock-returns-") and file_name.endswith(".xlsx")):
            continue
        df = pd.read_excel(os.path.join(folder_path, file_name))

        new_df = pd.DataFrame(
            {
                "date": df["date"],
                "date_ahead": df["date_ahead"],
                "Duration": pd.to_datetime(df["date_ahead"], format="%d-%m-%Y")
                - pd.to_datetime(df["date"], format="%d-%m-%Y"),
                **{f"{i + 1}": df["return_ahead_avg"].iloc[i] for i in range(from_to[0] - 1, from_to[1])},
            }
        )
        result_df = pd.concat([result_df, new_df], axis=0, ignore_index=True)

    result_df = result_df.drop_duplicates()
    result_df = result_df.reset_index(drop=True)
    result_df.index = result_df.index + 1
    return result_df


@calculate_execution_time
def main_process(modvar, max_dates: int = None, limit_tickers: int = None) -> None:
    ai = UsAnalyzer()

    obj, instrument_dict = ai.args_for_api()
    dates = ai.get_market_open_dates(
        start=modvar.start, duration=modvar.forward_days, instrument_dict=instrument_dict, obj=obj
    )
    if max_dates:
        dates = dates[:max_dates]
    print(dates)

    for start_date in dates:
        # change state of modvar for start, fromdate, todate
        modvar.start = start_date
        scripts = ai.get_target_scripts(start_date)
        if limit_tickers:
            scripts = scripts[:limit_tickers]

        df = ai.get_df_from_date_back_to_date_ahead(
            scripts, start_date, modvar.fromdate, modvar.todate, instrument_dict, obj
        )
        if df.empty:
            print(f"no usable data at all for {start_date}, skipping")
            continue

        df = ai.df_sort_n_index_reset(df)
        df = ai.df_get_rolling_avg_of_return_ahead(df)
        df.to_excel(f"{modvar.folder_path}/stock-returns-1yr-{start_date}.xlsx")

        # keep survivorship bias on the record, per run
        with open(f"{modvar.folder_path}/fetch-failures-{start_date}.txt", "w") as file:
            file.write(
                f"{len(ai.last_failures)} of {len(scripts)} tickers had no usable data "
                f"(mostly delisted names - survivorship bias)\n"
            )
            file.write("\n".join(ai.last_failures))
            if ai.stooq_rescues:
                file.write(f"\n\nrescued via Stooq ({len(ai.stooq_rescues)}):\n")
                file.write("\n".join(ai.stooq_rescues))

    # use this when researching multiple dates
    if len(dates) > 1:
        result_df = get_analytics(folder_path=modvar.folder_path, from_to=[5, 20])
        result_df.to_excel(f"{modvar.folder_path}/aaaa.xlsx")
        print(result_df)
