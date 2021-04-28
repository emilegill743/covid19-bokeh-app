import pandas as pd
from sqlalchemy import create_engine
import os
import time
import functools
import sys
import requests
import json
import io
from uk_covid19 import Cov19API
from pycountry_convert import (
    country_alpha2_to_continent_code,
    country_name_to_country_alpha2)


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
def jhu_cases_etl(db_engine):

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
                    'Country/Region': 'region',
                    'Province/State': 'province',
                    'Lat': 'lat',
                    'Long': 'long',
                    'Date': 'date',
                    })

        return(jhu_df)

    def load_data(jhu_df, db_engine):

        """Load JHU data into Postgres Database"""

        jhu_df.to_sql(
            name="jhu_global_cases",
            con=db_engine,
            if_exists="replace",
            index=False,
            method='multi')

    data = extract_data()
    data = transform_data(data)
    load_data(data, db_engine)


@etl_decorator
def jhu_deaths_etl(db_engine):

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
                    'Country/Region': 'region',
                    'Province/State': 'province',
                    'Lat': 'lat',
                    'Long': 'long',
                    'Date': 'date',
                    })

        return(jhu_df)

    def load_data(jhu_df, db_engine):

        """Load JHU data into Postgres Database"""

        jhu_df.to_sql(
                name="jhu_global_deaths",
                con=db_engine,
                if_exists="replace",
                index=False,
                method='multi')

    data = extract_data()
    data = transform_data(data)
    load_data(data, db_engine)


@etl_decorator
def jhu_lookup_etl(db_engine):

    """ETL job for Johns Hopkins Reference 'Lookup' Table"""

    lookup_url = 'https://raw.githubusercontent.com/CSSEGISandData/COVID-19/master/csse_covid_19_data/UID_ISO_FIPS_LookUp_Table.csv'
    lookup_df = pd.read_csv(lookup_url)

    def country_alpha2_to_continent(country_alpha2):

        """Map country name to continent"""

        try:
            continent_code = country_alpha2_to_continent_code(country_alpha2)
        except:
            continent_code = "N/A"

        return(continent_code)

    lookup_df['Continent'] = lookup_df['iso2'].apply(
                                country_alpha2_to_continent)

    lookup_df.rename(
        columns={col: col.lower() for col in lookup_df.columns},
        inplace=True)

    lookup_df.to_sql(
        name="jhu_lookup",
        con=db_engine,
        if_exists="replace",
        index=False,
        method='multi')


@etl_decorator
def jhu_us_cases_etl(db_engine):

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
                    'Country_Region': 'region',
                    'Province_State': 'province',
                    'Date': 'date',
                    })

        return(jhu_df)

    def load_data(jhu_df, db_engine):

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
    load_data(data, db_engine)


@etl_decorator
def jhu_us_deaths_etl(db_engine):

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
                    'Country_Region': 'region',
                    'Province_State': 'province',
                    'Date': 'date',
                    })

        return(jhu_df)

    def load_data(jhu_df, db_engine):

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
    load_data(data, db_engine)


@etl_decorator
def us_states_etl(db_engine):

    """ETL job for loading US states
    Longitude/Latitude data"""

    dirname = os.path.dirname(__file__)
    us_states_dataset_path = os.path.join(dirname,
                                          'geo_data',
                                          'kaggle_states.csv')

    us_states_df = pd.read_csv(us_states_dataset_path)

    us_states_df.to_sql(
                name="us_states_coords",
                con=db_engine,
                if_exists="replace",
                index=False,
                method='multi')


