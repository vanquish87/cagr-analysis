from datetime import date
from utils import calculate_execution_time
from df_helper import get_analytics
from models import Api, ModVar
from analyzer import AngleAnalyzer, UpstoxAnalyzer


@calculate_execution_time
def main_process(modvar: ModVar) -> None:
    if modvar.api == Api.ANGEL:
        ai = AngleAnalyzer()
    elif modvar.api == Api.UPSTOX:
        ai = UpstoxAnalyzer()

    obj, instrument_dict = ai.args_for_api()
    dates = ai.get_market_open_dates(start=modvar.start, duration=modvar.forward_days, instrument_dict=instrument_dict, obj=obj)
    print(dates)
    for start_date in dates:
        # change state of modvar for start, fromdate, todate
        modvar.start = start_date
        scripts = ai.get_target_scripts(start_date)
        df = ai.get_df_from_date_back_to_date_ahead(
            scripts,
            start_date,
            modvar.fromdate,
            modvar.todate,
            instrument_dict,
            obj,
        )
        df = ai.df_sort_n_index_reset(df)
        df = ai.df_get_rolling_avg_of_return_ahead(df)
        df.to_excel(f"{modvar.folder_path}/stock-returns-1yr-{start_date}.xlsx")

    # use this when researching multiple dates
    if len(dates) > 1:
        result_df = get_analytics(folder_path=modvar.folder_path, from_to=[5, 20])
        result_df.to_excel(f"{modvar.folder_path}/aaaa.xlsx")
        print(result_df)


def main() -> None:
    folder_path = "research/1yr-9mnth-back"

    # need to test UPSTOX more on this
    api = Api.UPSTOX  # Insert API to use here
    start = date(2025, 4, 1)
    back_days = 30 * 9
    forward_days = 365

    modvar = ModVar(api, folder_path, back_days, forward_days, start)

    main_process(modvar)


if __name__ == "__main__":
    main()
