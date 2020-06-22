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
import os
from sqlalchemy import create_engine

def build_global_tab():
    
    geo_data_shp = r'C:\Users\emile\OneDrive\Documents\GitHub\covid-19-app\geo_data\ne_50m_land\ne_50m_land.shp'
    geo_data_gdf = gpd.read_file(geo_data_shp)
    geosource = GeoJSONDataSource(geojson = geo_data_gdf.to_json())

    connection_uri = os.environ['connection_uri']
    db_engine = create_engine(connection_uri)

    geo_evol_df = pd.read_sql(
        'SELECT * FROM geo_time_evolution_view',
        db_engine)

    geo_snapshot_df = geo_evol_df[
                        geo_evol_df.date == min(geo_evol_df.date)]

    cases_cds = ColumnDataSource(geo_snapshot_df)

    p = figure(plot_height = 600 , plot_width = 950)

    geo_patches = p.patches('xs', 'ys', source=geosource)

    cases_circles = p.circle(
                        x='long',
                        y='lat',
                        size='size',
                        source=cases_cds,
                        color='red',
                        alpha=0.3)

    # Adding hover tool
    hover = HoverTool(
                tooltips=[
                    ('Country/Region', '@region'),
                    ('Province/State', '@province'),
                    ('Cases', '@cases')
                    ],
                renderers=[cases_circles])

    p.add_tools(hover)

    date_range = geo_evol_df.date.unique()
    
    date_range = [pd.Timestamp(date_val) for date_val in date_range]

    date_slider = DateSlider(
                    title="Date",
                    start=min(date_range),
                    end=max(date_range),
                    value= min(date_range))

    def date_slider_callback(attr, old, new):
        
        slider_date = date_slider.value
        
        geo_snapshot_df = geo_evol_df[
                    geo_evol_df.date == pd.Timestamp(slider_date)]

        cases_cds.data = geo_snapshot_df

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
            callback_id = curdoc().add_periodic_callback(animate_update, 100)
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