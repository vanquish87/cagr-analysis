from analytics_live import get_excel_1yr_back_1yr_ahead, get_dates
from scripts import scripts
import time
from datetime import date
from api_angel import loginAngel, instrumentList

"""
Some speed issues coming up because of Angel API
which can be fixed if
clientPublicIp can be set to None in below location n comment original value
I tried n fixed it... I am awesome :)
 File "C:\jimmy\cagr-analysis\env\lib\site-packages\smartapi\smartConnect.py", line 58, in SmartConnect
    clientPublicIp= " " + get('https://api.ipify.org').text
"""

dates = get_dates(date(2023, 6, 30))
print(dates)

start_time = time.perf_counter()

# need jwtToken & instrument_list first
obj = loginAngel()
instrument_list = instrumentList()

for start_date in [dates[0]]:
    data = get_excel_1yr_back_1yr_ahead(scripts, start_date, obj, instrument_list)
    print(data)

finish_time = time.perf_counter()

print(f"Finished in {round((finish_time - start_time), 2)} Seconds(s)")
