# package import statement
from smartapi import SmartConnect
from decouple import config
import pyotp, requests, json, os


def loginAngel():
    obj = SmartConnect(api_key=config("API_KEY"))

    ENABLE_TOTP = config("ENABLE_TOTP")
    totp = pyotp.TOTP(ENABLE_TOTP)
    totp_now = totp.now()

    data = obj.generateSession(config("CLIENTCODE"), config("PASSWORD"), totp_now)
    return obj


# json of all the instrumentList with '-EQ' from Angel_API
# Initial were pulling around 93661 SCRIPTS now down to  1915 with '-EQ'
# This will help in smaller list to iterate hance faster execution
# URL was taking a long time to load.. so to speed up we load from local file if its there
# we need instrument_list only once O(1) via requests
def instrumentList():
    instrument_data_file = "instrument_data.json"
    
    # Check if the file exists
    if os.path.exists(instrument_data_file):
        with open(instrument_data_file, "r") as file:
            instrument_list = json.load(file)
        return instrument_list

    instrument_list = requests.get(
        "https://margincalculator.angelbroking.com/OpenAPI_File/files/OpenAPIScripMaster.json"
    ).json()

    # Filter instruments and save to the file
    filtered_instruments = [instrument for instrument in instrument_list if instrument["symbol"].endswith("-EQ")]

    with open(instrument_data_file, "w") as file:
        json.dump(filtered_instruments, file)

    return filtered_instruments


# then we need a symboltoken with the help of scriptid
# This is a search in instrument_list with O(n)
# but with 1915 SCRIPTS down from 93661 :)
def scriptToken(scriptid, instrument_list):
    # get SCRIPTID from database of eq_stocks and convert them into stock_symbol
    stock_symbol = str(scriptid) + str("-EQ")
    for data in instrument_list:
        if data["symbol"] == stock_symbol:
            return data["token"]


# historical data
# Max Days in one Request ONE_DAY = 500, refer to smartapi docs
# scriptid = 'INFY', fromdate = '2022-05-05', todate = '2022-05-06'
def historical_angel(symboltoken, fromdate, todate, obj):
    try:
        historicParam = {
            "exchange": "NSE",
            "symboltoken": symboltoken,
            "interval": "ONE_DAY",
            "fromdate": f"{fromdate} 00:00",
            "todate": f"{todate} 15:30",
        }
        data = obj.getCandleData(historicParam)
        if data['message'] != 'SUCCESS':
            print(data)
        return data
    except Exception as e:
        print("Historic Api failed: {}".format(e))
        return {}


# this is the main function to be called
def getDataAPI(scriptid, fromdate, todate, jwtToken, instrument_list):
    symboltoken = scriptToken(scriptid, instrument_list)
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
