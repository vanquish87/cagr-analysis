# using this research model right now
from datetime import timedelta, date
import pandas as pd
from typing import Optional
from smartapi import SmartConnect
from api_angel import getDataAPI
import time
import os


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
def df_get_rolling_avg_of_return_ahead(df: pd.DataFrame) -> pd.DataFrame:
    df["return_ahead_avg"] = df["return_ahead"].expanding().mean().round(1)
    return df


def get_market_open_dates(*, start: date, duration: int, obj: SmartConnect, instrument_list: list) -> list:
    dates = []
    while start <= date.today():
        for _ in range(4):  # Repeat the check three times
            data = getDataAPI("INFY", start, start, obj, instrument_list)
            if data:
                dates.append(start)
                break
            time.sleep(0.5)
            start += timedelta(days=1)

        start += timedelta(days=duration)
        time.sleep(0.5)

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


def get_analytics(*, folder_path: str, from_to: list) -> pd.DataFrame:
    # Initialize an empty DataFrame to store the results
    result_df = pd.DataFrame()

    # Iterate through each file in the folder
    for file_name in os.listdir(folder_path):
        if file_name.endswith(".xlsx"):
            file_path = os.path.join(folder_path, file_name)

            # Read the Excel file into a DataFrame
            df = pd.read_excel(file_path)

            # Extract relevant columns and create a new DataFrame
            new_df = pd.DataFrame(
                {
                    "date": df["date"],
                    "date_ahead": df["date_ahead"],
                    "Duration": pd.to_datetime(df["date_ahead"], format="%d-%m-%Y")
                    - pd.to_datetime(df["date"], format="%d-%m-%Y"),
                    **{f"{i+1}": df["return_ahead_avg"].iloc[i] for i in range(from_to[0] - 1, from_to[1])},
                }
            )

            # Concatenate the new DataFrame with the result_df
            result_df = pd.concat([result_df, new_df], axis=0, ignore_index=True)

    # Drop duplicate rows in case there are any
    result_df = result_df.drop_duplicates()

    # Reset the index number
    result_df = result_df.reset_index(drop=True)
    # Reset the index number and start from 1
    result_df.index = result_df.index + 1

    return result_df


# result_df = get_analytics(folder_path="research/test/", from_to=[5, 20])
# result_df.to_excel(f"research/test/aaaa.xlsx")
# print(result_df)
