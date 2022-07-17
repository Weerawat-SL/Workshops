#---------------------------------Libraries-----------------------------------#
#Airflow----------------------------
from airflow import DAG
# from airflow.operators.bash_operator import BashOperator
from airflow.operators.python_operator import PythonOperator
from airflow.utils.dates import days_ago
#API Binance----------------------------
from binance.client import Client 
#Read config.ini----------------------------
import configparser as cf 
#Date and Time----------------------------
from datetime import datetime,timedelta
import time
#Line Notify----------------------------
import requests
#DataFrame----------------------------
import pandas as pd
#SQL----------------------------
import pymysql.cursors
from sqlalchemy import create_engine
#Option----------------------------
from typing import Dict, Optional
import pytz
import dateparser
#On-hold------------------------
# from decimal import Decimal
# import json
# from pathlib import Path
#---------------------------------Connection and Config-----------------------------------#
pd.options.mode.chained_assignment = None  # default='warn'

#read Config file location
setup = cf.ConfigParser()
setup.read("config.ini")

#import var from config file (get,getfloat,getint)
class Config:
  MYSQL_HOST = setup.get("Database_Config","HOST")
  MYSQL_PORT = setup.getint("Database_Config","PORT")
  MYSQL_USER = setup.get("Database_Config","USER")
  MYSQL_PASSWORD = setup.get("Database_Config","PASSWORD")
  MYSQL_DBname = setup.get("Database_Config","DATABASE_NAME")
  MYSQL_CHARSET = setup.get("Database_Config","CHARSET")

api_key = setup.get("Binance_Setup","api_key")
api_secret = setup.get("Binance_Setup","api_secret")

client = Client(api_key, api_secret)

LineNotify = setup.get("Notify","LineNotify")

url = 'https://notify-api.line.me/api/notify'
token = LineNotify
headers = {
            'content-type':
            'application/x-www-form-urlencoded',
            'Authorization':'Bearer '+token
           }

#--------------------------------------PythonOperator----------------------------------------#    

def get_historical_klines(symbol, interval, start_str, end_str):

    # create the Binance client, no need for api key
    client = Client("", "")

    # init our list
    output_data = []

    # setup the max limit
    limit = 500

    # convert interval to useful value in seconds
    timeframe = interval_to_milliseconds(interval)

    # convert our date strings to milliseconds
    start_ts = date_to_milliseconds(start_str)

    # if an end time was passed convert it
    # end_ts = None
    # if end_str:
    end_ts = date_to_milliseconds(end_str)

    idx = 0
    # it can be difficult to know when a symbol was listed on Binance so allow start time to be before list date
    symbol_existed = False
    while True:
        # fetch the klines from start_ts up to max 500 entries or the end_ts if set
        temp_data = client.get_klines(
            symbol=symbol,
            interval=interval,
            limit=limit,
            startTime=start_ts,
            endTime=end_ts
        )

        # handle the case where our start date is before the symbol pair listed on Binance
        if not symbol_existed and len(temp_data):
            symbol_existed = True

        if symbol_existed:
            # append this loops data to our output data
            output_data += temp_data

            # update our start timestamp using the last value in the array and add the interval timeframe
            start_ts = temp_data[len(temp_data) - 1][0] + timeframe
        else:
            # it wasn't listed yet, increment our start date
            start_ts += timeframe

        idx += 1
        # check if we received less than the required limit and exit the loop
        if len(temp_data) < limit:
            # exit the while loop
            break

        # sleep after every 3rd call to be kind to the API
        if idx % 3 == 0:
            time.sleep(1)

    return output_data

def date_to_milliseconds(date_str: str) -> int:
    
    # get epoch value in UTC
    epoch: datetime = datetime.utcfromtimestamp(0).replace(tzinfo=pytz.utc)
    # parse our date string
    d: Optional[datetime] = dateparser.parse(date_str, settings={'TIMEZONE': "UTC"})
    if not d:
        raise UnknownDateFormat(date_str)

    # if the date is not timezone aware apply UTC timezone
    if d.tzinfo is None or d.tzinfo.utcoffset(d) is None:
        d = d.replace(tzinfo=pytz.utc)

    # return the difference in time
    return int((d - epoch).total_seconds() * 1000.0)

