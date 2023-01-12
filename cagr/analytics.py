from datetime import timedelta, date
from nsepy import get_history
import pandas as pd
from scripts import scripts

start = date(2022,1,1)
end = date(2022,1,4)


def get_chart(scripts, start, end):
    df = pd.DataFrame()
    # creating dates
    five_years_start = start - timedelta(days=365*5)
    five_years_end= five_years_start + timedelta(days=5)

    ten_years_start = start - timedelta(days=365*10)
    ten_years_end= ten_years_start + timedelta(days=5)

    df_new = pd.DataFrame()

    for scriptid in scripts:
        print(f'Getting {scripts.index(scriptid) + 1} of {len(scripts)}.')
        try:
            data = get_history(symbol=scriptid, start=start, end=end)
            df = pd.DataFrame(data)
            cmp = df.loc[df.index[0], 'Close']
        except:
            pass

        try:
            data_5 = get_history(symbol=scriptid, start=five_years_start, end=five_years_end)
            df_5 = pd.DataFrame(data_5)
            before_5_yr = df_5.loc[df_5.index[0], 'Close']
            return_5_yrs = round((((cmp / before_5_yr)**(1/5)) -1) * 100, 1)
        except:
            before_5_yr = 'No Data'
            return_5_yrs = 'Nothing'

        try:
            data_10 = get_history(symbol=scriptid, start=ten_years_start, end=ten_years_end)
            df_10 = pd.DataFrame(data_10)
            before_10_yr = df_10.loc[df_10.index[0], 'Close']
            return_6_to_10_yrs = round((((before_5_yr / before_10_yr)**(1/5)) -1) * 100, 1)
        except:
            before_10_yr = 'No Data'
            return_6_to_10_yrs = 'Nothing'

        # Create a new DataFrame with the new row and same column names

        new_row = pd.DataFrame({'Script': [scriptid], 'CMP': [cmp], 'before_5_yr': [before_5_yr], 'before_10_yr': [before_10_yr], 'return_5_yrs': [return_5_yrs], 'return_6_to_10_yrs': [return_6_to_10_yrs]})

        # Concatenate the two DataFrames along the rows (axis=0)
        df_new = pd.concat([df_new, new_row], axis=0, ignore_index=True)

    df_new.to_excel("stock_returns.xlsx")
    return df_new


data = get_chart(scripts, start, end)

print(data)