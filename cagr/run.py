from datetime import date, timedelta
from utils import calculate_execution_time, get_analytics
from models import Api, ModVar
from SmartApi import SmartConnect
from api_angel import loginAngel, instrumentDict
from typing import Protocol, Tuple
from api_angel import getDataAPI
import time
from process_scripts import get_target_isin_date, get_nse_file
from isin import isin_yearly
import pandas as pd
from api_upstox import fetch_eod_candles, get_instrument_dict


def build_df(data: list, start: date, scriptid: str, fromdate: date, todate: date) -> pd.DataFrame:
    try:
        df = pd.DataFrame(data)
        mp_ahead = df.iloc[-1, 4]
        mp_back = df.iloc[0, 4]

        # convert the datetime column of the dataframe to datetime.date objects
        df_dates = pd.to_datetime(df[0]).dt.date
        # filter the dataframe to select rows with datetime values that match the date_to_check
        matching_rows = df[df_dates == start]
        cmp = df.iloc[matching_rows.index, 4].values[0]

        return_from_back = round((((cmp / mp_back) ** (1 / 1)) - 1) * 100, 1)
        return_ahead = round((((mp_ahead / cmp)) - 1) * 100, 1)

        # Calculate rolling average for the 'Volume' column
        df["Volume"] = df[5].rolling(window=30, min_periods=1).mean()
        avg_30day_volume = df.iloc[matching_rows.index, df.columns.get_loc("Volume")].values[0]
        avg_30day_vol_crore = int(avg_30day_volume * cmp / 10000000)

        # Calculate rolling median for the 'Volume' column
        df["Volume_median"] = df[5].rolling(window=30, min_periods=1).median()
        median_30day_volume = df.iloc[matching_rows.index, df.columns.get_loc("Volume_median")].values[0]
        median_30day_vol_crore = int(median_30day_volume * cmp / 10000000)

        return pd.DataFrame(
            {
                "Script": [scriptid],
                "CMP": [cmp],
                "date": [start.strftime("%d-%m-%Y")],  # Format the date as 'dd-mm-yyyy'
                "mp_back": [mp_back],
                "date_back": [fromdate.strftime("%d-%m-%Y")],  # Format the date_back as 'dd-mm-yyyy'
                "return_from_back": [return_from_back],
                "mp_date_ahead": [mp_ahead],
                "date_ahead": [todate.strftime("%d-%m-%Y")],  # Format the date_ahead as 'dd-mm-yyyy'
                "return_ahead": [return_ahead],
                "avg_30day_vol_crore": [avg_30day_vol_crore],
                "median_30day_vol_crore": [median_30day_vol_crore],
            }
        )

    except Exception as e:
        print(f"API didn't fetch any data for {scriptid}: {e}")


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

            time.sleep(0.25)

        return df_new


@calculate_execution_time
def main_process(modvar: ModVar) -> None:
    if modvar.api == Api.ANGEL:
        ai = AngleAnalyzer()
    elif modvar.api == Api.UPSTOX:
        ai = UpstoxAnalyzer()

    obj, instrument_dict = ai.args_for_api()
    dates = ai.get_market_open_dates(start=modvar.start, duration=modvar.forward_days, instrument_dict=instrument_dict, obj=obj)
    print(dates)
    for start_date in dates:
        # change state of modvar for start, fromdate, todate
        modvar.start = start_date
        scripts = ai.get_target_scripts(start_date)[:50]
        df = ai.get_df_from_date_back_to_date_ahead(
            scripts,
            start_date,
            modvar.fromdate,
            modvar.todate,
            instrument_dict,
            obj,
        )
        df = ai.df_sort_n_index_reset(df)
        df = ai.df_get_rolling_avg_of_return_ahead(df)
        df.to_excel(f"{modvar.folder_path}/stock-returns-1yr-{start_date}.xlsx")

    # use this when researching multiple dates
    if len(dates) > 1:
        result_df = get_analytics(folder_path=modvar.folder_path, from_to=[5, 20])
        result_df.to_excel(f"{modvar.folder_path}/aaaa.xlsx")
        print(result_df)


def main() -> None:
    folder_path = "research/1yr-9mnth-back"

    # need to test UPSTOX more on this
    api = Api.ANGEL  # Insert API to use here
    start = date(2025, 1, 2)
    back_days = 30 * 9
    forward_days = 365

    modvar = ModVar(api, folder_path, back_days, forward_days, start)

    main_process(modvar)


if __name__ == "__main__":
    main()
