from analytics_live import get_df_from_date_back_to_date_ahead
from utils import get_dates
from scripts import scripts
from datetime import date, timedelta
from api_angel import loginAngel, instrumentList
from utils import df_sort_n_index_reset, calculate_execution_time, df_get_rolling_avg_of_return


@calculate_execution_time
def main():
    dates = get_dates(start=date(2023, 9, 15), duration=13)
    print(dates)

    obj = loginAngel()
    instrument_list = instrumentList()

    for start_date in [dates[0]]:
        date_back = start_date - timedelta(days=30 * 9)
        date_ahead = start_date + timedelta(days=183)

        df = get_df_from_date_back_to_date_ahead(scripts, start_date, date_back, date_ahead, obj, instrument_list)

        df = df_sort_n_index_reset(df)
        
        df = df_get_rolling_avg_of_return(df)

        df.to_excel(f"research/1yr-9mnth-back/stock-returns-1yr-{start_date}.xlsx")

        print(df)


main()


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
