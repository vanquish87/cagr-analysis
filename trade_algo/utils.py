import sys

# Add the absolute path to the project root
sys.path.append("c:/jimmy/cagr-analysis")

from datetime import date
from cagr.api_angel import loginAngel, instrumentDict, getDataAPI
import pandas as pd


def get_EOD_date(start_date: date, date_back: date, scriptid: str) -> list:
    obj = loginAngel()
    instrument_dict = instrumentDict()
    data = getDataAPI(scriptid, date_back, start_date, obj, instrument_dict)
    return data


def get_formatted_df(data: list) -> pd.DataFrame:
    df = pd.DataFrame(data)
    df = df.rename(
        columns={0: "date", 1: "open", 2: "high", 3: "low", 4: "close", 5: "volume"}
    )
    df["date"] = pd.to_datetime(df["date"]).dt.date
    return df


def calculate_moving_average(df: pd.DataFrame, period: int) -> pd.DataFrame:
    df[f"{period}_day_MA"] = df["close"].rolling(window=period).mean()
    return df


def calculate_atr(df: pd.DataFrame, period: int) -> pd.DataFrame:
    df["high-low"] = df["high"] - df["low"]
    df["high-pc"] = abs(df["high"] - df["close"].shift(1))
    df["low-pc"] = abs(df["low"] - df["close"].shift(1))

    df["tr"] = df[["high-low", "high-pc", "low-pc"]].max(axis=1)
    df[f"{period}_atr"] = df["tr"].rolling(window=period).mean()

    df.drop(["high-low", "high-pc", "low-pc", "tr"], axis=1, inplace=True)

    return df


def create_trade_signal(df: pd.DataFrame) -> pd.DataFrame:
    df["signal"] = ""

    for i in range(1, len(df)):
        if (
            df.at[i - 1, "5_day_MA"] < df.at[i - 1, "8_day_MA"]
            and df.at[i, "5_day_MA"] >= df.at[i, "8_day_MA"]
        ):
            df.at[i, "signal"] = "buy"
        elif (
            df.at[i - 1, "5_day_MA"] > df.at[i - 1, "8_day_MA"]
            and df.at[i, "5_day_MA"] <= df.at[i, "8_day_MA"]
        ):
            df.at[i, "signal"] = "sell"
        else:
            df.at[i, "signal"] = "hold"

    return df
