from analytics_live import get_df_from_date_back_to_date_ahead
from utils import get_market_open_dates
from scripts import scripts
from datetime import date, timedelta
from api_angel import loginAngel, instrumentDict
from utils import df_sort_n_index_reset, calculate_execution_time, df_get_rolling_avg_of_return_ahead, get_analytics


@calculate_execution_time
def main() -> None:
    folder_path = "research/1yr-9mnth-back"
    instrument_dict_file = "instrument_data.json"

    obj = loginAngel()
    instrument_dict = instrumentDict(instrument_dict_file)

    dates = get_market_open_dates(start=date(2024, 1, 2), duration=365, obj=obj, instrument_dict=instrument_dict)
    print(dates)

    for start_date in dates:
        date_back = start_date - timedelta(days=30 * 9)
        date_ahead = start_date + timedelta(days=365)

        df = get_df_from_date_back_to_date_ahead(scripts, start_date, date_back, date_ahead, obj, instrument_dict)

        df = df_sort_n_index_reset(df)

        df = df_get_rolling_avg_of_return_ahead(df)

        df.to_excel(f"{folder_path}/stock-returns-1yr-{start_date}.xlsx")

        print(df)

    # use this when researching multiple dates
    if len(dates) > 1:
        result_df = get_analytics(folder_path=folder_path, from_to=[5, 20])
        result_df.to_excel(f"{folder_path}/aaaa.xlsx")
        print(result_df)


main()
