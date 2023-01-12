import http.client, mimetypes, json, re
import datetime, requests
import pyotp
import time
from decouple import config


# ANGEL BROKING API
# https://smartapi.angelbroking.com/docs/ResponseStructure
# The instrument list API returns a gzipped CSV dump of instruments across all exchanges that can be imported into a database.
# The dump is generated once every day and hence last_price is not real time.
# Retrieve the CSV dump of all tradable instruments in json format


# scriptid = 'TECHM'
def confirm_script_exchange(scriptid):
    instrument_list =  requests.get('https://margincalculator.angelbroking.com/OpenAPI_File/files/OpenAPIScripMaster.json').json()

    # get SCRIPTID from database of eq_stocks and convert them into stock_symbol
    stock_symbol = str(scriptid) + str('-EQ')

    exchange =''
    for data in instrument_list:
        if data['symbol'] == stock_symbol:
            if data['exch_seg']:
                exchange = data['exch_seg']
        # some stocks are in different trading segment. hence api not giving anything. SO set NSE by default
        else:
            exchange = 'NSE'

    return exchange


# for EOD Data in Angel_API
API_KEY = config('API_KEY')
CLIENTCODE = config('CLIENTCODE')
PASSWORD = config('PASSWORD')
ENABLE_TOTP = config('ENABLE_TOTP')


# first we need to login n get jwtToken
# only login if needed to get jwtToken, O(1) via API
def loginAngel():
    # for TOTP generation
    totp = pyotp.TOTP(ENABLE_TOTP)
    totp_now =totp.now()

    conn = http.client.HTTPSConnection(
        "apiconnect.angelbroking.com"
        )

    payload = "{\n\"clientcode\":\"%s\",\n\"password\":\"%s\"\n,\n\"totp\":\"%s\"\n}" %(CLIENTCODE, PASSWORD, totp_now)
    headers = {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
        'X-UserType': 'USER',
        'X-SourceID': 'WEB',
        'X-ClientLocalIP': 'CLIENT_LOCAL_IP',
        'X-ClientPublicIP': 'CLIENT_PUBLIC_IP',
        'X-MACAddress': 'MAC_ADDRESS',
        'X-PrivateKey': API_KEY
        }
    conn.request("POST", "/rest/auth/angelbroking/user/v1/loginByPassword", payload, headers)

    res = conn.getresponse()
    data = res.read()
    # print(data.decode("utf-8"))
    d = json.loads(data)
    # printing error only
    if d['status'] == False:
        print(d)
    # print(d['data']['jwtToken'])
    # print(d['data']['refreshToken'])

    jwtToken = d['data']['jwtToken']
    return jwtToken


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
def historical_angel(symboltoken, fromdate, todate, jwtToken):

    authorization = 'Bearer' + ' ' + str(jwtToken)
    conn = http.client.HTTPSConnection("apiconnect.angelbroking.com")
    payload = "{\r\n     \"exchange\": \"NSE\",\r\n \"symboltoken\": \"" + str(symboltoken) +" \",\r\n     \"interval\": \"FIFTEEN_MINUTE\",\r\n \"fromdate\": \"" + str(fromdate) +" 00:00\",\r\n     \"todate\": \"" + str(todate) +" 15:30\"\r\n}"
    print(payload)

    headers = {
        'X-PrivateKey': API_KEY ,
        'Accept': 'application/json',
        'X-SourceID': 'WEB',
        'X-ClientLocalIP': 'CLIENT_LOCAL_IP',
        'X-ClientPublicIP': 'CLIENT_PUBLIC_IP',
        'X-MACAddress': 'MAC_ADDRESS',
        'X-UserType': 'USER',
        'Authorization': authorization,
        'Accept': 'application/json',
        'X-SourceID': 'WEB',
        'Content-Type': 'application/json'
    }
    conn.request("POST", "/rest/secure/angelbroking/historical/v1/getCandleData", payload, headers)
    res = conn.getresponse()
    data = res.read()
    print(data.decode("utf-8"))
    d = json.loads(data)

    # print(d['data'])
    return d['data']


# this is the main function to be called
def getDataAPI(scriptid, fromdate, todate, jwtToken, instrument_list):
    # this is search from hash Table ie, JSON O(1)
    symboltoken = scriptToken(scriptid, instrument_list)

    # it will give:
    # [['2022-05-05T00:00:00+05:30', 1560.05, 1589.4, 1557.45, 1585.15, 6144870], ['2022-05-06T00:00:00+05:30', 1550.0, 1561.85, 1535.05, 1542.85, 6171472]]
    # it should be O(1) via API.. don't know internal of SmartAPI
    closing_list = historical_angel(symboltoken, fromdate, todate, jwtToken)

    return closing_list


# # ---------------------------- TESTING PURPOSE ONLY------------------------
fromdate = '2022-11-01'
todate = '2022-11-05'

