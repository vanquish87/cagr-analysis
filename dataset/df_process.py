import pandas as pd


def get_formatted_df(data: list) -> pd.DataFrame:
    df = pd.DataFrame(data)
    df = df.rename(columns={0: "date", 1: "open", 2: "high", 3: "low", 4: "close", 5: "volume"})
    df["date"] = pd.to_datetime(df["date"]).dt.date
    return df


def add_start_column_to_dataset(script: str, df: pd.DataFrame, df_dataset: pd.DataFrame) -> pd.DataFrame:
    # Extract relevant columns and create a new DataFrame
    new_row = pd.DataFrame(
        {
            "script": script,
            "start": df["date"].iloc[0],
            "end": df["date"].iloc[-1],
        },
        index=[0],
    )
    return pd.concat([df_dataset, new_row], axis=0, ignore_index=True)


def add_price_vol_to_dataset(df: pd.DataFrame, df_dataset: pd.DataFrame, index: int) -> pd.DataFrame:
    # Iterate over rows of df to construct 'close' and 'volume' columns
    for i in range(len(df)):
        df_dataset.loc[index, f"close_{i+1}"] = df["close"].iloc[i]
        df_dataset.loc[index, f"volume_{i+1}"] = df["volume"].iloc[i]

    return df_dataset
