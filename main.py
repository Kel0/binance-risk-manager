import pandas as pd
import xlwings as xl
import os
from glob import glob
from binance.futures import Futures
from pathlib import Path

ABS_PATH = Path().resolve()
file = os.path.join(ABS_PATH, "My_Futures.xlsx")

wb = xl.Book(file).sheets('Max History')

print('Обновляю тикеры биржи...')
Prices = pd.read_json('https://api.binance.com/api/v1/ticker/allPrices')

print('Подготавливаю рабочую среду...')
data_excel = pd.read_excel(file, sheet_name='Settings')  # Читаем лист в экселе
df_out_excel = pd.DataFrame(data_excel)  # Делаем промежуточную таблицу из данных в экселе

Df_in_excel = pd.DataFrame()  # Создаем пустую таблицу куда и сохраняем результаты
Prices_all = pd.DataFrame()
a = 3
b = data_excel.shape[0]

allPrices = pd.DataFrame(Prices)
allPrices = allPrices.sort_values(by='symbol')
allPrices = allPrices[['symbol']]

print('Отбираю все монеты торгуемые к USDT и BUSD')
usdt = allPrices[allPrices['symbol'].str.endswith('USDT')]
Prices_all = pd.concat([Prices_all, usdt], ignore_index=True, axis=0)

busd = allPrices[allPrices['symbol'].str.endswith('BUSD')]
Prices_all = pd.concat([Prices_all, busd], ignore_index=True, axis=0)

print('Корректирую тикеры для фьючерсного рынка')
while a < b:
    this_is = data_excel.iloc[a, 0]
    on_this = data_excel.iloc[a, 2]
    Prices_all.loc[Prices_all['symbol'] == this_is, 'symbol'] = on_this
    a = a + 1

# Функция получения ключа и секретного ключа из таблици Excel
def get_keys():
    Key = data_excel.iloc[0, 1]
    Secret = data_excel.iloc[0, 2]
    return Key, Secret

print('Получаю ключи из файла, после подключаюсь к бирже...')
Client = Futures(*get_keys())  # Получаем ключи "Динамической" функцией и передаем их на сервер
Ac = Client.account(recvWindow=10000)  # Запрос баланса с окном в 10 000 мс
Finish_index = Prices_all.shape[0]
Start_index = 0 # Создаем переменную с 1ым индексом строки промежуточной таблицы

print('Проверяю историю торговли к USDT... \n Это может занять некоторое время...')
while Start_index < Finish_index:  # Цикл получания данных по каждому торгуемому символу на Бинанс
    Finish_index_excel = Df_in_excel.shape[0]
    if Finish_index_excel <= Finish_index:
        a = Prices_all.iloc[Start_index]['symbol']
        try:
            Symbol_trades_usdt = Client.get_account_trades(symbol=a, recvWindow=10000)
        except:
            Start_index = Start_index + 1
            print('Обработал: ', a, '; Не торгуется на Фьючерсах', ' (', Start_index, ' - ', Finish_index, ')')
            continue
        Df_trades_usdt = pd.DataFrame(Symbol_trades_usdt)
        b = Df_trades_usdt.shape[0]
        if b == 0:
            Start_index = Start_index + 1
            print('Обработал: ', a, '; всего ордеров: ', b, ' (', Start_index, ' - ', Finish_index, ')')
            continue
        Df_in_excel = pd.concat([Df_in_excel, Df_trades_usdt], ignore_index=True, axis=0)  # Запись полученных данных в необходимую таблицу
        Start_index = Start_index + 1  # Задаем новое значение изначальному индексу, для выбора следующих ключей под прогон данного цикла
        print('Обработал: ', a, '; всего ордеров: ', b, ' (', Start_index, ' - ', Finish_index, ')')

    else:
        z = Prices_all.iloc[Start_index]['symbol']
        try:
            Symbol_trades_busd = Client.get_account_trades(symbol=z, recvWindow=10000)
        except:
            Start_index = Start_index + 1
            print('Обработал: ', z, '; Не торгуется на Фьючерсах', ' (', Start_index, ' - ', Finish_index, ')')
            continue
        Df_trades_busd = pd.DataFrame(Symbol_trades_busd)
        c = Df_trades_busd.shape[0]
        if b == 0:
            Start_index = Start_index + 1
            print('Обработал: ', z, '; всего ордеров: ', c, ' (', Start_index, ' - ', Finish_index, ')')
            continue
        Df_in_excel = pd.concat([Df_in_excel, Df_trades_busd], ignore_index=True,axis=0)  # Запись полученных данных в необходимую таблицу
        Start_index = Start_index + 1  # Задаем новое значение изначальному индексу, для выбора следующих ключей под прогон данного цикла
        print('Обработал: ', z, '; всего ордеров: ', c, ' (', Start_index, ' - ', Finish_index, ')')
print(Df_in_excel)
wb.range('a1').options(pd.DataFrame, index=False).value = Df_in_excel