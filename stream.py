import os
import json
from time import sleep
from pathlib import Path
import certifi
import datetime

import click
from binance.um_futures import UMFutures
from binance.websocket.um_futures.websocket_client import UMFuturesWebsocketClient

from cfg import KEY, SECRET

os.environ["SSL_CERT_FILE"] = certifi.where()
ABS_PATH = Path().resolve()
cm_futures_client = UMFutures(key=KEY, secret=SECRET)


def _kline(r):
    """
    Подписка на свечи
    :param r:
    :return:
    """
    if "k" in r:
        print(r.get("k").get("c"), r.get("k").get("V"))
    else:
        print("Подписка kline")


def _user_data(r):
    """
    Подписка на user_data
    :param r:
    :return:
    """
    if r.get("T"):
        readableDate = datetime.datetime.utcfromtimestamp(int(r["T"]) / 1000).strftime('%Y-%m-%d')
        filename = os.path.join(ABS_PATH, "actions", f"{str(readableDate)}.json")
        data = {}
        if r.get('o'):
            try:
                with open(filename, "r") as f:
                    data = json.load(f)
                    if data.get(r['o']['s']) is None:
                        data[r['o']['s']] = []

                    if float(r['o']["rp"]):
                        data[r['o']['s']].append(float(r['o']["rp"]))

            except Exception as e:
                if data.get(r['o']['s']) is None:
                    data[r['o']['s']] = []
                if float(r['o']["rp"]):
                    data[r['o']['s']].append(float(r['o']["rp"]))

            with open(filename, "w+") as f:
                f.truncate()
                json.dump(data, f, indent=4)


if __name__ == "__main__":
    # ******************* Основной код
    click.secho("Поднимаю Stream", fg="magenta")
    client = UMFuturesWebsocketClient()
    client.start()

    try:

        listen_key = cm_futures_client.new_listen_key().get("listenKey")
        print(listen_key)
        client.user_data(listen_key=listen_key, id=1, callback=_user_data)

        for i in range(1, 60 * 60 * 24):
            if i % 59 * 60 == 0:
                cm_futures_client.renew_listen_key(listen_key)
            if i % 60 == 0:
                click.secho(f"Сокет ок, {int(i / 60)} мин.", fg="yellow")
            sleep(1)

    except KeyboardInterrupt:
        ...
    finally:
        client.stop()
