from models import Api, ModVar
from datetime import date
from main import main_process


def main() -> None:
    folder_path = "research/1yr-9mnth-back"

    # need to test UPSTOX more on this
    # Have to update instrument_data.json(ANGEL) and NSE.json(UPSTOX) time to time
    # for SCRIPTID as well as ISINs
    api = Api.ANGEL  # Insert API to use here
    start = date(2026, 1, 10)
    back_days = 30 * 9
    forward_days = 365

    modvar = ModVar(api, folder_path, back_days, forward_days, start)

    main_process(modvar)


if __name__ == "__main__":
    main()
