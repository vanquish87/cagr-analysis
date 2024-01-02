import os
import sys

# Get the absolute path of the current script
current_script_path = os.path.abspath(__file__)
# Move one folder above
project_root = os.path.dirname(os.path.dirname(current_script_path))

# Add the absolute path to the project root to sys.path
sys.path.append(project_root)

import pandas as pd
from datetime import timedelta
from SmartApi import SmartConnect
from cagr.api_angel import getDataAPI
from models import AnalysisParameters


def get_formatted_df(data: list) -> pd.DataFrame:
    df = pd.DataFrame(data)
    df = df.rename(columns={0: "date", 1: "open", 2: "high", 3: "low", 4: "close", 5: "volume"})
    df["date"] = pd.to_datetime(df["date"]).dt.date
    return df


def get_breakout_list(
    scriptid: str, parameters: AnalysisParameters, obj: SmartConnect, instrument_dict: dict, breakout_list: list
):
    try:
        data = getDataAPI(scriptid, parameters.date_back, parameters.start_date, obj, instrument_dict)
        df = get_formatted_df(data)

        # Convert 'date' column to datetime type
        df["date"] = pd.to_datetime(df["date"])

        # Get the unique top n high values and their corresponding dates
        top_highs_df = df.nlargest(parameters.total_high_values, "high")
        top_highs_df = top_highs_df.sort_values(by="high")

        # Find the last date in top_highs_df
        last_date_in_top = top_highs_df["date"].iloc[-1]

        if last_date_in_top >= pd.Timestamp(parameters.start_date - timedelta(days=parameters.start_day_range)):
            # Eliminate rows from df whose 'date' is greater than last_date_in_top
            df_filtered = top_highs_df[top_highs_df["date"] <= last_date_in_top]
            df_filtered = df_filtered.sort_values(by="high", ascending=False)

            # Add a new column 'date_difference' with the calculated differences
            df_filtered["date_difference"] = df_filtered["date"].diff().dt.days

            # Replace NaN with 0 and convert to positive integers
            df_filtered["date_difference"] = df_filtered["date_difference"].fillna(0).astype(int).abs()

            if any(df_filtered["date_difference"] > parameters.ath_before):
                print(scriptid)
                breakout_list.append(scriptid)

    except Exception as e:
        print(f"Df processing failed: {e}")

    return breakout_list
