from datetime import date, timedelta
from utils import get_formatted_df, calculate_moving_average, calculate_atr, create_trade_signal
from cagr.api_angel import loginAngel, instrumentDict, getDataAPI


def main() -> None:
    start_date = date(2023, 12, 15)
    date_back = start_date - timedelta(days=2000)
    print(start_date)
    print(date_back)
    scriptid = "INFY"

    instrument_dict_file = "instrument_data.json"
    obj = loginAngel()
    instrument_dict = instrumentDict(instrument_dict_file)

    data = getDataAPI(scriptid, date_back, start_date, obj, instrument_dict)

    df = get_formatted_df(data)
    df = calculate_moving_average(df, period=5)
    df = calculate_moving_average(df, period=8)
    df = calculate_atr(df, period=5)
    df = create_trade_signal(df)

    print(df)


main()
