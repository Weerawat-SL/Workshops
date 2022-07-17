#pyinstaller tenet.py --onefile
from actions import *
from flask import Flask, request, abort
import ast
from binance.client import Client
import configparser as cf
import requests
import ccxt
import datetime

setup = cf.ConfigParser()
setup.read("config.ini")

API_KEY = setup.get("Config","API_KEY")
SC_KEY = setup.get("Config","API_SECRET")
LineNotify = setup.get("Config","LineNotify")
Id = setup.get("Webhook","Id")
Link = setup.get("Webhook","Link")
Passphrase = setup.get("Webhook","Passphrase")

url = 'https://notify-api.line.me/api/notify'
token = LineNotify
headers = {
            'content-type':
            'application/x-www-form-urlencoded',
            'Authorization':'Bearer '+token
           }

client = Client(API_KEY,SC_KEY)

exchange = ccxt.binance({
    'enableRateLimit': True,  # required by the Manual https://github.com/ccxt/ccxt/wiki/Manual#rate-limit
    'apiKey': API_KEY,
    'secret': SC_KEY,
    'options': {  # exchange-specific options
        'defaultType': 'future',  # switch to a futures API/account
    },
})

def parse_webhook(webhook_data):
    data = ast.literal_eval(webhook_data)
    return data

def current_position(data):
    coin = data['symbol']
    symbol = coin[:3]+"/"+coin[3:7]
    orders = exchange.fetchMyTrades(symbol)
    x =len(exchange.fetchMyTrades(symbol))
    positionSide = orders[x-1]['info']['positionSide']
    side = orders[x-1]['info']['side']
    if positionSide == 'LONG' and side == 'BUY':
        current_side = 'buy'
        print('Current_position :',positionSide,'side :',side,'current_side :',current_side)
    elif positionSide == 'SHORT' and side == 'SELL':
        current_side = 'sell'
        print('Current_position :',positionSide,'side :',side,'current_side :',current_side)
    else :
        current_side = 'None'
        print('Current_position :',current_side)
    return current_side

def set_leverage(data):
    symbol = data['symbol']
    leverage = client.futures_change_leverage(symbol=symbol,leverage=20)
    return leverage

