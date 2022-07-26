import os
import json
import gzip
import pytz
import time
import logging
import requests
import psycopg2
import schedule
import pandas as pd
from numpy import int64
from datetime import datetime,timedelta
from dotenv import load_dotenv
from sqlalchemy import create_engine

logging.basicConfig(level=logging.INFO)


load_dotenv()

def db_connect():

    user = os.getenv('POSTGRES_USER')
    password = os.getenv('POSTGRES_PASSWORD')
    host = os.getenv('POSTGRES_HOST')
    db = os.getenv('POSTGRES_DB')

    engine = create_engine(f'postgresql+psycopg2://{user}:{password}@{host}/{db}')
    engine.connect()

    return engine

tz = pytz.timezone('America/Mexico_City')

def get_current_time_format():
    now = datetime.now(tz= tz)
    dt_string = now.strftime("%Y_%m_%d-%H")
    return dt_string


def extract_data_from_api(target_folder,file_name):

    url = os.getenv('API_URL')

    logging.info(f'Extracting data from API:{url}')

    custom_headers = {
        'Accept-Encoding': 'gzip'
    }
    try:
        response = requests.get(
            url, 
            headers = custom_headers, 
            verify=False,
            stream=True
        )       
    except Exception as e:
        logging.error("Request url ERROR: " + str(e))

    if response:
        if response.status_code == 200 :
            logging.info('Succesfull response')

            file_name = get_current_time_format()

            logging.info(f'Reading file: {file_name}.gz')
            with open(f'{target_folder}/{file_name}.gz', 'wb') as fd:
                for chunk in response.iter_content(chunk_size=128):
                    fd.write(chunk)

def read_file_from_raw_layer(raw_folder,origin_file_name):
    logging.info(f'Reading gz file {origin_file_name} from raw layer')
    
    with gzip.open(f'{raw_folder}/{origin_file_name}', 'rb') as f:
        file_content = f.read() 

        file_content = file_content.decode('utf8').replace("'", '"')
        data = json.loads(file_content)

        df = pd. DataFrame(data)
    logging.info(f'-- Rows: {len(df)}')
    return df

def generate_average_table(df):
    df['date_time'] = pd.to_datetime(df['hloc'])

    now = datetime.now()

    df_filtered = df[(df['date_time'] > (now - timedelta(hours = 3))) & (df['date_time'] < (now -timedelta(hours = 1)))]
    
    df_filtered['prec'] = pd.to_numeric(df_filtered['prec'])
    df_filtered['temp'] = pd.to_numeric(df_filtered['temp'])
    df_avg_temp_rain = df_filtered.groupby(['ides','idmun','nes','nmun']).aggregate({'temp': 'mean','prec': 'mean'}).reset_index()
    df_avg_temp_rain.rename(columns = {'temp': 'avg_temp', 'prec':'avg_prec'}, inplace=True)
    return df_avg_temp_rain

def transform_data(raw_folder,stg_folder,origin_file_name):

    stg_file_name = origin_file_name.split('.')[0]
    df_forecast = read_file_from_raw_layer(raw_folder, origin_file_name)
    df_forecast.to_csv(f'{stg_folder}/{stg_file_name}.csv', index = False)
    df_avg_temp_rain = generate_average_table(df_forecast)

    return df_avg_temp_rain

def load_data(df,db_conn,table_name,method):

    now = datetime.now(tz=pytz.timezone('America/Mexico_City'))
    df['inserted_at'] = now

    logging.info(f'Saving table: {table_name}')
    df.to_sql(table_name, con = db_conn, if_exists= method, index=False)

    result = pd.read_sql(f"Select count(*) from {table_name}", db_conn)
    

def merge_data(folder_name_data, df_avg_temp_rain):
    dirs = os.listdir(folder_name_data)
    
    folders =[]
    for name in dirs:
        if os.path.isdir(os.path.join(folder_name_data, name)):
            folders.append(name)

    dates_list = [datetime.strptime(date, '%Y%m%d').date() for date in folders]
    dates_list.sort(reverse=True)

    recent_folder = datetime.strftime(dates_list[0],'%Y%m%d')

    df_data = pd.read_csv(f'{folder_name_data}/{recent_folder}/data.csv')
    
    df_data.rename(columns={'Cve_Ent': 'ides','Cve_Mun':'idmun','Value': 'value' }, inplace=True)

    df_avg_temp_rain['ides'] = df_avg_temp_rain['ides'].astype(int64)
    df_avg_temp_rain['idmun'] = df_avg_temp_rain['idmun'].astype(int64)

    df_merged_data = df_data.merge(df_avg_temp_rain, how='left',on=['ides','idmun'])
    
    return df_merged_data


def execute_etl():
    raw_folder = 'raw'
    file_name = f'{get_current_time_format()}.gz'
    stg_folder = 'stg'
    
    logging.info('Connecting to database')
    conn = db_connect()
    extract_data_from_api(raw_folder,file_name)
    df_avg_temp_rain = transform_data(raw_folder,stg_folder,file_name)

    folder_name_data='data_municipios'
    df_merged_data = merge_data(folder_name_data,df_avg_temp_rain)

    load_data(df_avg_temp_rain,conn,'weather_avg','append')
    load_data(df_merged_data,conn,'weather_data_mun','append')
    load_data(df_merged_data,conn,'weather_current','replace')


if __name__ == "__main__":
    execute_etl()
    schedule.every(1).hour.at(":30").do(execute_etl)

    while True:
         schedule.run_pending()
         time.sleep(1)
    
