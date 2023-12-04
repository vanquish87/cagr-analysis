from analytics_live import get_df_from_date_back_to_date_ahead
from utils import get_market_open_dates
from scripts import scripts
from datetime import date, timedelta
from api_angel import loginAngel, instrumentDist
from utils import df_sort_n_index_reset, calculate_execution_time, df_get_rolling_avg_of_return_ahead, get_analytics


@calculate_execution_time
def main():
    obj = loginAngel()
    instrument_dict_file = "instrument_data.json"
    instrument_dict = instrumentDist(instrument_dict_file)

    dates = get_market_open_dates(start=date(2023, 11, 30), duration=365, obj=obj, instrument_dict=instrument_dict)
    print(dates)

    for start_date in dates:
        date_back = start_date - timedelta(days=30 * 9)
        date_ahead = start_date + timedelta(days=365)

        df = get_df_from_date_back_to_date_ahead(scripts, start_date, date_back, date_ahead, obj, instrument_dict)

        df = df_sort_n_index_reset(df)

        df = df_get_rolling_avg_of_return_ahead(df)

        df.to_excel(f"research/1yr-9mnth-back/stock-returns-1yr-{start_date}.xlsx")

        print(df)


main()

# # use this when researching multiple dates
# result_df = get_analytics(folder_path="research/test/", from_to=[5, 20])
# result_df.to_excel(f"research/test/aaaa.xlsx")
# print(result_df)
