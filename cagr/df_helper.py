from datetime import date
import pandas as pd
import os


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
