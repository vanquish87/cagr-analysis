import requests
import pandas as pd
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed

# -------------------------------
# User Parameters
# -------------------------------
START_DATE = datetime(2023, 5, 1)
MAX_THREADS = 20
TOP_N = 200
OUTPUT_FILE = "top200_equity_returns.xlsx"

# -------------------------------
# STEP 1: Fetch all mutual funds
# -------------------------------
fund_list_url = "https://api.mfapi.in/mf"
funds = requests.get(fund_list_url).json()

equity_funds = []

print(f"Total schemes found: {len(funds)}\n")
print("STEP 1 → Filtering Equity Funds\n")

for idx, f in enumerate(funds, start=1):
    scheme_name = f["schemeName"]

    # Print progress counter
    print(f"[{idx} / {len(funds)}]")

    if "growth" in scheme_name.lower():
        print(f"✓ Selected Equity Fund → {scheme_name}")
        equity_funds.append(f)

print(f"\nTotal Equity Funds Selected: {len(equity_funds)}\n")

# -------------------------------
# STEP 2: Process equity funds
# -------------------------------

results = []


def process_equity_fund(f):
    scheme_code = f["schemeCode"]
    scheme_name = f["schemeName"]

    nav_url = f"https://api.mfapi.in/mf/{scheme_code}"
    try:
        data = requests.get(nav_url, timeout=10).json()
    except Exception as e:
        print(f"Error fetching NAV for {scheme_name}: {e}")
        return None

    if "data" not in data:
        return None

    df = pd.DataFrame(data["data"])
    df["nav"] = pd.to_numeric(df["nav"], errors="coerce")
    df["date"] = pd.to_datetime(df["date"], format="%d-%m-%Y")
    df = df.dropna(subset=["nav"])

    # Filter NAVs within ±3 days of START_DATE
    window_start = START_DATE - timedelta(days=3)
    window_end = START_DATE + timedelta(days=3)
    df_window = df[(df["date"] >= window_start) & (df["date"] <= window_end)].copy()

    if df_window.empty:
        return None

    # Pick NAV closest to START_DATE
    df_window["diff"] = (df_window["date"] - START_DATE).abs()
    start_row = df_window.loc[df_window["diff"].idxmin()]
    start_nav = start_row["nav"]
    actual_start_date = start_row["date"].date()  # for reference

    # Most recent NAV
    end_nav = df.iloc[df["date"].argmax()]["nav"]

    ret = ((end_nav - start_nav) / start_nav) * 100

    return {
        "scheme_code": scheme_code,
        "scheme_name": scheme_name,
        "start_nav": start_nav,
        "actual_start_date": actual_start_date,
        "end_nav": end_nav,
        "return_%": ret,
    }


print("STEP 2 → Fetching NAV + Calculating Returns (20 threads)...\n")

with ThreadPoolExecutor(max_workers=MAX_THREADS) as executor:
    futures = {executor.submit(process_equity_fund, f): f for f in equity_funds}

    for idx, future in enumerate(as_completed(futures), start=1):
        fund = futures[future]
        try:
            result = future.result()
            print(f"[{idx} / {len(equity_funds)}] Completed → {fund['schemeName']}")
            if result:
                results.append(result)
        except Exception as e:
            print(f"Error processing {fund['schemeName']}: {e}")

# -------------------------------
# STEP 3: Convert results to DataFrame and save
# -------------------------------
df_results = pd.DataFrame(results)

if df_results.empty:
    print("No funds found with NAV in the ±3 day window around START_DATE.")
else:
    df_results = df_results.sort_values(by="return_%", ascending=False)
    top200 = df_results.head(TOP_N)
    top200.to_excel(OUTPUT_FILE, index=False)
    print(f"\nDONE → {OUTPUT_FILE} saved successfully.")
