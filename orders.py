import json
from datetime import datetime
from pathlib import Path
import os
from stream import cm_futures_client

ABS_PATH = Path().resolve()


def get_all_tickers(client):
    # Get all available exchange tickers
    exchangeInfo = client.exchange_info()

    # Extract the tickers general info
    exchangeSymbols = []

    for i in exchangeInfo['symbols']:
        exchangeSymbols.append(i["symbol"])

    return exchangeSymbols


def check_orders(client):
    with open(os.path.join(ABS_PATH, "prosadka.txt"), "r") as f:
        limit = int(f.read()) * -1

    with open(os.path.join(ABS_PATH, "actions", f"{datetime.today().date()}.json"), 'r') as f:
        data = json.load(f)
        sums = 0
        for key, val in data.items():
            sums += sum(val)

    if sums < limit:
        print("BLOCKING TRADING")
        cancel_orders(client)


def cancel_orders(client):
    tickers = get_all_tickers(client)
    for ticker in tickers:
        client.countdown_cancel_order(symbol=ticker, countdownTime=6 * 60 * 60 * 1000)


if __name__ == "__main__":
    check_orders(cm_futures_client)
