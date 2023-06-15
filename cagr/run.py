from analytics_live import get_excel_1yr_back_1yr_ahead, get_dates
from scripts import scripts
import time
from datetime import date


dates = get_dates(date(2023, 6, 15))
print(dates)

start_time = time.perf_counter()

for start_date in [dates[0]]:
    data = get_excel_1yr_back_1yr_ahead(scripts, start_date)
    print(data)

finish_time = time.perf_counter()

print(f'Finished in {round((finish_time - start_time), 2)} Seconds(s)')