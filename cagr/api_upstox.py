import requests, json, os, gzip, time
from scripts import scripts

from concurrent.futures import ThreadPoolExecutor, as_completed
import multiprocessing

"""
API Notes:
1. Base URL: https://api-v2.upstox.com
2. Historical candle endpoint: /historical-candle/{instrument_key}/{interval}/{to_date}/{from_date}
3. Instrument data: https://assets.upstox.com/market-quote/instruments/exchange/NSE.json.gz
4. Historical data for Day interval is limited to 1 year
5. API expects dates in YYYY-MM-DD format
6. Response is in JSON format

Main Function Operation:
1. Loads or creates NSE.json file containing instrument data
2. Uses ThreadPoolExecutor for concurrent API requests
3. Iterates through trading symbols (scripts)
4. For each symbol:
   a. Fetches instrument key
   b. Retrieves EOD candles for specified date range
5. Prints results as they complete (may be out of order due to threading)
6. Measures and reports total execution time

Docs: https://upstox.com/developer/api-documentation/open-api

"""


def calculate_execution_time(func):
    def wrapper(*args, **kwargs):
        start_time = time.perf_counter()
        result = func(*args, **kwargs)
        finish_time = time.perf_counter()
        elapsed_time_ms = (finish_time - start_time) * 1000  # Convert to milliseconds
        print(f"Finished in {elapsed_time_ms:.2f} ms.")
        return result

    return wrapper


def fetch_gzip_data_upstox() -> list:
    response = requests.get("https://assets.upstox.com/market-quote/instruments/exchange/NSE.json.gz")
    if response.status_code == 200:
        return json.loads(gzip.decompress(response.content))
    print(f"Failed to fetch data. Status code: {response.status_code}")
    return []


def get_eq_index_list(instrument_list: list) -> list:
    return [ins for ins in instrument_list if ins["segment"] in ["NSE_EQ", "NSE_INDEX"]]


def create_json(json_file: str) -> list:
    eq_index_list = get_eq_index_list(fetch_gzip_data_upstox())
    with open(json_file, "w") as file:
        json.dump(eq_index_list, file)
    return eq_index_list


def get_instrument_list(json_file: str) -> list:
    try:
        if os.path.exists(json_file):
            with open(json_file, "r") as file:
                return json.load(file)
        return create_json(json_file)
    except Exception as e:
        print(f"Error getting NSE instrument list: {e}")
        return []


def get_instrument_key(trading_symbol: str, instruments: list) -> str:
    return next(
        (instrument["instrument_key"] for instrument in instruments if instrument["trading_symbol"] == trading_symbol),
        None,
    )


def get_EOD_candles(instrument_key: str, interval: str, to_date: str, from_date: str) -> list:
    url = f"https://api-v2.upstox.com/historical-candle/{instrument_key}/{interval}/{to_date}/{from_date}"
    headers = {"Accept": "application/json"}

    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        return response.json()["data"]["candles"]
    else:
        print(f"Error: {response.text}")
        return None


def fetch_eod_candles(trading_symbol, instruments, interval, to_date, from_date):
    instrument_key = get_instrument_key(trading_symbol, instruments)
    if instrument_key:
        stock_EOD_candles = get_EOD_candles(instrument_key, interval, to_date, from_date)
        return trading_symbol, stock_EOD_candles
    return trading_symbol, None


@calculate_execution_time
def main() -> None:
    json_file = "NSE.json"
    instruments = get_instrument_list(json_file)

    # Daily: Retrieve data for the past year, concluding on the endDate.
    interval = "day"
    to_date = "2024-08-13"
    from_date = "2024-08-09"

    with ThreadPoolExecutor(max_workers=multiprocessing.cpu_count()) as executor:
        futures = [
            executor.submit(fetch_eod_candles, symbol, instruments, interval, to_date, from_date) for symbol in scripts
        ]

        for future in as_completed(futures):
            symbol, candles = future.result()
            print(symbol)
            print(candles)


main()
