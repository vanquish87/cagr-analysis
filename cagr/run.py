from analytics_live import get_df_from_date_back_to_date_ahead
from utils import get_market_open_dates
from scripts import scripts
from datetime import date, timedelta
from utils import df_sort_n_index_reset, calculate_execution_time, df_get_rolling_avg_of_return_ahead, get_analytics
from api_adapter import Api, get_args_for_api


@calculate_execution_time
def main() -> None:
    folder_path = "research/1yr-9mnth-back"

    # need to test UPSTOX more on this
    api = Api.ANGEL  # Insert API to use here
    obj, instrument_dict, instruments = get_args_for_api(api)

    dates = get_market_open_dates(
        start=date(2024, 8, 22),
        duration=365,
        obj=obj,
        instrument_dict=instrument_dict,
        api=api,
        instruments=instruments,
    )
    print(dates)

    for start_date in dates:
        fromdate = start_date - timedelta(days=30 * 9)
        todate = start_date + timedelta(days=365)

        df = get_df_from_date_back_to_date_ahead(
            scripts, start_date, fromdate, todate, obj, instrument_dict, api, instruments
        )

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
