from datetime import date, timedelta
from nsepy import get_history
import pandas as pd

sbin = get_history(symbol='SBIN', start=date(2015,1,1), end=date(2015,1,2))


df = pd.DataFrame(sbin)
print(df.columns)
print(df)

print(df.loc[df.index[0], 'Close'])
df.reset_index(level=0, inplace=True)
print(df.loc[df.index[0], 'Date'])
print(df.index)

print(date(2015,1,1))
print(type(date(2015,1,1)))
print(date(2015,1,1) - timedelta(days=365*10))
# print(df.loc[df.index[0], 'Date'])
