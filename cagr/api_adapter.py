from api_upstox import fetch_eod_candles, get_instrument_list
from api_angel import getDataAPI
from SmartApi import SmartConnect
from api_angel import loginAngel, instrumentDict

from enum import Enum
from datetime import date
from typing import List, Tuple, Optional


class Api(Enum):
    UPSTOX = 1
    ANGEL = 2


# Adapter function to switch between APIs
# UPSTOX doesn't work on current trading day
# ANGEL doesn't get more than 2000 days
def adapter(
    api: Api,
    scriptid: str,
    fromdate: date,
    todate: date,
    jwtToken: SmartConnect,
    instrument_dict: dict,
    instruments: list,
) -> List:
    if api == Api.UPSTOX:
        interval = "day"
        fromdate_str = fromdate.strftime("%Y-%m-%d")
        todate_str = todate.strftime("%Y-%m-%d")

        scriptid, stock_EOD_candles = fetch_eod_candles(scriptid, instruments, interval, fromdate_str, todate_str)
        return stock_EOD_candles[::-1] if stock_EOD_candles else None

    elif api == Api.ANGEL:
        return getDataAPI(scriptid, fromdate, todate, jwtToken, instrument_dict)


def get_args_for_api(api: Api) -> Tuple[Optional[SmartConnect], Optional[dict], Optional[list]]:
    obj, instrument_dict, instruments = None, None, None

    if api == Api.ANGEL:
        print("Using ANGEL API")
        obj = loginAngel()
        instrument_dict_file = "instrument_data.json"
        instrument_dict = instrumentDict(instrument_dict_file)
    elif api == Api.UPSTOX:
        print("Using UPSTOX API")
        json_file = "NSE.json"
        instruments = get_instrument_list(json_file)

    return obj, instrument_dict, instruments
