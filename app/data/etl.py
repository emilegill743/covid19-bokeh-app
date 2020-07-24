import pandas as pd
from sqlalchemy import create_engine
import os
import time
import functools
import sys

def etl_decorator(func):
    """Wrap func in try-except and report time taken to execute"""
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        try:
            start = time.perf_counter()
            value = func(*args, **kwargs)
            end = time.perf_counter()
            print(f"Successfully executed {func.__name__} in {end-start:0.4f}s")
            return value
        except Exception as err:
            print(f"Failed to execute {func.__name__}")
            print(sys.exc_info())
    return wrapper

@etl_decorator
def jhu_cases_etl():

    """ETL job for Johns Hopkins Global Cases Data"""

    def extract_data():

        """Get JHU data for global confirmed cases"""

        jhu_url = 'https://raw.githubusercontent.com/CSSEGISandData/COVID-19/master/csse_covid_19_data/csse_covid_19_time_series/time_series_covid19_confirmed_global.csv'
        jhu_df = pd.read_csv(jhu_url)

        return(jhu_df)

    def transform_data(jhu_df):

        """Transform JHU data into Cases by Date by Region"""

        jhu_df['Province/State'].fillna(value='N/A', inplace=True)

        jhu_df = pd.melt(
                    frame=jhu_df,
                    id_vars=['Country/Region',
                            'Province/State',
                            'Lat',
                            'Long'],
                    var_name='Date',
                    value_name='cases')

        jhu_df['Date'] = pd.to_datetime(jhu_df['Date'])

        jhu_df.sort_values(
            by=['Country/Region', 'Province/State', 'Date'],
            inplace=True)

        jhu_df = jhu_df.rename(columns={
                    'Country/Region' : 'region',
                    'Province/State' : 'province',
                    'Lat' : 'lat',
                    'Long' : 'long',
                    'Date' : 'date',
                    })

        return(jhu_df)

    def load_data(jhu_df):

            """Load JHU data into Postgres Database"""

            connection_uri = os.environ['connection_uri']
            db_engine = create_engine(connection_uri)

            jhu_df.to_sql(
                name="jhu_global_cases",
                con=db_engine,
                if_exists="replace",
                index=False,
                method='multi')
    
    data = extract_data()
    data = transform_data(data)
    load_data(data)

@etl_decorator
def jhu_deaths_etl():

    """ETL job for Johns Hopkins Global Deaths Data"""

    def extract_data():

        """Get JHU data for global deaths"""

        jhu_url = 'https://raw.githubusercontent.com/CSSEGISandData/COVID-19/master/csse_covid_19_data/csse_covid_19_time_series/time_series_covid19_deaths_global.csv'
        jhu_df = pd.read_csv(jhu_url)

        return(jhu_df)

    def transform_data(jhu_df):

        """Transform JHU data into Deaths by Date by Region"""

        jhu_df['Province/State'].fillna(value='N/A', inplace=True)

        jhu_df = pd.melt(
                    frame=jhu_df,
                    id_vars=['Country/Region',
                            'Province/State',
                            'Lat',
                            'Long'],
                    var_name='Date',
                    value_name='deaths')

        jhu_df['Date'] = pd.to_datetime(jhu_df['Date'])

        jhu_df.sort_values(
            by=['Country/Region', 'Province/State', 'Date'],
            inplace=True)

        jhu_df = jhu_df.rename(columns={
                    'Country/Region' : 'region',
                    'Province/State' : 'province',
                    'Lat' : 'lat',
                    'Long' : 'long',
                    'Date' : 'date',
                    })

        return(jhu_df)

    def load_data(jhu_df):

            """Load JHU data into Postgres Database"""

            connection_uri = os.environ['connection_uri']
            db_engine = create_engine(connection_uri)

            jhu_df.to_sql(
                name="jhu_global_deaths",
                con=db_engine,
                if_exists="replace",
                index=False,
                method='multi')
    
    data = extract_data()
    data = transform_data(data)
    load_data(data)

@etl_decorator
def jhu_lookup_etl():

    """ETL job for Johns Hopkins Reference 'Lookup' Table"""

    lookup_url = 'https://raw.githubusercontent.com/CSSEGISandData/COVID-19/master/csse_covid_19_data/UID_ISO_FIPS_LookUp_Table.csv'
    lookup_df = pd.read_csv(lookup_url)

    connection_uri = os.environ['connection_uri']
    db_engine = create_engine(connection_uri)

    lookup_df.to_sql(
        name="jhu_lookup",
        con=db_engine,
        if_exists="replace",
        index=False,
        method='multi')

