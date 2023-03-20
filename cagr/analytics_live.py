# using this research model right now
'''Script
cmp
Date
mp_5yr_back
date_5yr_back
return_5_yrs
mp_1yr_ahead
date_1yr_ahead
return_5_yr_from_1yr_ahead'''

from datetime import timedelta, date
from api_angel import loginAngel, instrumentList, getDataAPI
import pandas as pd
from scripts import scripts
import time


def get_excel(scripts, start, end):
    df = pd.DataFrame()

    # need jwtToken & instrument_list first
    obj = loginAngel()
    instrument_list = instrumentList()

    # creating dates
    date_back = start - timedelta(days=365 + 1)
    date_back_end= date_back + timedelta(days=5)

    # date_ahead = start + timedelta(days=365*2 + 1)
    # date_ahead_end= date_ahead + timedelta(days=5)

    # date_5yr_back_from_1yr_ahead = date_1yr_ahead - timedelta(days=365*4 + 1)
    # date_5yr_back_from_1yr_ahead_end= date_5yr_back_from_1yr_ahead + timedelta(days=5)

    df_new = pd.DataFrame()

    for scriptid in scripts:
        print(f'Fetching {scripts.index(scriptid) + 1} of {len(scripts)}.')
        # for cmp
        try:
            data = getDataAPI(scriptid, start, end, obj, instrument_list)
            df = pd.DataFrame(data)
            cmp = df.iloc[0, 4]
            time.sleep(0.35)
        except:
            print('No Data')

        # for mp_1yr_back
        try:
            data_back = getDataAPI(scriptid, date_back, date_back_end, obj, instrument_list)
            df_back = pd.DataFrame(data_back)
            mp_back = df_back.iloc[0, 4]
            return_from_back = round((((cmp / mp_back)**(1/1)) -1) * 100, 1)
            time.sleep(0.35)
        except:
            print('No Data')
            mp_back = 'No Data'
            return_from_back = 'Nothing'

        # for mp_1yr_ahead
        # try:
        #     data_ahead = getDataAPI(scriptid, date_ahead, date_ahead_end, obj, instrument_list)
        #     df_ahead = pd.DataFrame(data_ahead)
        #     mp_ahead = df_ahead.iloc[0, 4]
        #     return_ahead = round((((mp_ahead / cmp)) -1) * 100, 1)
        #     time.sleep(0.35)
        # except:
        #     print('No Data')
        #     mp_ahead = 'No Data'
        #     return_ahead = 'Nothing'

        # for mp_5yr_back_from_1yr_ahead
        # try:
        #     data_1_5 = getDataAPI(scriptid, date_5yr_back_from_1yr_ahead, date_5yr_back_from_1yr_ahead_end, obj, instrument_list)
        #     df_1_5 = pd.DataFrame(data_1_5)
        #     mp_5yr_back_from_1yr_ahead = df_1_5.iloc[0, 4]
        #     return_5yr_back_from_1yr_ahead = round((((mp_1yr_ahead / mp_5yr_back_from_1yr_ahead)**(1/4)) -1) * 100, 1)
        #     time.sleep(0.35)
        # except:
        #     print('No Data')
        #     mp_5yr_back_from_1yr_ahead = 'No Data'
        #     return_5yr_back_from_1yr_ahead = 'Nothing'

        # Create a new DataFrame with the new row and same column names

        new_row = pd.DataFrame({
                        "Script": [scriptid],
                        "CMP": [cmp],
                        "Date": [start],
                        "mp_1yr_back": [mp_back],
                        "date_1yr_back": [date_back],
                        "return_from_back": [return_from_back],
                        # "mp_2yr_ahead": [mp_ahead],
                        # "date_2yr_ahead": [date_ahead],
                        # "return_ahead": [return_ahead],
                        # "mp_4yr_back_from_1yr_ahead": [mp_5yr_back_from_1yr_ahead],
                        # "date_4yr_back_from_1yr_ahead": [date_5yr_back_from_1yr_ahead],
                        # "return_4yr_back_from_1yr_ahead": [return_5yr_back_from_1yr_ahead],
                    })

        # Concatenate the two DataFrames along the rows (axis=0)
        df_new = pd.concat([df_new, new_row], axis=0, ignore_index=True)

    df_new.to_excel(f"research/1yr/stock-returns-1yr-{start}.xlsx")
    return df_new



def get_dates(start):
    # because we can get EOD date only so select yesterday as latest
    today = date.today() - timedelta(days=1)
    dates = [start]
    while start <= today:
        start += timedelta(days=365*1 + 1)
        if start <= today:
            dates.append(start)
        else:
            dates.append(today)
    return dates


dates = get_dates(date(2023,3,20))

for i in dates:
    end = i + timedelta(days=3)
    data = get_excel(scripts, i, end)
    print(data)
