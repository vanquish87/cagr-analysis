from analytics_live import get_excel_1yr_back_1yr_ahead, get_dates
from scripts import scripts
import time
from datetime import date


dates = get_dates(date(2023, 4, 28))

start_time = time.perf_counter()

for i in dates:
    data = get_excel_1yr_back_1yr_ahead(scripts, i)
    print(data)

finish_time = time.perf_counter()

print(f'Finished in {round((finish_time - start_time), 2)} Seconds(s)')