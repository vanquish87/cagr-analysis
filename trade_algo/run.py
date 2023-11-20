from datetime import date, timedelta
from utils import (
    get_EOD_date,
    get_formatted_df,
    calculate_moving_average,
    calculate_atr,
    create_trade_signal
)


def main() -> None:
    start_date = date(2023, 9, 15)
    date_back = start_date - timedelta(days=50)
    scriptid = "INFY"

    data = get_EOD_date(start_date, date_back, scriptid)
    df = get_formatted_df(data)
    df = calculate_moving_average(df, period=5)
    df = calculate_moving_average(df, period=8)
    df = calculate_atr(df, period=5)
    df = create_trade_signal(df)


    print(df)


main()
