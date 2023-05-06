# using this research model right now
from datetime import timedelta, date
from api_angel import loginAngel, instrumentList, getDataAPI
import pandas as pd
import time



def get_excel_1yr_back_1yr_ahead(scripts, start):
    '''
    Previously took 621.72 Seconds for 501 Scripts
    after refactoring and hitting API only 1 time now
    for same 501 Scripts takes 166.81 Seconds.
    
    Note: Can't use multiprocessing as API has rate limit
    Further optimization would be welcomed :)
    '''
    # need jwtToken & instrument_list first
    obj = loginAngel()
    instrument_list = instrumentList()

    # creating dates
    date_back = start - timedelta(days=365)
    date_ahead = start + timedelta(days=365 * 1)

    df_new = pd.DataFrame()

    # to avoid repeated computations
    len_scripts = len(scripts)

    for scriptid in scripts:
        print(f"Fetching {scripts.index(scriptid) + 1} of {len_scripts}.")
        # for cmp
        try:
            data = getDataAPI(scriptid, date_back, date_ahead, obj, instrument_list)
            df = pd.DataFrame(data)
            mp_ahead = df.iloc[-1, 4]
            mp_back = df.iloc[0, 4]

            # convert the datetime column of the dataframe to datetime.date objects
            df_dates = pd.to_datetime(df[0]).dt.date
            # filter the dataframe to select rows with datetime values that match the date_to_check
            matching_rows = df[df_dates == start]
            cmp = df.iloc[matching_rows.index, 4].values[0]

            return_from_back = round((((cmp / mp_back) ** (1 / 1)) - 1) * 100, 1)
            return_ahead = round((((mp_ahead / cmp)) - 1) * 100, 1)

            time.sleep(0.05)
        except:
            print("API didn't fetch any data, please check the date.")
            cmp = "No cmp Data"
            mp_back = "No mp_back Data"
            return_from_back = "return_from_back is None"
            return_ahead = "return_ahead is None"

        new_row =  pd.DataFrame(
            {
                "Script": [scriptid],
                "CMP": [cmp],
                "Date": [start],
                "mp_1yr_back": [mp_back],
                "date_1yr_back": [date_back],
                "return_from_back": [return_from_back],
                "mp_1yr_ahead": [mp_ahead],
                "date_1yr_ahead": [date_ahead],
                "return_ahead": [return_ahead],
            }
        )

        # Concatenate the two DataFrames along the rows (axis=0)
        df_new = pd.concat([df_new, new_row], axis=0, ignore_index=True)

    df_new.to_excel(f"research/1yr/stock-returns-1yr-{start}.xlsx")
    return df_new


def get_dates(start):
    # because we can get EOD date only so select yesterday as latest
    today = date.today() - timedelta(days=1)
    dates = [start]
    while start <= today:
        start += timedelta(days=365 * 1)
        if start <= today:
            dates.append(start)
        elif start - timedelta(days=365 * 1) != today:
            dates.append(today)
    return dates

