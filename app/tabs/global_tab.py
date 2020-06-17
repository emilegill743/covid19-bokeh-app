from bokeh.plotting import figure
from bokeh.tile_providers import get_provider
from bokeh.models import (Panel, GeoJSONDataSource, ColumnDataSource,
                          DateSlider, Button, HoverTool)
from bokeh.layouts import row, widgetbox
import geopandas as gpd
import pandas as pd
import numpy as np
import math
from datetime import datetime, timedelta
from bokeh.io import curdoc

def get_data():

    confirmed_global_url = 'https://raw.githubusercontent.com/CSSEGISandData/COVID-19/master/csse_covid_19_data/csse_covid_19_time_series/time_series_covid19_confirmed_global.csv'
    confirmed_global_df = pd.read_csv(confirmed_global_url)

    return(confirmed_global_df)

def transform_data(data, date='latest'):

    cases_df = data.copy()

    cases_df = cases_df.loc[
                    ~(cases_df[['Lat', 'Long']] == 0).all(axis=1)
                    ]

    cases_df = pd.melt(frame=cases_df,
                       id_vars=['Country/Region',
                                'Province/State',
                                'Lat',
                                'Long'],
                       var_name='Date',
                       value_name='Cases')
    
    cases_df['Date'] = pd.to_datetime(cases_df['Date'])

    if date == 'latest':
        cases_df = cases_df[
                        cases_df.Date == max(cases_df.Date)
                        ]
    else:
        cases_df = cases_df[
                        cases_df.Date == date
                        ]

    cases_df['Size'] = cases_df.Cases.apply(
                            lambda x : math.log(x, 1.2) if x > 0 else 0)
    
    cases_df['Province/State'].fillna(value='N/A', inplace=True)
    
    return(cases_df)



def build_global_tab():
    
    geo_data_shp = r'C:\Users\emile\OneDrive\Documents\GitHub\covid-19-app\geo_data\ne_50m_land\ne_50m_land.shp'
    
    geo_data_gdf = gpd.read_file(geo_data_shp)

    geosource = GeoJSONDataSource(geojson = geo_data_gdf.to_json())

    cases_data = get_data()
    cases_data = transform_data(cases_data)

    cases_cds = ColumnDataSource(cases_data)

    p = figure(plot_height = 600 , plot_width = 950)

    geo_patches = p.patches('xs', 'ys', source=geosource)

    cases_circles = p.circle(
                        x='Long',
                        y='Lat',
                        size='Size',
                        source=cases_cds,
                        color='red',
                        alpha=0.3)

    # Adding hover tool
    hover = HoverTool(
                tooltips=[
                    ('Country/Region', '@{Country/Region}'),
                    ('Province/State', '@{Province/State}'),
                    ('Cases', '@Cases')
                    ],
                renderers=[cases_circles]
                )
    p.add_tools(hover)

    date_range = pd.melt(
                        frame=get_data(),
                        id_vars=[
                            'Country/Region',
                            'Province/State',
                            'Lat',
                            'Long'],
                        var_name='Date',
                        value_name='Cases').Date.unique()
    
    date_range = [datetime.strptime(date_val, '%m/%d/%y') for date_val in date_range]

    date_slider = DateSlider(
        title="Date",
        start=min(date_range),
        end=max(date_range),
        value= max(date_range)
    )

    def date_slider_callback(attr, old, new):
        
        slider_date = date_slider.value

        data = get_data()
        data = transform_data(
                    data,
                    date=pd.Timestamp(slider_date)
                    )

        cases_cds.data = data

    date_slider.on_change('value', date_slider_callback)

    def animate_update():
        date = date_slider.value + timedelta(days=1)
        if pd.Timestamp(date) >= max(date_range):
            date = min(date_range)
        date_slider.value = date

    callback_id = None

    def animate():
        global callback_id
        if button.label == '► Play':
            button.label = '❚❚ Pause'
            callback_id = curdoc().add_periodic_callback(animate_update, 200)
        else:
            button.label = '► Play'
            curdoc().remove_periodic_callback(callback_id)

    button = Button(label='► Play', width=60)
    button.on_click(animate)

    layout = row(
                widgetbox(date_slider, button),
                p)

    # Creating lockdown tab
    global_tab = Panel(child=layout, title='Global')

    return(global_tab)