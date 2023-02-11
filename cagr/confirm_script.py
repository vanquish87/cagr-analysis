import re
from bs4 import BeautifulSoup
import requests
from scripts import scripts


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
            print(data)
            print(data['token'])
            print(data['name'])
            print(data['exch_seg'])
            return data['token']


instrument_list = instrumentList()
for scriptid in scripts:
    scriptToken(scriptid, instrument_list)
