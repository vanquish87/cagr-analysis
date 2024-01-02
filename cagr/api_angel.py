# package import statement
from SmartApi import SmartConnect
from decouple import config
import pyotp, requests, json, os
from datetime import date


def loginAngel() -> SmartConnect:
    obj = SmartConnect(api_key=config("API_KEY"))

    ENABLE_TOTP = config("ENABLE_TOTP")
    totp = pyotp.TOTP(ENABLE_TOTP)
    totp_now = totp.now()

    data = obj.generateSession(config("CLIENTCODE"), config("PASSWORD"), totp_now)
    return obj


# json of all the instrumentList with '-EQ' n 'BE' from Angel_API
# Initial were pulling around 93661 SCRIPTS now down to  2121 with '-EQ' n 'BE'
# This will help in smaller list to iterate hance faster execution
# URL was taking a long time to load.. so to speed up we load from local file if its there
# we need instrument_list only once O(1) via requests
def instrumentDict(instrument_dict_file: json) -> dict:
    try:
        # Check if the file exists
        if os.path.exists(instrument_dict_file):
            with open(instrument_dict_file, "r") as file:
                instrument_dict = json.load(file)
        else:
            # Fetch instrument data from the URL
            instrument_list = requests.get(
                "https://margincalculator.angelbroking.com/OpenAPI_File/files/OpenAPIScripMaster.json"
            ).json()

            # Filter instruments and save to the file
            instrument_dict = {
                instrument["symbol"]: instrument
                for instrument in instrument_list
                if instrument["symbol"].endswith("-EQ") or instrument["symbol"].endswith("-BE")
            }

            with open(instrument_dict_file, "w") as file:
                json.dump(instrument_dict, file)

    except Exception as e:
        print(f"Error getting instrumentList: {e}")
        return None  # Handle the error as needed

    return instrument_dict


# then we need a symboltoken with the help of scriptid
# This is a search in instrument_dict with O(1)
# but with 2121 SCRIPTS down from 93661 :)
def scriptToken(scriptid: str, instrument_dict: dict) -> str:
    if scriptid + "-EQ" in instrument_dict:
        return instrument_dict[scriptid + "-EQ"]["token"]
    if scriptid + "-BE" in instrument_dict:
        return instrument_dict[scriptid + "-BE"]["token"]

    print("Script ID not found")


# historical data
# Max Days in one Request ONE_DAY = 500, refer to smartapi docs
# scriptid = 'INFY', fromdate = '2022-05-05', todate = '2022-05-06'
def historical_angel(symboltoken: str, fromdate: date, todate: date, obj: SmartConnect) -> dict:
    try:
        historicParam = {
            "exchange": "NSE",
            "symboltoken": symboltoken,
            "interval": "ONE_DAY",
            "fromdate": f"{fromdate} 00:00",
            "todate": f"{todate} 15:30",
        }
        data = obj.getCandleData(historicParam)
        if data["message"] != "SUCCESS":
            print(data)
        return data
    except Exception as e:
        print("Historic Api failed: {}".format(e))
        return {}


# this is the main function to be called
def getDataAPI(scriptid: str, fromdate: date, todate: date, jwtToken: SmartConnect, instrument_dict: dict) -> list:
    symboltoken = scriptToken(scriptid, instrument_dict)
    # it will give:
    # {'status': True, 'message': 'SUCCESS', 'errorcode': '', 'data': [['2023-01-02T00:00:00+05:30', 181.0, 189.3, 180.85, 187.7, 2692157]]}
    candle_data = historical_angel(symboltoken, fromdate, todate, jwtToken)
    return candle_data.get("data")


# --------------------------- TESTING PURPOSE ONLY------------------------
# fromdate = date(2023,1,4)
# todate = date(2023,1,6)

# # need jwtToken & instrument_list first
# obj = loginAngel()
# instrument_list = instrumentList()
# print(len(instrument_list))
# print(type(instrument_list))

# scripts = ['JINDALPOLY', 'ITC']
# for i in scripts:
#     print(f'Fetching {scripts.index(i) + 1} of {len(scripts)}.')
#     yo = getDataAPI(i, fromdate, todate, obj, instrument_list)
#     print(type(yo))
#     print(i)
#     print(yo)
#     print('-------')
#     time.sleep(0.15)
