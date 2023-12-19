"""Trying to find
Multi Year breakout in ATH
Kind of Cup n Handle ripoff without Handle
"""

from datetime import date, timedelta
from utils import get_breakout_list
from models import AnalysisParameters
from cagr.api_angel import loginAngel, instrumentDict
from cagr.scripts import scripts
from cagr.utils import calculate_execution_time


@calculate_execution_time
def main() -> None:
    start_date = date(2023, 12, 19)

    parameters = AnalysisParameters(
        start_date=start_date,
        date_back=start_date - timedelta(days=2000),
        ath_before=800,
        total_high_values=5,
        start_day_range=10,
    )

    instrument_dict_file = "instrument_data.json"
    obj = loginAngel()
    instrument_dict = instrumentDict(instrument_dict_file)

    breakout_list = []
    for scriptid in scripts:
        print(f"AI analyzing {scripts.index(scriptid) + 1} of {len(scripts)}: {scriptid}")

        breakout_list = get_breakout_list(scriptid, parameters, obj, instrument_dict, breakout_list)

    print(breakout_list)


main()
