
import analytics_live
# import sys
# sys.path.append('C:\jimmy\cagr-analysis\cagr')
from datetime import date
import pandas as pd


def test_get_excel():
    # Define test inputs and expected outputs
    start_date = date(2021, 1, 1)
    expected_output = pd.DataFrame(
        {
            "Script": ["AAPL"],
            "CMP": [132.05],
            "Date": [start_date],
            "mp_1yr_back": [122.22],
            "date_1yr_back": [date(2019, 12, 31)],
            "return_from_back": [8.1],
            "mp_1yr_ahead": [147.04],
            "date_1yr_ahead": [date(2022, 1, 2)],
            "return_ahead": [11.9],
        }
    )

    # Call the function with the test inputs
    output = analytics_live.get_excel(["AAPL"], start_date)

    # Compare the output to the expected output
    assert output.equals(expected_output)
