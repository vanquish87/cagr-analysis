from datetime import timedelta, date
from nsepy import get_history
import pandas as pd
from scripts import scripts


def get_chart(scripts, start, end):
    df = pd.DataFrame()
    # creating dates
    start_1yr_ahead = start + timedelta(days=365)
    start_1yr_ahead_end= start_1yr_ahead + timedelta(days=5)

    start_2yr_ahead = start + timedelta(days=365*2)
    start_2yr_ahead_end= start_2yr_ahead + timedelta(days=5)

    df_new = pd.DataFrame()

    for scriptid in scripts:
        print(f'Fetching {scripts.index(scriptid) + 1} of {len(scripts)}.')
        try:
            data = get_history(symbol=scriptid, start=start, end=end)
            df = pd.DataFrame(data)
            start_price = df.loc[df.index[0], 'Close']
        except:
            pass

        try:
            data_1 = get_history(symbol=scriptid, start=start_1yr_ahead, end=start_1yr_ahead_end)
            df_1 = pd.DataFrame(data_1)
            close_1yr_ahead = df_1.loc[df_1.index[0], 'Close']
            return_1_yr_ahead = round((((close_1yr_ahead / start_price)**(1)) -1) * 100, 1)
        except:
            close_1yr_ahead = 'No Data'
            return_1_yr_ahead = 'Nothing'

        try:
            data_2 = get_history(symbol=scriptid, start=start_2yr_ahead, end=start_2yr_ahead_end)
            df_2 = pd.DataFrame(data_2)
            close_2yr_ahead = df_2.loc[df_2.index[0], 'Close']
            return_2_yr_ahead = round((((close_2yr_ahead / start_price)**(1/2)) -1) * 100, 1)
        except:
            close_2yr_ahead = 'No Data'
            return_2_yr_ahead = 'Nothing'

        # Create a new DataFrame with the new row and same column names

        new_row = pd.DataFrame({'Script': [scriptid], 'start_price': [start_price], 'Date': [start], 'close_1yr_ahead': [close_1yr_ahead], 'start_1yr_ahead': [start_1yr_ahead], 'close_2yr_ahead': [close_2yr_ahead], 'start_2yr_ahead': [start_2yr_ahead], 'return_1_yr_ahead': [return_1_yr_ahead], 'return_2_yr_ahead': [return_2_yr_ahead]})

        # Concatenate the two DataFrames along the rows (axis=0)
        df_new = pd.concat([df_new, new_row], axis=0, ignore_index=True)

    df_new.to_excel("research/stock_returns_1yr.xlsx")
    return df_new


start = date(2021,12,31)
end = date(2023,1,7)

data = get_chart(scripts, start, end)
print(data)