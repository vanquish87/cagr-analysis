import requests, json, os, gzip, time
from scripts import scripts

# from concurrent.futures import ThreadPoolExecutor, as_completed
# import multiprocessing
from typing import List, Tuple, Optional

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


def get_instrument_key(scriptid: str, instruments: list) -> str:
    return next(
        (instrument["instrument_key"] for instrument in instruments if instrument["trading_symbol"] == scriptid),
        None,
    )


# Daily: Retrieve data for the past 1 year, concluding on the todate.
# but seems like it works to any length of Day now like I tried from 206 - 2024 it worked!!
def get_EOD_candles(instrument_key: str, interval: str, fromdate: str, todate: str) -> list:
    url = f"https://api-v2.upstox.com/historical-candle/{instrument_key}/{interval}/{todate}/{fromdate}"
    headers = {"Accept": "application/json"}

    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        return response.json()["data"]["candles"]
    else:
        print(f"Error: {response.text}")
        return None


def fetch_eod_candles(
    scriptid: str, instruments: List[dict], interval: str, fromdate: str, todate: str
) -> Tuple[str, Optional[list]]:
    instrument_key = get_instrument_key(scriptid, instruments)

    if not instrument_key:
        print(f"Script ID '{scriptid}' not found.")
        return scriptid, None

    stock_EOD_candles = get_EOD_candles(instrument_key, interval, fromdate, todate)
    return scriptid, stock_EOD_candles


# @calculate_execution_time
# def main() -> None:
#     json_file = "NSE.json"
#     instruments = get_instrument_list(json_file)

#     # Daily: Retrieve data for the past year, concluding on the endDate.
#     # but seems like it works to any length of Day now like I tried from 206 - 2024 it worked!!
#     interval = "day"
#     todate = "2024-08-13"
#     fromdate = "2016-08-09"

#     with ThreadPoolExecutor(max_workers=multiprocessing.cpu_count()) as executor:
#         futures = [
#             executor.submit(fetch_eod_candles, symbol, instruments, interval, fromdate, todate) for symbol in scripts
#         ]

#         for future in as_completed(futures):
#             symbol, candles = future.result()
#             if candles:
#                 print(candles)
#                 print(symbol)
#                 print(candles[0])
#                 print(candles[-1])

#                 print(len(candles))


# main()