# # scripts = ['ADANIENT', 'ADANIPORTS', 'APOLLOHOSP', 'ASIANPAINT', 'AXISBANK', 'BAJAJ-AUTO', 'BAJFINANCE', 'BAJAJFINSV', 'BPCL', 'BHARTIARTL', 'BRITANNIA', 'CIPLA', 'COALINDIA', 'DIVISLAB', 'DRREDDY', 'EICHERMOT', 'GRASIM', 'HCLTECH', 'HDFCBANK', 'HDFCLIFE', 'HEROMOTOCO', 'HINDALCO', 'HINDUNILVR', 'HDFC', 'ICICIBANK', 'ITC', 'INDUSINDBK', 'INFY', 'JSWSTEEL', 'KOTAKBANK', 'LT', 'M&M', 'MARUTI', 'NTPC', 'NESTLEIND', 'ONGC', 'POWERGRID', 'RELIANCE', 'SBILIFE', 'SBIN', 'SUNPHARMA', 'TCS', 'TATACONSUM', 'TATAMOTORS', 'TATASTEEL', 'TECHM', 'TITAN', 'UPL', 'ULTRACEMCO', 'WIPRO']


# # # This is value n growth basket research automation
# # scripts = ['ADANIENT', 'ADANITRANS', 'APLAPOLLO', 'TRIDENT', 'PERSISTENT', 'LAURUSLABS', 'TATAELXSI', 'JSL', 'JINDALPOLY', 'NAVINFLUOR', 'MINDTREE', 'JBCHEPHARM', 'SRF', 'GUJGASLTD', 'KPRMILL', 'COFORGE', 'JKCEMENT', 'ICIL', 'TATACOMM', 'HFCL', 'APOLLOHOSP', 'JSWENERGY', 'GRANULES', 'BSOFT', 'LINDEINDIA', 'LTI', 'LALPATHLAB', 'REDINGTON', 'RELAXO', 'PIIND', 'SCI', 'MUTHOOTFIN', 'SPLPETRO', 'ALLCARGO', 'TIMKEN', 'LTTS', 'CENTURYPLY']

# scripts = ['AARTIDRUGS', 'ABBOTINDIA', 'ADANIENT', 'ADANITRANS', 'AKZOINDIA', 'ALLCARGO', 'APLAPOLLO', 'APOLLOHOSP', 'ASIANPAINT', 'BALAMINES', 'BALRAMCHIN', 'BERGEPAINT', 'BRITANNIA', 'BSE', 'BSOFT', 'CAPLIPOINT', 'CENTURYPLY', 'CHAMBLFERT', 'CHOLAFIN', 'COFORGE', 'CRISIL', 'DABUR', 'DEEPAKNTR', 'DMART', 'EICHERMOT', 'GLAXO', 'GODREJCP', 'GPIL', 'GRANULES', 'GUJGASLTD', 'HDFCLIFE', 'HFCL', 'HINDUNILVR', 'ICICIGI', 'ICICIPRULI', 'ICIL', 'INDIGO', 'ITC', 'JBCHEPHARM', 'JINDALPOLY', 'JKCEMENT', 'JSL', 'JSLHISAR', 'JSWENERGY', 'JUBLFOOD', 'KANSAINER', 'KEI', 'KNRCON', 'KPRMILL', 'KRBL', 'LALPATHLAB', 'LAURUSLABS', 'LINDEINDIA', 'LTI', 'LTTS', 'LUXIND', 'MCDOWELL-N', 'MCX', 'MINDTREE', 'MUTHOOTFIN', 'NAVINFLUOR', 'NESTLEIND', 'NIACL', 'PAGEIND', 'PERSISTENT', 'PFIZER', 'PGHH', 'PIIND', 'REDINGTON', 'RELAXO', 'SBILIFE', 'SCI', 'SPICEJET', 'SRF', 'SUNPHARMA', 'SUPPETRO',
# 'SUPREMEIND', 'TASTYBITE', 'TATACOMM', 'TATAELXSI', 'TATAMOTORS', 'TCIEXP', 'TECHM', 'THYROCARE', 'TIMKEN', 'TITAN', 'TRIDENT', 'TRIVENI', 'UBL', 'VAIBHAVGBL', 'VBL', 'VENKEYS', 'VSTIND', 'ZYDUSWELL']

scripts = ['JINDALPOLY', 'SCI', 'MUTHOOTFIN', 'REDINGTON']

# need jwtToken & instrument_list first
jwtToken = loginAngel()
instrument_list = instrumentList()

# it will give:
# [['2022-05-05T00:00:00+05:30', 1560.05, 1589.4, 1557.45, 1585.15, 6144870], ['2022-05-06T00:00:00+05:30', 1550.0, 1561.85, 1535.05, 1542.85, 6171472]]
for i in scripts:
  yo = getDataAPI(i, fromdate, todate, jwtToken, instrument_list)
  print(type(yo))
  print(i)
  # print(yo)
  print(yo)
  print('-------')
  time.sleep(0.2)
