# package import statement
from smartapi import SmartConnect
from decouple import config
import pyotp, requests, time
from datetime import date

def loginAngel():
    obj = SmartConnect(api_key=config('API_KEY'))

    ENABLE_TOTP = config('ENABLE_TOTP')
    totp = pyotp.TOTP(ENABLE_TOTP)
    totp_now =totp.now()

    data = obj.generateSession(config('CLIENTCODE'),config('PASSWORD'),totp_now)
    return obj


# json of all the instrumentList from Angel_API
# we need instrument_list only once O(1) via requests
def instrumentList():
    instrument_list =  requests.get('https://margincalculator.angelbroking.com/OpenAPI_File/files/OpenAPIScripMaster.json').json()
    return instrument_list


# then we need a symboltoken with the help of scriptid
# this is search from hash Table ie, JSON O(1)
def scriptToken(scriptid, instrument_list):
    # get SCRIPTID from database of eq_stocks and convert them into stock_symbol
    stock_symbol = str(scriptid) + str('-EQ')
    for data in instrument_list:
        if data['symbol'] == stock_symbol:
            # print(data)
            # print(data['token'])
            # print(data['name'])
            # print(data['exch_seg'])
            return data['token']


# historical data
# Max Days in one Request ONE_DAY = 2000, refer to smartapi docs
# scriptid = 'INFY', fromdate = '2022-05-05', todate = '2022-05-06'
def historical_angel(symboltoken, fromdate, todate, obj):
    try:
        historicParam={
        "exchange": "NSE",
        "symboltoken": symboltoken,
        "interval": "ONE_DAY",
        "fromdate": f"{fromdate} 00:00",
        "todate": f"{todate} 15:30"
        }
        return obj.getCandleData(historicParam)
    except Exception as e:
        print("Historic Api failed: {}".format(e.message))


# this is the main function to be called
def getDataAPI(scriptid, fromdate, todate, jwtToken, instrument_list):
    # this is search from hash Table ie, JSON O(1)
    symboltoken = scriptToken(scriptid, instrument_list)

    # it will give:
    # {'status': True, 'message': 'SUCCESS', 'errorcode': '', 'data': [['2023-01-02T00:00:00+05:30', 181.0, 189.3, 180.85, 187.7, 2692157]]}
    candle_data = historical_angel(symboltoken, fromdate, todate, jwtToken)
    closing_list = candle_data['data']

    return closing_list


# --------------------------- TESTING PURPOSE ONLY------------------------
# fromdate = date(2023,1,4)
# todate = date(2023,1,6)

# # need jwtToken & instrument_list first
# obj = loginAngel()
# instrument_list = instrumentList()

# scripts = ['JINDALPOLY', 'ITC']
# for i in scripts:
#     print(f'Fetching {scripts.index(i) + 1} of {len(scripts)}.')
#     yo = getDataAPI(i, fromdate, todate, obj, instrument_list)
#     print(type(yo))
#     print(i)
#     print(yo)
#     print('-------')
#     time.sleep(0.15)
