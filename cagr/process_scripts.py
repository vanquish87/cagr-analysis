from isin import isin_yearly
import json
import datetime


def get_nse_file(file_with_loc: str) -> dict:
    with open(file_with_loc, "r") as file:
        return json.load(file)


# if date is less than oldest date then take oldest one
# if date is between dates fron isin_yearly then take lesser date than input date
# if date is greater than dates from isin_yearly then take the latest one
def get_target_isin_date(isin_yearly: dict, date: datetime.date) -> datetime.date:
    isin_yearly = list(reversed(isin_yearly.items()))

    for idx in range(len(isin_yearly)):
        key, _ = isin_yearly[idx]  # Get the current key and value

        # Check if date is less than or equal to the first key
        if date <= key and idx == 0:
            return key

        # Check the next key, if it exists
        if idx + 1 < len(isin_yearly):
            next_idx = idx + 1
            next_key, _ = isin_yearly[next_idx]

            # Compare if date is between the current key and the next key
            if date >= key and date < next_key:
                return key
        # for greater dates
        else:
            return key


def get_target_scripts(date: datetime.date) -> list:
    isin_date = get_target_isin_date(isin_yearly, date)

    isins = isin_yearly[isin_date]
    print(f"Processed date is {isin_date} has total ISINs: {len(isins)}")

    file_with_loc = "NSE.json"
    nse_file = get_nse_file(file_with_loc)

    return sorted(
        script for script in nse_file if nse_file[script].get("isin") in isins
    )