def interval_to_milliseconds(interval: str) -> Optional[int]:

    seconds_per_unit: Dict[str, int] = {
        "m": 60,
        "h": 60 * 60,
        "d": 24 * 60 * 60,
        "w": 7 * 24 * 60 * 60,
    }
    try:
        return int(interval[:-1]) * seconds_per_unit[interval[-1]] * 1000
    except (ValueError, KeyError):
        return None

def to_table(df,table,type):
    conn_string = f'mysql+pymysql://{Config.MYSQL_USER}:{Config.MYSQL_PASSWORD}@{Config.MYSQL_HOST}/{Config.MYSQL_DBname}'
  
    db = create_engine(conn_string)
    conn = db.connect()

    df.to_sql(table, con=conn, if_exists=type,index=False) #{'fail', 'replace', 'append'}
    print(f'{type} "{table}" : Done ')

    conn.close()
    db.dispose()

def line(process,df,action):
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    msg = (f"\nCreated at :{now}\
            \n{process} : Done\
            \nCount_Rows {action} : {len(df)}")
    requests.post(url, headers=headers , data = {'message':msg})

def Set_table():
    connection = pymysql.connect(   
        host=Config.MYSQL_HOST,
        port=Config.MYSQL_PORT,
        user=Config.MYSQL_USER,
        password=Config.MYSQL_PASSWORD,
        db=Config.MYSQL_DBname,
        charset=Config.MYSQL_CHARSET,
        cursorclass=pymysql.cursors.DictCursor)

    cursor = connection.cursor()
    sql = "CREATE TABLE IF NOT EXISTS T_AC_BINANCE_EXCHAN_INFO (    \
                `symbol` VARCHAR(200)                       \
                ,`status` VARCHAR(200)                      \
                ,`baseAsset` VARCHAR(200)                   \
                ,`baseAssetPrecision` INT                   \
                ,`quoteAsset` VARCHAR(200)                  \
                ,`quotePrecision` INT                       \
                ,`quoteAssetPrecision` INT                  \
                ,`orderTypes` VARCHAR(200)                  \
                ,`icebergAllowed` VARCHAR(20)               \
                ,`ocoAllowed` VARCHAR(20)                   \
                ,`quoteOrderQtyMarketAllowed` VARCHAR(20)   \
                ,`allowTrailingStop` VARCHAR(20)            \
                ,`cancelReplaceAllowed` VARCHAR(20)         \
                ,`isSpotTradingAllowed` VARCHAR(20)         \
                ,`isMarginTradingAllowed` VARCHAR(20)       \
                ,`filters` VARCHAR(200)                     \
                ,`permissions` VARCHAR(200));" 
    cursor.execute(sql)

    sql = "CREATE TABLE IF NOT EXISTS T_AC_BINANCE_DAILY_CANDLE (   \
                `Symbol` VARCHAR(200)                       \
                ,`Open_time` TIMESTAMP(6)                   \
                ,`Close_time` TIMESTAMP(6)                  \
                ,`Open` FLOAT(20,8)                         \
                ,`High` FLOAT(20,8)                         \
                ,`Low` FLOAT(20,8)                          \
                ,`Close` FLOAT(20,8)                        \
                ,`Volume` FLOAT(20,8)                       \
                ,`Quote_asset_volume` FLOAT(20,8)           \
                ,`Number_of_trades` INT(50)                 \
                ,`Taker_buy_base_asset_volume` FLOAT(20,8)  \
                ,`Taker_buy_quote_asset_volume` FLOAT(20,8) \
                ,`Ignore` FLOAT(20,8));" 
    cursor.execute(sql)
    cursor.close()

def Exchange_Info_Daily_Load():
    exchange_info = client.get_exchange_info()
    ex_info = pd.DataFrame(exchange_info['symbols'],columns =['symbol', 'status', 'baseAsset', 'baseAssetPrecision', 'quoteAsset', 'quotePrecision', 'quoteAssetPrecision', 'orderTypes', 'icebergAllowed', 'ocoAllowed', 'quoteOrderQtyMarketAllowed','allowTrailingStop','cancelReplaceAllowed','isSpotTradingAllowed','isMarginTradingAllowed','filters','permissions'])

    #Convert dict to str
    for j in range(len(ex_info['orderTypes'])):
            ex_info['orderTypes'][j] =  ','.join(str(v) for v in ex_info['orderTypes'][j])
            ex_info['filters'][j] =  ','.join(str(v) for v in ex_info['filters'][j])
            ex_info['permissions'][j] =  ','.join(str(v) for v in ex_info['permissions'][j])
            # ex_info['filters'][j] =  str(ex_info['filters'][j])

    to_table(ex_info,'T_AC_BINANCE_EXCHAN_INFO','replace')#{'fail', 'replace', 'append'}
    
    line('Exchange_Info_Daily_Load',ex_info,'Replace')

