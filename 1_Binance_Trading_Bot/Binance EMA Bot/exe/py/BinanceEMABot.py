#Created file exe by command (pyinstaller --onefile BinanceEMABot.py)
from binance.client import Client
import configparser as cf
import ccxt
import pandas as pd
import ta
from pandas import Timestamp
import time
import datetime
from termcolor import cprint
import os

pd.options.mode.chained_assignment = None

os.system("")

#read Config file location
setup = cf.ConfigParser()
setup.read("config.ini")

#import var from config file (get,getfloat,getint)
API_KEY = setup.get("Config","API_KEY") #API Key from Binance.
SC_KEY = setup.get("Config","API_SECRET") #Secret Key from Binance.
Live = setup.get("Config","Live") #real/test order (on = real, off = test).
Time_Loop = setup.getfloat("Config","Time_Loop") #time loop for check condition.
Enable_scheduler = setup.get("Config","Enable_scheduler") # on = Submit one order and close the program.
Time_frame = setup.get("Binance_Setup","Time_frame") # Time frame for condition.
Coin = setup.get("Binance_Setup","Coin").split(',') #cyrpto coins to trade.
Quantity = setup.get("Binance_Setup","Quantity").split(',') #Quantity to trade.
Base = setup.get("Binance_Setup","Base") #available coins.
EMA_Fast = setup.getint("EMA_Setup","EMA_Fast")
EMA_Slow = setup.getint("EMA_Setup","EMA_Slow")
Bar = setup.getint("EMA_Setup","Bar") #chart bar for check condition.


client = Client(API_KEY,SC_KEY)

Time_Sec = Time_Loop * 60 #Time loop from min to sec
binance = ccxt.binance()

print("---------------------------------------------")
print("Binance EMA Bot V.1")
print("Contact Line ID : Keramost")
print("---------------------------------------------")
print("*****[Setting Config]*****")
print(f"Live_Trade  : {Live}")
print(f"Time_Loop : {Time_Loop}")
print(f"Enable_scheduler : {Enable_scheduler}")
print(f"Time_frame : {Time_frame}")
print(f"EMA_Fast : {EMA_Fast}")
print(f"EMA_Slow : {EMA_Slow}")
print("---------------------------------------------")
print("*****[Asset Config]*****")
print(f"Asset : {Coin}")
print(f"Quantity : {Quantity}")
print("---------------------------------------------")
print("The program is running.")
print("---------------------------------------------")

while True:
    print("--------------------START--------------------")
    counter=0
    for coin in Coin:
        symbol = coin+"/"+Base

        r = binance.fetch_ohlcv(symbol,Time_frame,None,Bar)

        df = pd.DataFrame(r,columns =['date', 'open', 'high', 'low', 'close', 'volume'])

        for i in range(len(df['date'])):
            df['date'][i] = df['date'].values[i]/1000
            df['date'][i] = pd.Timestamp(df['date'][i], unit='s')

        df.close = df.close.astype(float)

        df['EMAfast'] = ta.trend.ema_indicator(df.close, window  = EMA_Fast,fillna = True)
        df['EMAslow'] = ta.trend.ema_indicator(df.close, window  = EMA_Slow,fillna = True)

        balance = client.get_asset_balance(asset=coin)
        sy = coin+Base
        price = client.get_ticker(symbol=sy)
        Time_Open = datetime.datetime.fromtimestamp(price["openTime"] / 1000.0)
        LastPrice = float(price["lastPrice"])
        Quant = float(balance["free"])
        cost = LastPrice * Quant
        Lot = client.get_symbol_info(symbol=sy)
        num=Lot["filters"][2]["minQty"]
        integer, decimal = (int(i) for i in str(num).split("."))
        if decimal==0 :
            decimal="000000000"
            
        else :
            pass
        decimalsize = 9-int(len(str(decimal)))
        size = round(float(Quantity[counter]) / LastPrice, decimalsize)
        check = round(size*LastPrice,8)
        

        if df['EMAfast'][Bar-2] > df['EMAslow'][Bar-2]:
            signal = 'UP-Trend'

            if  cost >= float(Quantity[counter]):
                Act =  "Hold Position"
                class style():
                    Color = '\033[38;5;98m'
                    Trend = '\033[38;5;78m'
            else:
                Act =  "Buy"
                class style():
                    Color = '\033[38;5;78m'
                    Trend = '\033[38;5;78m'
                if Live == 'on':
                    order = client.create_order(symbol=sy, side='BUY', type='MARKET', quantity=size)
                else:
                    pass
        elif df['EMAfast'][Bar-2] < df['EMAslow'][Bar-2]:
            signal = 'DOWN-Trend'
            if cost >= float(Quantity[counter]):
                Act =  "Sell"
                class style():
                    Color = '\033[38;5;210m'
                    Trend = '\033[38;5;210m'
                if Live == 'on':
                    order = client.create_order(symbol=sy, side='SELL', type='MARKET', quantity=Quant)
                else:
                    pass
            else:
                Act =  "Waiting Signal To UP!!"
                class style():
                    Color = '\033[38;5;98m'
                    Trend = '\033[38;5;210m'
        else:
            pass
        print(' ')
        cprint(style.Color+f'Symbol       : {sy} Price : {LastPrice}')
        cprint(style.Color+f'Created at   : {Time_Open}')
        cprint(style.Color+f'Quantity     : {Quant}')
        cprint(style.Color+f'Cost         : {cost}')
        cprint(style.Color+f'Signal       : '+style.Trend+f'{signal}')
        cprint(style.Color+f'Action       : '+style.Trend+f'{Act}')
        cprint(style.Color+f'Size Check   : {check} {Base} = {size} {coin}')
        counter = counter + 1
    print("---------------------END----------------------")
    if Enable_scheduler == 'on':
        print("Ending program in 60 seconds")
        time.sleep(60)
        break
        
    else:
        print(f"Please waiting time to start loop in {round(Time_Loop, 0)} minute.")
        time.sleep(Time_Sec)