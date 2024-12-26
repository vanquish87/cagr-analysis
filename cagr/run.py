from analytics_live import get_df_from_date_back_to_date_ahead
from utils import get_market_open_dates
from process_scripts import get_target_scripts
from datetime import date
from utils import df_sort_n_index_reset, calculate_execution_time, df_get_rolling_avg_of_return_ahead, get_analytics
from api_adapter import get_args_for_api
from models import Api, ModVar


@calculate_execution_time
def main_process(modvar: ModVar) -> None:
    obj, instrument_dict = get_args_for_api(modvar.api)

    dates = get_market_open_dates(
        start=modvar.start, duration=modvar.forward_days, obj=obj, instrument_dict=instrument_dict, api=modvar.api
    )
    print(dates)

    for start_date in dates:
        # change state of modvar for start, fromdate, todate
        modvar.start = start_date
        scripts = get_target_scripts(start_date)

        df = get_df_from_date_back_to_date_ahead(
            scripts, start_date, modvar.fromdate, modvar.todate, obj, instrument_dict, modvar.api
        )

        df = df_sort_n_index_reset(df)

        df = df_get_rolling_avg_of_return_ahead(df)

        df.to_excel(f"{modvar.folder_path}/stock-returns-1yr-{start_date}.xlsx")

        print(df)

    # use this when researching multiple dates
    if len(dates) > 1:
        result_df = get_analytics(folder_path=modvar.folder_path, from_to=[5, 20])
        result_df.to_excel(f"{modvar.folder_path}/aaaa.xlsx")
        print(result_df)


def main() -> None:
    folder_path = "research/1yr-9mnth-back"

    # need to test UPSTOX more on this
    api = Api.ANGEL  # Insert API to use here
    start = date(2025, 1, 2)
    back_days = 30 * 9
    forward_days = 365

    modvar = ModVar(api, folder_path, back_days, forward_days, start)

    main_process(modvar)


if __name__ == "__main__":
    main()
