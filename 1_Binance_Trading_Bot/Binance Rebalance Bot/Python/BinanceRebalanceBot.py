import configparser as cf
from binance.client import Client
import datetime
from termcolor import cprint
import time
import os

os.system("")

setup = cf.ConfigParser()
setup.read("config.ini")

API_KEY = setup.get("Config","API_KEY")
SC_KEY = setup.get("Config","API_SECRET")
Live_Trade = setup.get("Config","Live_Trade")
Enable_Scheduler = setup.get("Config","Enable_Scheduler")
Asset = setup.get("Config","Asset").split(',')
Core = setup.get("Config","Core").split(',')
Base = setup.get("Config","Base")
Percentage = setup.getfloat("Config","Percentage")
Time_Loop = setup.getfloat("Config","Time_Loop")

client = Client(API_KEY,SC_KEY)

Time_Sec = Time_Loop*60

print("----------------------------------------------")
print("Binance Rebalancing Bot V.1")
print("Contact Line ID : Keramost")
print("----------------------------------------------")
print("*****[Setting Config]*****")
print(f"Live_Trade  : {Live_Trade}")
print(f"Time_Loop : {Time_Loop}")
print(f"Enable_scheduler : {Enable_Scheduler}")
print("----------------------------------------------")
print("*****[Asset Config]*****")
print(f"Asset : {Asset}")
print(f"Core : {Core}")
print(f"Base : {Base}")
print(f"Percentage : {Percentage}")
print("----------------------------------------------")
print("The program is running.")
print("----------------------------------------------")


while True:
    print("-------------------START-------------------")
    counter=0
    for coin in Asset:
        balance = client.get_asset_balance(asset=coin)
        sy = coin+Base
        price = client.get_ticker(symbol=sy)
        
        LastPrice = float(price["lastPrice"])
        Time_Open = datetime.datetime.fromtimestamp(price["openTime"] / 1000.0)
        Prefix = round(float(Core[counter]),8)
        Current = round(float(price["lastPrice"]) * float(balance["free"]),8)
        Percen = round((Current - Prefix) / Prefix * 100,2)
        Lot = client.get_symbol_info(symbol=sy)
        num=Lot["filters"][2]["minQty"]
        integer, decimal = (int(i) for i in str(num).split("."))
        decimal= 9-int(len(str(decimal)))
        size = round(abs(Current - Prefix) / LastPrice, decimal)
        check = round(size*LastPrice,8)
        if abs(Percen)>Percentage and Percen < 0:
            Act = "BUY"
            class style():
                Color = '\033[38;5;78m'
            if Live_Trade == 'on':
                order = client.create_order(symbol=sy, side='BUY', type='MARKET', quantity=size)
            else:
                pass

        elif abs(Percen)>Percentage and Percen > 0:
            Act = "SELL"
            class style():
                Color = '\033[38;5;210m'
            if Live_Trade == 'on':
                order = client.create_order(symbol=sy, side='SELL', type='MARKET', quantity=size)
            else:
                pass

        else:
            Act = "Do Nothing"
            class style():
                Color = '\033[38;5;98m'

        print(' ')
        cprint(style.Color+f'Symbol       : {sy} Price : {LastPrice}')
        cprint(style.Color+f'Created at   : {Time_Open}')
        cprint(style.Color+f'Prefix Core  : {Prefix}')
        cprint(style.Color+f'Current Core : {Current}')
        cprint(style.Color+f'Percentage   : {Percen}%')
        cprint(style.Color+f'Action       : {Act}  {check} {Base} {size}')
        counter = counter + 1
    print("---------------------END---------------------")
    if Enable_Scheduler == 'on':
        print("Ending program in 60 seconds")
        time.sleep(60)
        break
    else:
        print(f"Waiting time to start loop in {round(Time_Loop, 0)} minute")
        time.sleep(Time_Sec)