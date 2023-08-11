from analytics_live import get_excel_from_historical_date_to_current_ahead
from utils import get_dates
from scripts import scripts
import time
from datetime import date, timedelta
from api_angel import loginAngel, instrumentList

dates = get_dates(date(2023, 8, 11))
print(dates)

start_time = time.perf_counter()
print(time.perf_counter())

# need jwtToken & instrument_list first
obj = loginAngel()
print(time.perf_counter())
instrument_list = instrumentList()
print(time.perf_counter())

for start_date in [dates[0]]:
    date_back = start_date - timedelta(days=30 * 165)
    data = get_excel_from_historical_date_to_current_ahead(scripts, start_date, date_back, obj, instrument_list)
    print(data)

finish_time = time.perf_counter()

print(f"Finished in {round((finish_time - start_time), 2)} Seconds(s)")
