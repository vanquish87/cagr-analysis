import requests
import csv
import json
from scripts import scripts
import time

# https://upstox.com/developer/api-documentation/open-api


def calculate_execution_time(func):
    def wrapper(*args, **kwargs):
        start_time = time.perf_counter()
        result = func(*args, **kwargs)
        finish_time = time.perf_counter()
        elapsed_time_ms = (finish_time - start_time) * 1000  # Convert to milliseconds
        print(f"Finished in {elapsed_time_ms:.2f} ms.")
        return result

    return wrapper


def csv_to_dict(csv_file_path: str) -> dict:
    trading_symbol_map = {}
    with open(csv_file_path, "r") as csv_file:
        csv_reader = csv.DictReader(csv_file)
        for row in csv_reader:
            trading_symbol_map[row["tradingsymbol"]] = row["instrument_key"]

    return trading_symbol_map


def get_instrument_key(trading_symbol: str, data_dict: dict) -> str:
    if trading_symbol in data_dict:
        return data_dict[trading_symbol]


@calculate_execution_time
def get_EOD_candles(instrument_key: str, interval: str, to_date: str, from_date: str) -> list:
    url = f"https://api-v2.upstox.com/historical-candle/{instrument_key}/{interval}/{to_date}/{from_date}"

    payload = {}
    headers = {"Api-Version": "2.0", "Accept": "application/json"}
    response = requests.get(url, headers=headers, data=payload)

    if response.status_code == 200:
        data = json.loads(response.text)
        return data["data"]["candles"]
    else:
        print(f"Error: {response.text}")
        return None


def main():
    csv_file_path = r"NSE.csv"
    trading_symbol_map = csv_to_dict(csv_file_path)

    for trading_symbol in scripts:
        instrument_key = get_instrument_key(trading_symbol, trading_symbol_map)
        interval = "day"
        to_date = "2023-11-23"
        from_date = "2023-11-20"

        if instrument_key:
            stock_EOD_candles = get_EOD_candles(instrument_key, interval, to_date, from_date)
            print(trading_symbol)
            print(stock_EOD_candles)


main()
