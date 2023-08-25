# using this research model right now
from datetime import timedelta, date
import pandas as pd
from typing import Optional
from smartapi import SmartConnect
from api_angel import getDataAPI
import time


def get_price(scriptid: list, date_obj: date, obj: SmartConnect, instrument_list: list) -> Optional[float]:
    try:
        data = getDataAPI(scriptid, date_obj, date_obj, obj, instrument_list)
        df = pd.DataFrame(data)
        time.sleep(0.15)
        return df.iloc[0, 4]  # closing price

    except Exception as e:
        print("API didn't fetch any data: {}".format(e))
        time.sleep(0.15)
        return None


def df_sort_n_index_reset(df_new: pd.DataFrame) -> pd.DataFrame:
    # Sort the DataFrame in descending order based on the 'return_from_back' column
    df_new = df_new.sort_values(by="return_from_back", ascending=False)
    # Reset the index number
    df_new = df_new.reset_index(drop=True)
    # Reset the index number and start from 1
    df_new.index = df_new.index + 1

    return df_new


def get_dates(*, start: date, duration: int) -> list:
    # because we can get EOD date only so select yesterday as latest
    today = date.today() - timedelta(days=1)
    dates = [start]
    while start <= today:
        start += timedelta(days=duration)
        if start <= today:
            dates.append(start)
        else:
            dates.append(today)
    return dates
