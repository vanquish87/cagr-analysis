from datetime import date
import pandas as pd


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
