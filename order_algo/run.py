"""
This server functions as a sample automation tool designed for placing orders at scale.
It patiently waits for these orders to be filled.
If orders do not get filled within a specified time frame, the server cancels them
and strategically places new orders in proximity to the current market price (CMP).

The algorithm for this functionality is still under consideration and refinement.
It's essential to thoroughly test this boilerplate code in a live market environment
using a small quantity before deploying it for larger-scale operations.
"""

import kiteconnect
import time
import datetime

NSE_PREFIX = "NSE:"


def get_kite_api(api_key, api_secret, redirect_url):
    kite = kiteconnect.KiteConnect(api_key=api_key)
    print("Generate the following URL and visit it in your browser:")
    print(kite.login_url())
    request_token = input("Enter the request token obtained from the URL: ")
    data = kite.generate_session(request_token, api_secret=api_secret)
    kite.set_access_token(data["access_token"])
    print("Access Token:", data["access_token"])
    return kite


def get_median_volume(kite, symbol, interval="day", duration=30):
    instrument_token = kite.ltp(symbol)[f"{NSE_PREFIX}{symbol}"]["instrument_token"]
    historical_data = kite.historical_data(
        instrument_token=instrument_token,
        interval=interval,
        from_date=(datetime.datetime.now() - datetime.timedelta(days=duration)).strftime("%Y-%m-%d"),
        to_date=datetime.datetime.now().strftime("%Y-%m-%d"),
    )
    volumes = [candle["volume"] for candle in historical_data]
    median_volume = sorted(volumes)[len(volumes) // 2]
    return median_volume


def calculate_bid_quantity(median_volume, market_seconds=6 * 60 * 60):
    intervals_per_market = market_seconds / 20
    bid_quantity = median_volume / market_seconds * intervals_per_market
    return int(bid_quantity)


def get_filled_order_amounts(kite, order, filled_order_amounts):
    order_id = order["order_id"]
    try:
        order_details = kite.order_history(order_id)
        filled_quantity = sum([trade["quantity"] for trade in order_details["trades"]])
        filled_amount = sum([trade["trade_value"] for trade in order_details["trades"]])

        kite.cancel_order(variety=kite.VARIETY_REGULAR, order_id=order_id)
        print(f"Canceled order: {order_id}, Filled Quantity: {filled_quantity}, Filled Amount: {filled_amount}")
        filled_order_amounts.append(filled_amount)
    except Exception as e:
        print(f"Error processing order {order_id}: {e}")

    return filled_order_amounts


def check_orders(kite, symbol, timeout=180):
    start_time = time.time()
    filled_order_amounts = []

    while time.time() - start_time < timeout:
        open_orders = kite.orders()

        if not open_orders:
            print("All orders filled.")
            return filled_order_amounts

        time.sleep(10)

    print("Timeout reached. Canceling open orders.")
    for order in open_orders:
        filled_order_amounts = get_filled_order_amounts(kite, order, filled_order_amounts)

    return sum(filled_order_amounts)


def place_orders(kite, symbol, amount_to_invest, bid_quantity, step_size):
    ticker = kite.ltp(symbol)
    current_price = ticker[f"{NSE_PREFIX}{symbol}"]["last_price"]
    for factor in range(1, int(1 / step_size) + 1):
        price = current_price - factor * step_size * current_price
        quantity = bid_quantity / price
        order_params = {
            "tradingsymbol": symbol,
            "exchange": kite.EXCHANGE_NSE,
            "transaction_type": kite.TRANSACTION_TYPE_BUY,
            "quantity": int(quantity),
            "order_type": kite.ORDER_TYPE_LIMIT,
            "price": round(price, 2),
            "product": kite.PRODUCT_MIS,
        }
        order_id = kite.place_order(variety=kite.VARIETY_REGULAR, **order_params)
        print(f"Placed order: {order_id}")

    return current_price


def main():
    api_key = "YOUR_API_KEY"
    api_secret = "YOUR_API_SECRET"
    redirect_url = "http://your_redirect_url"
    symbol = "RELIANCE"
    amount_to_invest = 100
    step_size = 0.02

    kite = get_kite_api(api_key, api_secret, redirect_url)

    filled_amounts = check_orders(kite, symbol)
    amount_to_invest -= filled_amounts

    while amount_to_invest > 0:
        median_volume = get_median_volume(kite, symbol)
        bid_quantity = calculate_bid_quantity(median_volume)
        start_price = place_orders(kite, symbol, amount_to_invest, bid_quantity, step_size)
        filled_amounts = check_orders(kite, symbol)
        amount_to_invest -= sum(filled_amounts)


if __name__ == "__main__":
    main()
