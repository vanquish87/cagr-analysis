from datetime import timedelta, date
from api_angel import getDataAPI
import pandas as pd
import time
from smartapi import SmartConnect
from utils import df_sort_n_index_reset, get_price


def get_excel_from_date_back_to_1yr_ahead(
    scripts: list, start: date, date_back: date, date_ahead: date, obj: SmartConnect, instrument_list: list
) -> pd.DataFrame:
    """
    Previously took 621.72 Seconds for 501 Scripts
    after refactoring and hitting API only 1 time now
    for same 501 Scripts takes 166.81 Seconds.

    Note: Can't use multiprocessing as API has rate limit
    Further optimization would be welcomed :)
    """

    df_new = pd.DataFrame()

    # to avoid repeated computations
    len_scripts = len(scripts)

    for scriptid in scripts:
        print(f"Neural analyzing {scripts.index(scriptid) + 1} of {len_scripts}: {scriptid}")
        # for cmp
        data = getDataAPI(scriptid, date_back, date_ahead, obj, instrument_list)
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
            avg_30_day_volume = df.iloc[matching_rows.index, df.columns.get_loc("Volume")].values[0]
            avg_30_day_vol_in_crore = round((avg_30_day_volume * cmp / 10000000), 2)

            new_row = pd.DataFrame(
                {
                    "Script": [scriptid],
                    "CMP": [cmp],
                    "Date": [start],
                    "mp_back": [mp_back],
                    "date_back": [date_back],
                    "return_from_back": [return_from_back],
                    "mp_date_ahead": [mp_ahead],
                    "date_ahead": [date_ahead],
                    "return_ahead": [return_ahead],
                    "avg_30_day_vol_in_crore": [avg_30_day_vol_in_crore],
                }
            )

            df_new = pd.concat([df_new, new_row], axis=0, ignore_index=True)

            time.sleep(0.15)

        except Exception as e:
            print("API didn't fetch any data: {}".format(e))
            time.sleep(0.15)

    df_new = df_sort_n_index_reset(df_new)
    df_new.to_excel(f"research/1yr-9mnth-back/stock-returns-1yr-{start}.xlsx")

    return df_new


def get_excel_from_historical_date_to_current_ahead(
    scripts: list, start: date, date_back: date, obj: SmartConnect, instrument_list: list
) -> pd.DataFrame:
    df_new = pd.DataFrame()

    len_scripts = len(scripts)  # to avoid repeated computations

    for scriptid in scripts:
        print(f"Neural analyzing {scripts.index(scriptid) + 1} of {len_scripts}: {scriptid}")
        mp_back = get_price(scriptid, date_back, obj, instrument_list)
        cmp = get_price(scriptid, start, obj, instrument_list)

        try:
            return_from_back = round(((cmp / mp_back) - 1) * 100, 1)
            new_row = pd.DataFrame(
                {
                    "Script": [scriptid],
                    "CMP": [cmp],
                    "Date": [start],
                    "mp_back": [mp_back],
                    "date_back": [date_back],
                    "return_from_back": [return_from_back],
                }
            )

            df_new = pd.concat([df_new, new_row], axis=0, ignore_index=True)
        except Exception as e:
            print("Error with cmp or mp_back: {}".format(e))

    df_new = df_sort_n_index_reset(df_new)
    df_new.to_excel(f"research/historical/stock-returns-{date_back}-to-{start}.xlsx")

    return df_new