@etl_decorator
def local_uk_data_etl(db_engine):

    """ETL job for UK local data"""

    def extract_data():

        """Pull local UK data from gov.uk API"""

        endpoint = "https://api.coronavirus.data.gov.uk/v1/data"

        filters = [
            "areaType=ltla"
        ]

        structure = {
            "date": "date",
            "areaName": "areaName",
            "areaCode": "areaCode",
            "newCasesByPublishDate": "newCasesByPublishDate",
            "cumCasesByPublishDate": "cumCasesByPublishDate"}

        api_params = {
            "filters": str.join(";", filters),
            "structure": json.dumps(structure, separators=(",", ":"))}

        response = requests.get(endpoint, params=api_params, timeout=240)

        if response.status_code >= 400:
            raise RuntimeError(f'Request failed: { response.text }')

        json_data = response.json()
        df = pd.DataFrame(json_data["data"])

        return(df)

    def transform_data(local_uk_df):

        local_uk_df = local_uk_df.rename(columns={
                            'areaName': 'area_name',
                            'areaCode': 'area_code',
                            'newCasesByPublishDate': 'new_cases',
                            'cumCasesByPublishDate': 'cum_cases'})

        return(local_uk_df)

    def load_data(local_uk_df, db_engine):

        """Load UK local data into Postgres Database"""

        local_uk_df.to_sql(
            name="local_uk",
            con=db_engine,
            if_exists="replace",
            index=False,
            method='multi')

    data = extract_data()
    data = transform_data(data)
    load_data(data, db_engine)


@etl_decorator
def owid_global_vaccinations_etl(db_engine):

    # Extract owid vaccinations data
    owid_global_vaccinations_url = "https://raw.githubusercontent.com/owid/covid-19-data/master/public/data/vaccinations/vaccinations.csv"
    owid_global_vaccinations_df = pd.read_csv(owid_global_vaccinations_url)

    owid_global_vaccinations_df.date = pd.to_datetime(
                                            owid_global_vaccinations_df.date)

    # Load owid vaccinations data
    owid_global_vaccinations_df.to_sql(
        name="owid_global_vaccinations",
        con=db_engine,
        if_exists="replace",
        index=False,
        method='multi')


@etl_decorator
def bloomberg_global_vaccinations_etl(db_engine):

    # Extract owid vaccinations data
    bloomberg_global_vaccinations_url = "https://raw.githubusercontent.com/BloombergGraphics/covid-vaccine-tracker-data/master/data/current-global.csv"
    bloomberg_global_vaccinations_df = pd.read_csv(
                                            bloomberg_global_vaccinations_url)

    # Load owid vaccinations data
    bloomberg_global_vaccinations_df.to_sql(
        name="bloomberg_global_vaccinations",
        con=db_engine,
        if_exists="replace",
        index=False,
        method='multi')


@etl_decorator
def create_data_files(db_engine):

    dirname = os.path.dirname(__file__)

    data_views = [
        'country_trajectories',
        'geo_time_evolution',
        'global_by_day',
        'continents_by_day',
        'local_uk',
        'vaccinations_by_country_by_day',
        'vaccinations_by_continent_by_day'
        ]

    for view in data_views:

        sql_file = os.path.join(dirname, 'sql', f'{view}.sql')
        sql = open(sql_file, 'r').read()

        data = pd.read_sql(sql, db_engine)
        data.to_csv(
                os.path.join(dirname, 'data_view', f'{view}.csv'),
                index=False
                )


def etl(db_engine):

    jhu_cases_etl(db_engine)
    jhu_deaths_etl(db_engine)
    jhu_lookup_etl(db_engine)
    jhu_us_cases_etl(db_engine)
    jhu_us_deaths_etl(db_engine)
    us_states_etl(db_engine)
    local_uk_data_etl(db_engine)
    owid_global_vaccinations_etl(db_engine)
    bloomberg_global_vaccinations_etl(db_engine)
    create_data_files(db_engine)


if __name__ == '__main__':

    start = time.perf_counter()

    connection_uri = os.environ['connection_uri']
    db_engine = create_engine(connection_uri)

    etl(db_engine)

    end = time.perf_counter()

    print(f"\nLoaded data in {end-start:0.4f}s")
