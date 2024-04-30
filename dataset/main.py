import os
import sys

# Get the absolute path of the current script
current_script_path = os.path.abspath(__file__)
# Move one folder above
project_root = os.path.dirname(os.path.dirname(current_script_path))

# Add the absolute path to the project root to sys.path
sys.path.append(project_root)

from cagr.utils import get_market_open_dates
from cagr.api_angel import loginAngel, instrumentDict
from cagr.utils import (
    calculate_execution_time,
)
from cagr.api_angel import getDataAPI

from cagr.scripts import scripts
from df_process import get_formatted_df, add_start_column_to_dataset, add_price_vol_to_dataset
from datetime import date, timedelta
import pandas as pd
import time
from datetime import datetime


@calculate_execution_time
def main() -> None:
    instrument_dict_file = "instrument_data.json"

    obj = loginAngel()
    instrument_dict = instrumentDict(instrument_dict_file)

    dates = get_market_open_dates(start=date(2023, 1, 2), duration=365, obj=obj, instrument_dict=instrument_dict)
    print(dates)

    # Create DataFrame with 'script', 'start', and 'end' columns
    df_dataset = pd.DataFrame(columns=["script", "start", "end"])
    index = 0
    for script in scripts[:100]:
        try:
            print(f"AI analyzing {scripts.index(script) + 1} of {len(scripts[:100])}: {script}")
            date_back = dates[0] - timedelta(days=1995)
            date_ahead = dates[0]
            data = getDataAPI(script, date_back, date_ahead, obj, instrument_dict)
            time.sleep(0.5)

            data_datetime = datetime.strptime(data[0][0], "%Y-%m-%dT%H:%M:%S%z")

            # check if len(data) is of desired length or else stock which has less data ie, new listing is avoided
            if date_back == data_datetime.date():
                # create df from historical data
                df = pd.DataFrame(data)
                df = get_formatted_df(data)
                # process df into actual dataset by adding specific columns
                df_dataset = add_start_column_to_dataset(script, df, df_dataset)
                df_dataset = add_price_vol_to_dataset(df, df_dataset, index)

                # future returns -- target vector calc
                # first get future data
                date_back = dates[0]
                date_ahead = dates[0] + timedelta(days=365)
                data_fut = getDataAPI(script, date_back, date_ahead, obj, instrument_dict)
                time.sleep(0.5)

                # create df from future data
                df_fut = pd.DataFrame(data_fut)
                df_fut = get_formatted_df(df_fut)

                # Add 'target_close' and 'target_volume' columns
                df_dataset.loc[index, "target_date"] = df_fut.iloc[-1]["date"]
                df_dataset.loc[index, "target_close"] = df_fut.iloc[-1]["close"]

                # calc returns
                return_ahead = round((((df_fut.iloc[-1]["close"] / df_fut.iloc[0]["close"])) - 1) * 100, 1)
                df_dataset.loc[index, "target_return"] = return_ahead

                index += 1
        except Exception as e:
            print(e)

    print(df_dataset)

    folder_path = "research/dataset"
    df_dataset.to_excel(f"{folder_path}/a4.xlsx")
