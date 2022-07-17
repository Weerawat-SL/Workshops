from airflow import DAG
from airflow.operators.python_operator import PythonOperator
from datetime import datetime, timedelta

from airflow.hooks.mysql_hook import MySqlHook

default_args = {
    'owner': 'User',
    'depends_on_past': False,
    'start_date': datetime(2015, 12, 1),
    'email': ['airflow@example.com'],
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
    'schedule_interval': '@daily', #https://crontab.guru/
}


dag = DAG('db4free-mysql-connection', catchup=False, default_args=default_args)

def ger_db4free():
    #get database
    conn = MySqlHook("db4free-connection")
    #List all table
    tables = conn.get_records("SHOW TABLES;")
    print(tables)
    #print data in table test
    dt = conn.get_records("SELECT * FROM id_db4free")
    print(dt)

t1 = PythonOperator( task_id = 'Query_DB', python_callable = get_db4free, dag = dag)