def Daily_Candle_Load():
    connection = pymysql.connect(host=Config.MYSQL_HOST,
                             port=Config.MYSQL_PORT,
                             user=Config.MYSQL_USER,
                             password=Config.MYSQL_PASSWORD,
                             db=Config.MYSQL_DBname,
                             charset=Config.MYSQL_CHARSET,
                             cursorclass=pymysql.cursors.DictCursor)

    cursor = connection.cursor()

    sql = "SELECT * FROM `T_AC_BINANCE_EXCHAN_INFO` WHERE `status` = 'TRADING'"
    cursor.execute(sql)
    allrow=cursor.fetchall()
    X=pd.DataFrame(allrow)

    test_interval = ('1d')
    start_str = datetime.now().strftime("%d/%m/%Y") #'07/01/2022'
    end_str = datetime.now().strftime("%d/%m/%Y") #'07/01/2022'

    df = pd.DataFrame(columns =['Open_time', 'Open', 'High', 'Low', 'Close', 'Volume', 'Close_time', 'Quote_asset_volume', 'Number_of_trades', 'Taker_buy_base_asset_volume', 'Taker_buy_quote_asset_volume','Ignore','Symbol'])

    n=0

    for s in X['symbol']:
        # if n>5:
        #     break
        Candlestick_Data = get_historical_klines(s, test_interval, start_str, end_str)
        
        df2 = pd.DataFrame(Candlestick_Data,columns =['Open_time', 'Open', 'High', 'Low', 'Close', 'Volume', 'Close_time', 'Quote_asset_volume', 'Number_of_trades', 'Taker_buy_base_asset_volume', 'Taker_buy_quote_asset_volume','Ignore'])
        
        for p in df2 ['Open_time']:
            df2['Symbol'] = s
            
        df = pd.concat([df, df2],ignore_index = True)
        
        # T = len(X['symbol'])
        # percentLoad = round(n/T*100,2)
        # print('\r','Loading :',n,'/',T,'    >>     ',percentLoad,'%   ')
        n=n+1

    for i in range(len(df['Open_time'])):
            df['Open_time'][i] = df['Open_time'].values[i]/1000
            df['Open_time'][i] = pd.Timestamp(df['Open_time'][i], unit='s')
            df['Close_time'][i] = df['Close_time'].values[i]/1000
            df['Close_time'][i] = pd.Timestamp(df['Close_time'][i], unit='s')

    cursor.close()
    to_table(df,'T_AC_BINANCE_DAILY_CANDLE','append')#{'fail', 'replace', 'append'}
    line('Daily_Candle_Load',df,'Append')
#--------------------------------------Default Args----------------------------------------#
default_args = {
    'owner': 'Weerawat',
    'depends_on_past': False,
    'start_date': days_ago(2), #datetime(2015,12,1) 
    'email': ['airflow@example.com'],
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 1, #try send e-mail
    'retry_delay': timedelta(minutes=5),
    'schedule_interval': "1 0 * * *" #'@daily', #https://crontab.guru/
}
#---------------------------------------Create DAG-----------------------------------------#
dag = DAG(
    'Binance_Market',#catchup=False #(False:now>>future/True:Start>>End date)
    default_args=default_args,
    description='Pipeline for Binance_Market data',
    schedule_interval=timedelta(days=1),
)


# Set_table
t1 = PythonOperator(
    task_id='Set_table',
    python_callable=Set_table,
    dag=dag,
)

# Exchange_Info_Daily_Load
t2 = PythonOperator(
    task_id='Exchange_Info_Daily_Load',
    python_callable=Exchange_Info_Daily_Load,
    # op_args=['Hello World!'], #Passing in arguments (list)
    # op_kwargs=('random_base':float(i)/10), #Passing in arguments (dict)( parameter : value )
    dag=dag,
)

# Daily_Candle_Load
t3 = PythonOperator(
    task_id='Daily_Candle_Load',
    python_callable=Daily_Candle_Load,
    dag=dag,
)

#---------------------------------------DAG Flow-----------------------------------------#

t1>>t2>>t3
