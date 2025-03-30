from SmartApi import SmartConnect
from api_angel import loginAngel, instrumentDict
from api_angel import getDataAPI
from process_scripts import get_target_isin_date, get_nse_file
from df_helper import build_df
from isin import isin_yearly
from api_upstox import fetch_eod_candles, get_instrument_dict
from typing import Protocol, Tuple
import pandas as pd
import time
from datetime import date, timedelta


class Analyzer(Protocol):
    def args_for_api(self) -> Tuple[SmartConnect, dict]: ...

    def get_market_open_dates(self, *, start: date, duration: int, instrument_dict: dict, obj: SmartConnect) -> list: ...

    def get_df_from_date_back_to_date_ahead(
        self, scripts: list, start: date, fromdate: date, todate: date, instrument_dict: dict, obj: SmartConnect
    ) -> pd.DataFrame: ...

    def get_target_scripts(self, date: date) -> list: ...

    def df_sort_n_index_reset(self, df: pd.DataFrame) -> pd.DataFrame: ...

    def df_get_rolling_avg_of_return_ahead(self, df: pd.DataFrame) -> pd.DataFrame: ...


class DefaultAnalyzer(Analyzer):
    NSE_FILE = "NSE.json"

    def get_target_scripts(self, date: date) -> list:
        isin_date = get_target_isin_date(isin_yearly, date)

        isins = isin_yearly[isin_date]
        print(f"Processed date is {isin_date} has total ISINs: {len(isins)}")

        nse_file = get_nse_file(self.NSE_FILE)

        return sorted(script for script in nse_file if nse_file[script].get("isin") in isins)

    def df_sort_n_index_reset(self, df: pd.DataFrame) -> pd.DataFrame:
        # Sort the DataFrame in descending order based on the 'return_from_back' column
        df = df.sort_values(by="return_from_back", ascending=False)
        # Reset the index number
        df = df.reset_index(drop=True)
        # Reset the index number and start from 1
        df.index = df.index + 1
        return df

    # Add a new column for rolling average of 'return_from_back'
    def df_get_rolling_avg_of_return_ahead(self, df: pd.DataFrame) -> pd.DataFrame:
        df["return_ahead_avg"] = df["return_ahead"].expanding().mean().round(1)
        return df


class AngleAnalyzer(DefaultAnalyzer):
    INSTRUMENT_FILE = "instrument_data.json"

    def args_for_api(self) -> Tuple[SmartConnect, dict]:
        print("Using ANGEL API")
        obj = loginAngel()
        instrument_dict = instrumentDict(self.INSTRUMENT_FILE)
        return obj, instrument_dict

    def get_market_open_dates(self, *, start: date, duration: int, instrument_dict: dict, obj: SmartConnect) -> list:
        dates = []
        while start <= date.today():
            for _ in range(4):  # Repeat the check three times

                data = getDataAPI("INFY", start, start, obj, instrument_dict)
                if data:
                    dates.append(start)
                    break
                time.sleep(0.5)
                start += timedelta(days=1)

            start += timedelta(days=duration)
            time.sleep(0.5)

        return dates

    def get_df_from_date_back_to_date_ahead(
        self, scripts: list, start: date, fromdate: date, todate: date, instrument_dict: dict, obj: SmartConnect
    ) -> pd.DataFrame:
        df_new = pd.DataFrame()
        len_scripts = len(scripts)  # to avoid repeated computations

        for scriptid in scripts:
            print(f"AI analyzing {scripts.index(scriptid) + 1} of {len_scripts}: {scriptid}")
            data = getDataAPI(scriptid, fromdate, todate, obj, instrument_dict)
            new_data = build_df(data, start, scriptid, fromdate, todate)

            if new_data is not None:
                df_new = pd.concat([df_new, new_data], axis=0, ignore_index=True)

            time.sleep(0.25)

        return df_new


class UpstoxAnalyzer(DefaultAnalyzer):
    def args_for_api(self) -> Tuple[SmartConnect, dict]:
        print("Using UPSTOX API")
        instrument_dict = get_instrument_dict(self.NSE_FILE)
        return None, instrument_dict

    def get_market_open_dates(self, *, start: date, duration: int, instrument_dict: dict, obj: SmartConnect = None) -> list:
        dates = []
        while start <= date.today():
            for _ in range(4):  # Repeat the check three times
                interval = "day"
                fromdate_str = todate_str = start.strftime("%Y-%m-%d")

                _, data = fetch_eod_candles("INFY", instrument_dict, interval, fromdate_str, todate_str)
                if data:
                    dates.append(start)
                    break
                start += timedelta(days=1)

            start += timedelta(days=duration)

        return dates

    def get_df_from_date_back_to_date_ahead(
        self, scripts: list, start: date, fromdate: date, todate: date, instrument_dict: dict, obj: SmartConnect = None
    ) -> pd.DataFrame:
        df_new = pd.DataFrame()
        len_scripts = len(scripts)  # to avoid repeated computations
        interval = "day"

        for scriptid in scripts:
            print(f"AI analyzing {scripts.index(scriptid) + 1} of {len_scripts}: {scriptid}")

            _, stock_EOD_candles = fetch_eod_candles(
                scriptid,
                instrument_dict,
                interval,
                fromdate.strftime("%Y-%m-%d"),
                todate.strftime("%Y-%m-%d"),
            )
            data = stock_EOD_candles[::-1] if stock_EOD_candles else None

            new_data = build_df(data, start, scriptid, fromdate, todate)

            if new_data is not None:
                df_new = pd.concat([df_new, new_data], axis=0, ignore_index=True)

        return df_new
