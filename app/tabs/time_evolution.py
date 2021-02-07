from bokeh.io import curdoc
from bokeh.models import (ColumnDataSource, HoverTool, Button,
                          GeoJSONDataSource, DateSlider, RadioButtonGroup,
                          Div, LabelSet, RadioGroup)
from bokeh.plotting import figure
from bokeh.layouts import widgetbox, column
import pandas as pd
import numpy as np
from pathlib import Path
import geopandas as gpd
import math
from datetime import datetime, timedelta


def build_time_evolution_tab():
   
    # Importing geographical shapefile
    root_dir = Path(__file__).parent.parent

    geo_data_gdf = gpd.read_file(
                        root_dir.joinpath(
                            'data', 'geo_data',
                            'ne_50m_land', 'ne_50m_land.shp'))

    geosource = GeoJSONDataSource(geojson=geo_data_gdf.to_json())

    # Importing geo-evolutions cases/deaths data
    time_evol_df = pd.read_csv(
                        root_dir.joinpath(
                            'data', 'data_view',
                            'geo_time_evolution.csv'))
    
    # Selecting earliest snapshot
    time_evol_df.date = pd.to_datetime(time_evol_df.date)

    snapshot_df = time_evol_df[
                        time_evol_df.date == min(time_evol_df.date)]

    global_by_day_df = pd.read_csv(
                            root_dir.joinpath(
                                'data', 'data_view',
                                'global_by_day.csv'))
 
    global_by_day_df.date = pd.to_datetime(global_by_day_df.date)
    global_totals_df = global_by_day_df.loc[
                            global_by_day_df.date == min(time_evol_df.date)]
    global_cases = int(global_totals_df.iloc[0]['cases'])
    global_deaths = int(global_totals_df.iloc[0]['deaths'])
    
    # Applying bubble-size mapping
    bubble_size = snapshot_df['cases'].apply(
                                            lambda x: 0.5*math.log(x, 1.1)
                                            if x > 0 else 0)
    snapshot_df = snapshot_df.assign(size=bubble_size.values)

    # Creating ColumnDataSource for visualisation
    cases_cds = ColumnDataSource(snapshot_df)

    # Adding figure and geographical patches from shapefile
    geo_plot = figure(plot_height=450,
                      plot_width=720,
                      x_range=(-180, 180),
                      y_range=(-90, 90),
                      name="time_evolution_geo_plot",
                      sizing_mode="scale_width")

    geo_patches = geo_plot.patches('xs', 'ys', source=geosource, alpha=0.5)

    # Adding circle glyph to create bubble plot
    cases_circles = geo_plot.circle(
                        x='long',
                        y='lat',
                        size='size',
                        source=cases_cds,
                        color='red',
                        alpha=0.2)

    # Adding hover tool
    hover = HoverTool(
                tooltips=[
                    ('Country/Region', '@region'),
                    ('Province/State', '@province'),
                    ('Cases', '@cases')
                    ],
                renderers=[cases_circles])
    geo_plot.add_tools(hover)

    # Adding hbar
    countries_df = snapshot_df.loc[:, ['date', 'region', 'cases']]

    countries_df.rename(
                    columns={"cases": "value"},
                    inplace=True)

    countries_df = countries_df.groupby(
                                    ['date', 'region']
                                    ).sum().reset_index()

    countries_df.sort_values(by='value', ascending=False, inplace=True)
    countries_df = countries_df.reset_index(drop=True)
    countries_cds = ColumnDataSource(countries_df)

    hbar_plot = figure(plot_height=450,
                       plot_width=475,
                       y_range=(10.5, -0.5),
                       x_range=(0, countries_df.value.max()*1.2),
                       name="time_evolution_hbar_plot",
                       sizing_mode="scale_width")

    hbar = hbar_plot.hbar(left=0,
                          right='value',
                          y='index',
                          source=countries_cds,
                          height=0.5,
                          line_color='white')

    labels = LabelSet(
                x='value', y='index', text='region',
                text_font_size='10pt', text_color='white',
                x_offset=5, y_offset=0, source=countries_cds,
                level='glyph', render_mode='canvas')

    hbar_plot.add_layout(labels)

    # Adding hover tool
    hover_hbar = HoverTool(
                    tooltips=[
                        ('Country/Region', '@region'),
                        ('Cases', '@value')],
                    renderers=[hbar])
    hbar_plot.add_tools(hover_hbar)

    # Adding callback for updating data
    def data_view_callback(attr, old, new):

        """Callback function to update data source:

            - Updates source data to selected data view
              (cases/deaths/new cases/new deaths)
              and selected snapshot date on date slider.

            - Updates HoverTool to reflect data view change

            - Updates Divs for total cases/deaths
        """

        # Determine data view selection
        if cases_deaths_button.active == 0:
            data_view = "cases"
        elif cases_deaths_button.active == 1:
            data_view = "deaths"
        
        if total_new_button.active == 1:
            data_view = f"new_{data_view}"

        # Determine date selection
        slider_date = date_slider.value

        # Filter data for selected date
        snapshot_df = time_evol_df[
                        time_evol_df.date == pd.Timestamp(slider_date)]

        # Map bubble size on selected data view
        bubble_size = snapshot_df[data_view].apply(
                                                lambda x: 0.5*math.log(x, 1.1)
                                                if x > 0 else 0)
        snapshot_df = snapshot_df.assign(size=bubble_size.values)

        cases_cds.data = snapshot_df

        hover.tooltips = [('Country/Region', '@region'),
                          ('Province/State', '@province'),
                          (data_view.replace('_', ' ').title(),
                          f'@{data_view}')]

        # Update hbar data
        countries_df = snapshot_df.loc[:, ['date', 'region', data_view]]
        countries_df.rename(columns={data_view: "value"},
                            inplace=True)

        countries_df = countries_df.groupby(
                                        ['date', 'region']
                                        ).sum().reset_index()

        countries_df.sort_values(by="value", ascending=False, inplace=True)
        countries_df = countries_df.reset_index(drop=True)
        countries_cds.data = countries_df

        hbar_plot.x_range.end = countries_df.value.max()*1.2

        hover_hbar.tooltips = [('Country/Region', '@region'),
                               (data_view.replace('_', ' ').title(),
                               '@value')]

        # Filter for totals
        global_totals_df = global_by_day_df.loc[
                            (global_by_day_df.date
                             == pd.Timestamp(slider_date))]
        global_cases = int(global_totals_df.iloc[0]['cases'])
        global_deaths = int(global_totals_df.iloc[0]['deaths'])

        cases_div.text = (f'<h3 class="card-text">'
                          f'{global_cases:,}</h3>')

        deaths_div.text = (f'<h3 class="card-text">'
                           f'{global_deaths:,}</h3>')

    # Adding Date slider
    date_range = [pd.Timestamp(date_val) for date_val
                  in time_evol_df.date.unique()]

    date_slider = DateSlider(
                    title="Date",
                    start=min(date_range),
                    end=max(date_range),
                    value= min(date_range),
                    sizing_mode="scale_width")
    date_slider.on_change('value', data_view_callback)

    # Adding Cases/Deaths toggle
    cases_deaths_button = RadioButtonGroup(
                            labels=["Cases", "Deaths"],
                            active=0,
                            sizing_mode="scale_width")
    cases_deaths_button.on_change('active', data_view_callback)

    # Adding Total/New toggle
    total_new_button = RadioButtonGroup(
                            labels=["Total", "New"],
                            active=0,
                            sizing_mode="scale_width")
    total_new_button.on_change('active', data_view_callback)

    # Adding callback for zooming into a selected continent
    def continent_zoom_callback(attr, old, new):

        continent_map_ref = {
                    # Worldwide
                    0: {'x_range': [-200, 200],
                        'y_range': [-100, 100]},
                    # Europe
                    1: {'x_range': [-30, 50],
                        'y_range': [30, 70]},
                    # North America
                    2: {'x_range': [-175, -15],
                        'y_range': [0, 80]},
                    # South America
                    3: {'x_range': [-140, 10],
                        'y_range': [-60, 15]},
                    # Africa
                    4: {'x_range': [-55, 105],
                        'y_range': [-40, 40]},
                    # Asia
                    5: {'x_range': [40, 140],
                        'y_range': [-5, 45]},
                    # Oceania
                    6: {'x_range': [80, 200],
                        'y_range': [-55, 5]}}
            
        map_ref = continent_map_ref[continent_button.active]
        geo_plot.x_range.start = map_ref['x_range'][0]
        geo_plot.x_range.end = map_ref['x_range'][1]
        geo_plot.y_range.start = map_ref['y_range'][0]
        geo_plot.y_range.end = map_ref['y_range'][1]

    # Adding continent toggle
    continent_button = RadioGroup(
        labels=[
            "Worldwide",
            "Europe",
            "North America",
            "South America",
            "Africa",
            "Asia",
            "Oceania"
            ], active=0)
    continent_button.on_change('active', continent_zoom_callback)

    # Adding animation with Play/Pause button
    callback_id = None

    def animate():
        def animate_update():
            date = date_slider.value + timedelta(days=1)
            if pd.Timestamp(date) >= max(date_range):
                date = min(date_range)
            date_slider.value = date

        global callback_id
        if play_button.label == '► Play':
            play_button.label = '❚❚ Pause'
            callback_id = curdoc().add_periodic_callback(animate_update, 300)
        else:
            play_button.label = '► Play'
            curdoc().remove_periodic_callback(callback_id)

    play_button = Button(label='► Play', width=60, button_type="success")
    play_button.on_click(animate)

    # Adding Cases/Deaths count
    cases_div = Div(text=f'<h3 class="card-text">'
                         f'{global_cases:,}</h3>',
                    sizing_mode="scale_width",
                    name="cases_div")

    deaths_div = Div(text=f'<h3 class="card-text">'
                          f'{global_deaths:,}</h3>',
                     sizing_mode="scale_width",
                     name="deaths_div")

    # Defining layout of tab
    widgets = widgetbox(
                    date_slider, cases_deaths_button, total_new_button,
                    play_button, continent_button,
                    name="time_evolution_widgetbox",
                    sizing_mode="scale_width")

    # Add the plot to the current document
    curdoc().add_root(geo_plot)
    curdoc().add_root(hbar_plot)
    curdoc().add_root(widgets)

    curdoc().add_root(cases_div)
    curdoc().add_root(deaths_div)
