from analytics_live import get_excel_from_date_back_to_1yr_ahead, get_dates
from scripts import scripts
import time
from datetime import date, timedelta
from api_angel import loginAngel, instrumentList

"""
Some speed issues coming up because of Angel API
which can be fixed if
clientPublicIp can be set to None in below location n comment original value
I tried n fixed it... I am awesome :)
 File "C:\jimmy\cagr-analysis\env\lib\site-packages\smartapi\smartConnect.py", line 58, in SmartConnect
    clientPublicIp= " " + get('https://api.ipify.org').text
"""

# backtest dates list
# dates = [
#     datetime.date(2007, 1, 2),
#     datetime.date(2008, 1, 3),
#     datetime.date(2009, 1, 5),
#     datetime.date(2010, 1, 5),
#     datetime.date(2011, 1, 6),
#     datetime.date(2012, 1, 7),
#     datetime.date(2013, 1, 7),
#     datetime.date(2014, 1, 8),
#     datetime.date(2015, 1, 9),
#     datetime.date(2016, 1, 11),
#     datetime.date(2017, 1, 11),
#     datetime.date(2018, 1, 12),
#     datetime.date(2019, 1, 14),
#     datetime.date(2020, 1, 15),
#     datetime.date(2021, 1, 15),
#     datetime.date(2022, 1, 17),
# ]

dates = get_dates(date(2023, 7, 14))
print(dates)

start_time = time.perf_counter()

# need jwtToken & instrument_list first
obj = loginAngel()
instrument_list = instrumentList()

for start_date in [dates[0]]:
    date_back = start_date - timedelta(days=30 * 9)
    data = get_excel_from_date_back_to_1yr_ahead(scripts, start_date, date_back, obj, instrument_list)
    print(data)

finish_time = time.perf_counter()

print(f"Finished in {round((finish_time - start_time), 2)} Seconds(s)")
