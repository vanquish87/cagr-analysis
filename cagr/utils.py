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


def df_sort_n_index_reset(df: pd.DataFrame) -> pd.DataFrame:
    # Sort the DataFrame in descending order based on the 'return_from_back' column
    df = df.sort_values(by="return_from_back", ascending=False)
    # Reset the index number
    df = df.reset_index(drop=True)
    # Reset the index number and start from 1
    df.index = df.index + 1
    return df


# Add a new column for rolling average of 'return_from_back'
def df_get_rolling_avg_of_return(df: pd.DataFrame) -> pd.DataFrame:
    df["return_from_back_avg"] = df["return_from_back"].expanding().mean().round(1)
    return df


def get_dates(*, start: date, duration: int) -> list:
    # because we can get EOD date only so select yesterday as latest
    yesterday = date.today() - timedelta(days=1)
    dates = [start]
    while start <= yesterday:
        start += timedelta(days=duration)
        if start <= yesterday:
            dates.append(start)
        else:
            dates.append(yesterday)
    return dates


# Define your decorator function
def calculate_execution_time(func):
    def wrapper(*args, **kwargs):
        start_time = time.perf_counter()
        result = func(*args, **kwargs)
        finish_time = time.perf_counter()
        print(f"Finished in {int(finish_time - start_time)} seconds.")
        return result

    return wrapper
