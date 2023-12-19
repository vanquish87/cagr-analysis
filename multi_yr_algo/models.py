from dataclasses import dataclass
from datetime import date


@dataclass
class AnalysisParameters:
    start_date: date
    date_back: date
    ath_before: int  # last ATH is taken before start_date - threshold Days
    total_high_values: int  # number of unique top n high values
    start_day_range: int  # number of days range before start_date to find last_date_in_top
