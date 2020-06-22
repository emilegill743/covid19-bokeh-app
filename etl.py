import pandas as pd
from sqlalchemy import create_engine
import os
import time
import functools

def etl_decorator(func):
    """Wrap func in try-except and report time taken to execute"""
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        try:
            start = time.perf_counter()
            value = func(*args, **kwargs)
            end = time.perf_counter()
            print(f"Successfully executed {func.__name__} in {end-start:0.4f}s")
        except Exception as err:
            print(f"Failed to execute {func.__name__}")
            print(f"{err}")
        return value

    return wrapper


# John's Hopkins
@etl_decorator
def extract_jhu_data():

    """Get JHU data for global confirmed cases"""

    jhu_url = 'https://raw.githubusercontent.com/CSSEGISandData/COVID-19/master/csse_covid_19_data/csse_covid_19_time_series/time_series_covid19_confirmed_global.csv'
    jhu_df = pd.read_csv(jhu_url)

    return(jhu_df)

@etl_decorator
def transform_jhu_data(jhu_df):

    """Transform JHU data into Cases by Date by Region"""

    jhu_df['Province/State'].fillna(value='N/A', inplace=True)

    jhu_df = pd.melt(
                frame=jhu_df,
                id_vars=['Country/Region',
                         'Province/State',
                         'Lat',
                         'Long'],
                var_name='Date',
                value_name='Cases')

    jhu_df['Date'] = pd.to_datetime(jhu_df['Date'])

    jhu_df = jhu_df.groupby(['Country/Region',
                             'Province/State',
                             'Lat',
                             'Long',
                             'Date']).sum()
    jhu_df = jhu_df.reset_index()
    jhu_df = jhu_df.rename(columns={
                'Country/Region' : 'region',
                'Province/State' : 'province',
                'Lat' : 'lat',
                'Long' : 'long',
                'Date' : 'date',
                'Cases' : 'cases'
                })

    return(jhu_df)

@etl_decorator
def load_jhu_data(jhu_df):

    """Load JHU data into Postgres Database"""

    connection_uri = os.environ['connection_uri']
    db_engine = create_engine(connection_uri)

    jhu_df.to_sql(
        name="jhu_global_cases",
        con=db_engine,
        if_exists="replace",
        index=False,
        method='multi')

def etl():

    # Extract JHU data
    jhu_data = extract_jhu_data()
    # Transform JHU data
    jhu_data = transform_jhu_data(jhu_data)
    # Load JHU data
    load_jhu_data(jhu_data)

if __name__ == '__main__':
    start = time.perf_counter()
    etl()
    end = time.perf_counter()
    print(f"\nLoaded data in {end-start:0.4f}s")

    