def close_position(data):
    if current_position(data) != 'None':   
        coin = data['symbol']
        symbol = coin[:3]+"/"+coin[3:7]
        orders = exchange.fetchMyTrades(symbol)
        x =len(exchange.fetchMyTrades(symbol))
        orderQty = data['amount']
        print("-----------------START ORDER PROCESS-----------------")
        if current_position(data) == 'buy':
            close_order=client.futures_create_order(symbol=coin,side='SELL',type="MARKET",positionSide='LONG',quantity=orderQty)
            neworders = exchange.fetchMyTrades(symbol)
            y =len(exchange.fetchMyTrades(symbol))
            print(f"{Id} :\nCreated at :{datetime.datetime.now()}\nCoin Pair :{coin}\nSignal :SELL LONG\nAmount :{orderQty}\nOrder :--Close_Position--\nRealized Profit :{round(float(neworders[y-1]['info']['realizedPnl']),5)}")
            msg = (f"{Id} :\nCreated at :{datetime.datetime.now()}\nCoin Pair :{coin}\nSignal :SELL LONG\nAmount :{orderQty}\nOrder :--Close_Position--\nRealized Profit :{round(float(neworders[y-1]['info']['realizedPnl']),5)}")
        elif current_position(data) == 'sell':
            close_order=client.futures_create_order(symbol=coin,side='BUY',type="MARKET",positionSide='SHORT',quantity=orderQty)
            neworders = exchange.fetchMyTrades(symbol)
            y =len(exchange.fetchMyTrades(symbol))
            print(f"{Id} :\nCreated at :{datetime.datetime.now()}\nCoin Pair :{coin}\nSignal :BUY SHORT\nAmount :{orderQty}\nOrder :--Close_Position--\nRealized Profit :{round(float(neworders[y-1]['info']['realizedPnl']),5)}")
            msg = (f"{Id} :\nCreated at :{datetime.datetime.now()}\nCoin Pair :{coin}\nSignal :BUY SHORT\nAmount :{orderQty}\nOrder :--Close_Position--\nRealized Profit :{round(float(neworders[y-1]['info']['realizedPnl']),5)}")
        else:
            print('ERROR')
        r = requests.post(url, headers=headers , data = {'message':msg})
        print(r.text)
        print("-----------------ENDING ORDER PROCESS-----------------")
        
    else:
        close_order = None
    if data['cmd'] == 'buy':
        positionSide = 'LONG'
        side = 'BUY'
    elif data['cmd'] == 'sell':
        positionSide = 'SHORT'
        side = 'SELL'
    else:
        pass
    if (abs(float(data['amount'])-float(orders[x-1]['amount'])))>(float(orders[x-1]['amount']*0.2)):
        size = abs(float(data['amount'])-float(orders[x-1]['amount']))
        close_order=client.futures_create_order(symbol=coin,side=side,type="MARKET",positionSide=positionSide,quantity=size,closePosition=False)
        print("-----------------START ORDER PROCESS-----------------")
        print(f"{Id} :\nCreated at :{datetime.datetime.now()}\nCoin Pair :{coin}\nSignal :{side} {positionSide}\nAmount :{size}\nOrder :--New_Position--")
        msg = (f"{Id} :\nCreated at :{datetime.datetime.now()}\nCoin Pair :{coin}\nSignal :{side} {positionSide}\nAmount :{size}\nOrder :--New_Position--")
        r = requests.post(url, headers=headers , data = {'message':msg})
        print("-----------------ENDING ORDER PROCESS-----------------")
        print(r.text)
    else:
        pass
    
    return close_order

def new_order(data):
    coin = data['symbol']
    newSize = float(data['amount'])
    orderQty = float(newSize)
    if data['cmd'] == 'buy':
        positionSide = 'LONG'
        side = 'BUY'
    elif data['cmd'] == 'sell':
        positionSide = 'SHORT'
        side = 'SELL'
    else:
        pass
    order_placememt=client.futures_create_order(symbol=coin,side=side,type="MARKET",positionSide=positionSide,quantity=orderQty,closePosition=False)
    print("-----------------START ORDER PROCESS-----------------")
    print(f"{Id} :\nCreated at :{datetime.datetime.now()}\nCoin Pair :{coin}\nSignal :{side} {positionSide}\nAmount :{orderQty}\nOrder :--New_Position--")
    msg = (f"{Id} :\nCreated at :{datetime.datetime.now()}\nCoin Pair :{coin}\nSignal :{side} {positionSide}\nAmount :{orderQty}\nOrder :--New_Position--")
    r = requests.post(url, headers=headers , data = {'message':msg})
    print(r.text)
    print("-----------------ENDING ORDER PROCESS-----------------")
    return order_placememt

app = Flask(__name__)

@app.route('/')
def root():
    return 'online'

@app.route(f'/{Link}',methods=['POST'])
def webhook():
    if request.method == 'POST':
        data = parse_webhook(request.get_data(as_text=True))
        print("////////////////////// START SIGNAL PROCESS //////////////////////")
        print(f"Order Command :\n{data}")
        if data['passphrase'] != Passphrase:
            return {
                'code': 'error',
                'message': 'nice try buddy'
            }
        if current_position(data) == 'None':
            new_order(data)
            order = "new_order"
        else:
            if data['cmd'] != current_position(data):
                close_position(data)
                order = "close_position"
            elif data['cmd'] == current_position(data):
                print('Already have position, Do Nothing')
            else:
                print('ERROR_MAIN')
        print("////////////////////// ENDING SIGNAL PROCESS //////////////////////")
        print(" ")
        print(" ")
        print(" ")
        print(" ")
        print(" ")
    return data

if __name__ == "__main__":
    app.run()