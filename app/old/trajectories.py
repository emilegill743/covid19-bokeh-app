from bokeh.io import curdoc
from bokeh.models import (ColumnDataSource, HoverTool,
                          MultiSelect, Button, DateSlider)
from bokeh.plotting import figure
from bokeh.palettes import Spectral11
from bokeh.layouts import widgetbox, row, column
import pandas as pd
import numpy as np
from pathlib import Path


def build_trajectories_tab():

    # Reading data
    root_dir = Path(__file__).parent.parent

    traj_df = pd.read_csv(
                    root_dir.joinpath(
                            'data', 'data_view',
                            'country_trajectories.csv'))

    # Creating trajectories plot
    xs = []
    ys = []
    countries = []
    colors = []

    for index, (region, region_df) in enumerate(traj_df.groupby('region')):
        xs.append(region_df['days_since_arrival'].values - 1)
        ys.append(region_df['cases'].values)
        countries.append(region)
        colors.append(Spectral11[index % 11])

    source = ColumnDataSource(data={
                    'xs': xs,
                    'ys': ys,
                    'country': countries,
                    'color': colors})

    plot = figure(title='Country Trajectories',
                  width=600,
                  height=300,
                  y_axis_type='log',
                  name="trajectories_plot",
                  sizing_mode="scale_width")

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

        """
        Callback function for MultiSelect widget:
            - Sets source data to dataset filtered for selected countries
        """
        
        selected_countries = multiselect.value

        filtered_df = traj_df.loc[traj_df.region.isin(selected_countries)]

        xs_new = []
        ys_new = []
        countries_new = []

        for region, region_df in filtered_df.groupby('region'):
            xs_new.append(region_df['days_since_arrival'].values - 1)
            ys_new.append(region_df['cases'].values)
            countries_new.append(region)
        
        countries_subset = [countries.index(country) for country
                            in selected_countries]

        colors_new = [colors[i] for i in countries_subset]

        new_data = data = {'xs': xs_new,
                           'ys': ys_new,
                           'country': countries_new,
                           'color': colors_new}
        
        source.data = new_data

    # Callback func for Clear Selection Button
    def clear_selection_button_callback(event):

        multiselect.value = []

    # Callback func for Select All Button
    def select_all_button_callback(event):

        multiselect.value = countries

    # Creating Multiselect widget with list of countries
    multiselect = MultiSelect(
                        title='Countries:',
                        options=countries,
                        value=countries,
                        size=25,
                        sizing_mode="scale_width")

    multiselect.on_change('value', country_multiselect_callback)

    # Creating Clear All, Select All Buttons
    clear_button = Button(
                        label="Clear Selection",
                        button_type="success",
                        sizing_mode="scale_width")
    clear_button.on_click(clear_selection_button_callback)

    select_all_button = Button(
                            label="Select All",
                            button_type="success",
                            sizing_mode="scale_width")
    select_all_button.on_click(select_all_button_callback)

    widgets = widgetbox(
                    clear_button, select_all_button, multiselect,
                    name="trajectories_widgetbox",
                    sizing_mode="scale_width")

    # Add the plot to the current document
    curdoc().add_root(widgets)
    curdoc().add_root(plot)
