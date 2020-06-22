from bokeh.io import curdoc
from bokeh.models import (ColumnDataSource, HoverTool, MultiSelect, Button,
                          Panel)
from bokeh.plotting import figure, show
from bokeh.palettes import Spectral11
from bokeh.layouts import widgetbox, row
import pandas as pd
import numpy as np
import itertools
from sqlalchemy import create_engine
import os

def build_countries_tab():

    connection_uri = os.environ['connection_uri']
    db_engine = create_engine(connection_uri)

    traj_df = pd.read_sql(
        'SELECT * FROM country_trajectories_view',
        db_engine)

    # Creating trajectories plot

    xs = []
    ys = []
    countries = []
    colors = []

    for index, (region, region_df) in enumerate(traj_df.groupby('region')):
        xs.append(region_df['days_since_arrival'].values - 1)
        ys.append(region_df['cases'].values)
        countries.append(region)
        colors.append(Spectral11[index%11])

    source = ColumnDataSource(data={
                    'xs' : xs,
                    'ys' : ys,
                    'country' : countries,
                    'color' : colors})

    plot = figure(title='Country Trajectories',
                  width=800,
                  height=600,
                  y_axis_type='log')

    # Adding hover tool
    hover = HoverTool(tooltips=[('Country', '@country')])
    plot.add_tools(hover)

    # Adding multi_line glyph of trajectories
    line = plot.multi_line(xs='xs',
                           ys='ys',
                           source=source,
                           line_color='color',
                           line_width=2)

    plot.xaxis.axis_label = 'Days since cases exceeded 100'
    plot.yaxis.axis_label = 'Cases'

    # Callback func for Multiselect widget
    def country_multiselect_callback(attr, old, new):
        
        selected_countries = multiselect.value

        filtered_df = traj_df.loc[traj_df.region.isin(selected_countries)]

        xs_new = []
        ys_new = []
        countries_new = []

        for region, region_df in filtered_df.groupby('region'):
            xs_new.append(region_df['days_since_arrival'].values -1)
            ys_new.append(region_df['cases'].values)
            countries_new.append(region)
        
        countries_subset = [countries.index(country) for country in selected_countries]
        colors_new = [colors[i] for i in countries_subset]

        new_data = data={
                    'xs' : xs_new,
                    'ys' : ys_new,
                    'country' : countries_new,
                    'color' : colors_new}
        
        source.data = new_data

    # Callback func for Clear Selection Button
    def clear_selection_button_callback(event):

        multiselect.value = []

    # Callback func for Select All Button
    def select_all_button_callback(event):

        multiselect.value = countries

    # Creating Multiselect widget with list of countries
    multiselect = MultiSelect(title='Countries:',
                            options=countries,
                            value=countries,
                            height=500)

    multiselect.on_change('value', country_multiselect_callback)

    # Creating Clear All, Select All Buttons
    clear_button = Button(label="Clear Selection", button_type="success")
    clear_button.on_click(clear_selection_button_callback)

    select_all_button = Button(label="Select All", button_type="success")
    select_all_button.on_click(select_all_button_callback)

    # Add the plot to the current document and add a title
    layout = row(widgetbox(clear_button, select_all_button, multiselect), plot)

    # Creating countries tab
    countries_tab = Panel(child=layout, title='Countries')

    return(countries_tab)