@etl_decorator
def jhu_us_cases_etl():

    """ETL job for Johns Hopkins US Deaths Data"""

    def extract_data():

        """Get JHU data for US deaths"""

        jhu_url = 'https://raw.githubusercontent.com/CSSEGISandData/COVID-19/master/csse_covid_19_data/csse_covid_19_time_series/time_series_covid19_confirmed_US.csv'
        jhu_df = pd.read_csv(jhu_url)

        return(jhu_df)

    def transform_data(jhu_df):

        """Transform JHU data into Cases by Date by Region"""

        jhu_df = jhu_df.drop(
                            columns=[
                                'UID', 'iso2', 'iso3',
                                'code3', 'FIPS', 'Admin2',
                                'Combined_Key', 'Lat', 'Long_']) 
        jhu_df = pd.melt(
                        frame=jhu_df,
                        id_vars=['Country_Region',
                                'Province_State'],
                        var_name='Date',
                        value_name='cases')

        jhu_df = jhu_df.groupby(
                            ['Country_Region',
                             'Province_State',
                             'Date']).sum().reset_index()

        jhu_df['Date'] = pd.to_datetime(jhu_df['Date'])

        jhu_df = jhu_df.rename(columns={
                    'Country_Region' : 'region',
                    'Province_State' : 'province',
                    'Date' : 'date',
                    })

        return(jhu_df)

    def load_data(jhu_df):

            """Load JHU data into Postgres Database"""

            connection_uri = os.environ['connection_uri']
            db_engine = create_engine(connection_uri)

            jhu_df.to_sql(
                name="jhu_us_cases",
                con=db_engine,
                if_exists="replace",
                index=False,
                method='multi')
    
    data = extract_data()
    data = transform_data(data)
    load_data(data)

@etl_decorator
def jhu_us_deaths_etl():

    """ETL job for Johns Hopkins US Deaths Data"""

    def extract_data():

        """Get JHU data for US deaths"""

        jhu_url = 'https://raw.githubusercontent.com/CSSEGISandData/COVID-19/master/csse_covid_19_data/csse_covid_19_time_series/time_series_covid19_deaths_US.csv'
        jhu_df = pd.read_csv(jhu_url)

        return(jhu_df)

    def transform_data(jhu_df):

        """Transform JHU data into Deaths by Date by Region"""

        jhu_df = jhu_df.drop(
                            columns=[
                                'UID', 'iso2', 'iso3',
                                'code3', 'FIPS', 'Admin2',
                                'Combined_Key', 'Population',
                                'Lat', 'Long_']) 
        jhu_df = pd.melt(
                        frame=jhu_df,
                        id_vars=['Country_Region',
                                'Province_State'],
                        var_name='Date',
                        value_name='deaths')

        jhu_df = jhu_df.groupby(
                            ['Country_Region',
                             'Province_State',
                             'Date']).sum().reset_index()

        jhu_df['Date'] = pd.to_datetime(jhu_df['Date'])

        jhu_df = jhu_df.rename(columns={
                    'Country_Region' : 'region',
                    'Province_State' : 'province',
                    'Date' : 'date',
                    })

        return(jhu_df)

    def load_data(jhu_df):

            """Load JHU data into Postgres Database"""

            connection_uri = os.environ['connection_uri']
            db_engine = create_engine(connection_uri)

            jhu_df.to_sql(
                name="jhu_us_deaths",
                con=db_engine,
                if_exists="replace",
                index=False,
                method='multi')
    
    data = extract_data()
    data = transform_data(data)
    load_data(data)

@etl_decorator
def create_data_files():

    connection_uri = os.environ['connection_uri']
    db_engine = create_engine(connection_uri)

    dirname = os.path.dirname(__file__)

    data_views = [
        'country_trajectories',
        'geo_time_evolution',
        'global_by_day'
        ]

    for view in data_views:

        sql_file = os.path.join(dirname, 'sql', f'{view}.sql')
        sql = open(sql_file, 'r').read()

        data = pd.read_sql(sql, db_engine)
        data.to_csv(
                os.path.join(dirname, 'data_view', f'{view}.csv'),
                index=False
                )
    
def etl():
    jhu_cases_etl()
    jhu_deaths_etl()
    jhu_lookup_etl()
    jhu_us_cases_etl()
    jhu_us_deaths_etl()
    create_data_files()

if __name__ == '__main__':
    start = time.perf_counter()
    etl()
    end = time.perf_counter()
    print(f"\nLoaded data in {end-start:0.4f}s")

