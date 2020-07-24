from bokeh.io import curdoc
from bokeh.models import (ColumnDataSource, HoverTool, MultiSelect, Button,
                          Panel, GeoJSONDataSource, DateSlider, RadioButtonGroup,
                          Range1d, BoxZoomTool, Div, FactorRange, LabelSet)
from bokeh.plotting import figure, show
from bokeh.palettes import Spectral11
from bokeh.layouts import widgetbox, row, column
import pandas as pd
import numpy as np
import os
import geopandas as gpd
import math
from datetime import datetime, timedelta

def countries_tab():

    traj_df = pd.read_csv(
                    os.path.join(
                        os.path.dirname(__file__),
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
    layout = row(
                widgetbox(clear_button, select_all_button, multiselect),
                plot)

    # Creating countries tab
    countries_tab = Panel(child=layout, title='Countries', name='countries_tab')

    return(countries_tab)

def global_tab():
    
    # Importing geographical shapefile
    geo_data_gdf = gpd.read_file(
                        os.path.join(
                        os.path.dirname(__file__),
                        'data', 'geo_data',
                        'ne_50m_land', 'ne_50m_land.shp'))
    geosource = GeoJSONDataSource(geojson = geo_data_gdf.to_json())

    # Importing geo-evolutions cases/deaths data
    geo_evol_df = pd.read_csv(
                    os.path.join(
                    os.path.dirname(__file__),
                    'data', 'data_view',
                    'geo_time_evolution.csv'))
    
    # Selecting earliest snapshot
    geo_evol_df.date = pd.to_datetime(geo_evol_df.date)

    geo_snapshot_df = geo_evol_df[
                        geo_evol_df.date == min(geo_evol_df.date)]
    
    # Applying bubble-size mapping
    bubble_size = geo_snapshot_df['cases'].apply(
                                                lambda x: 0.5*math.log(x,1.1)
                                                if x>0 else 0)
    geo_snapshot_df = geo_snapshot_df.assign(size=bubble_size.values)

    # Creating ColumnDataSource for visualisation
    cases_cds = ColumnDataSource(geo_snapshot_df)

    # Adding figure and geographical patches from shapefile
    p = figure(
            plot_height = 450,
            plot_width = 720,
            x_range=(-180,180),
            y_range=(-90,90))

    geo_patches = p.patches('xs', 'ys', source=geosource)

    # Adding circle glyph to create bubble plot
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

    # Adding vbar
    countries_df = geo_snapshot_df.loc[:, ['date', 'region', 'cases', 'deaths', 'new_cases', 'new_deaths']]
    countries_df = countries_df.groupby(['date', 'region']).sum().reset_index()
    countries_df.sort_values(by='cases', ascending=False, inplace=True)
    countries_df = countries_df.reset_index(drop=True)
    countries_cds = ColumnDataSource(countries_df)

    p2 = figure(
            plot_height = 450,
            plot_width = 475,
            y_range=(10.5,-0.5),
            x_range=(-10,countries_df.cases.max()*1.2)
            )

    vbar = p2.hbar(
                left=0,
                right='cases',
                y='index',
                source=countries_cds,
                height=0.5,
                line_color='white')

    labels = LabelSet(
                x='cases', y='index', text='region',
                text_font_size='10pt', text_color='white',
                x_offset=5, y_offset=0, source=countries_cds,
                level='glyph', render_mode='canvas')

    p2.add_layout(labels)

    # Adding hover tool
    hover_vbar = HoverTool(
                tooltips=[
                    ('Country/Region', '@region'),
                    ('Cases', '@cases')
                    ],
                renderers=[vbar])
    p2.add_tools(hover_vbar)

    # Adding callback for updating data
    def data_view_callback(attr, old, new):

        if (cases_deaths_button.active == 0
            and total_new_button.active == 0):
            data_view = 'cases'

        elif (cases_deaths_button.active == 1
              and total_new_button.active == 0):
            data_view = 'deaths'

        elif (cases_deaths_button.active == 0
              and total_new_button.active == 1):
            data_view = 'new_cases'

        elif (cases_deaths_button.active == 1
              and total_new_button.active == 1):
            data_view = 'new_deaths'
               
        slider_date = date_slider.value

        geo_snapshot_df = geo_evol_df[
                    geo_evol_df.date == pd.Timestamp(slider_date)]
        
        bubble_size = geo_snapshot_df[data_view].apply(
                                                lambda x: 0.5*math.log(x,1.1)
                                                if x>0 else 0)
        geo_snapshot_df = geo_snapshot_df.assign(size=bubble_size.values)

        cases_cds.data = geo_snapshot_df

        countries_df = geo_snapshot_df.loc[:, ['date', 'region', 'cases', 'deaths', 'new_cases', 'new_deaths']]
        countries_df = countries_df.groupby(['date', 'region']).sum().reset_index()
        countries_df.sort_values(by='cases', ascending=False, inplace=True)
        countries_df = countries_df.reset_index(drop=True)
        countries_cds.data = countries_df

        p2.x_range.end = countries_df.cases.max()*1.2
        
        hover.tooltips = [('Country/Region', '@region'),
                          ('Province/State', '@province'),
                          (data_view.replace('_',' ').title(),
                           f'@{data_view}')]

        cases_div.text = f"""
                            <div class="alert alert-dark" role="alert" style="width:300px">
                                <h5>
                                    Global cases: {geo_snapshot_df.cases.sum():,}
                                </h5>
                            </div>"""

        deaths_div.text = f"""
                            <div class="alert alert-dark" role="alert" style="width:300px">
                                <h5>
                                    Global deaths: {geo_snapshot_df.deaths.sum():,}
                                </h5>
                            </div>"""

    # Adding Date slider
    date_range = [pd.Timestamp(date_val) for date_val in geo_evol_df.date.unique()]
    date_slider = DateSlider(
                    title="Date",
                    start=min(date_range),
                    end=max(date_range),
                    value= min(date_range))
    date_slider.on_change('value', data_view_callback)

    # Adding Cases/Deaths toggle
    cases_deaths_button = RadioButtonGroup(
        labels=["Cases", "Deaths"], active=0)
    cases_deaths_button.on_change('active', data_view_callback)

    # Adding Total/New toggle
    total_new_button = RadioButtonGroup(
        labels=["Total", "New"], active=0)
    total_new_button.on_change('active', data_view_callback)

    # Adding callback for zooming into a selected continent
    def continent_zoom_callback(attr, old, new):

        if continent_button.active == 0:
            p.x_range.start = -200
            p.x_range.end = 200
            p.y_range.start = -100
            p.y_range.end = 100
        elif continent_button.active == 1:
            p.x_range.start = -30
            p.x_range.end = 50
            p.y_range.start = 30
            p.y_range.end = 70
        elif continent_button.active == 2:
            p.x_range.start = -175
            p.x_range.end = -15
            p.y_range.start = 0
            p.y_range.end = 80
        elif continent_button.active == 3:
            p.x_range.start = -140
            p.x_range.end = 10
            p.y_range.start = -60
            p.y_range.end = 15
        elif continent_button.active == 4:
            p.x_range.start = -55
            p.x_range.end = 105
            p.y_range.start = -40
            p.y_range.end = 40
        elif continent_button.active == 5:
            p.x_range.start = 40
            p.x_range.end = 140
            p.y_range.start = -5
            p.y_range.end = 45
        elif continent_button.active == 6:
            p.x_range.start = 80
            p.x_range.end = 200
            p.y_range.start = -55
            p.y_range.end = 5

    # Adding continent toggle
    continent_button = RadioButtonGroup(
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
            callback_id = curdoc().add_periodic_callback(animate_update, 500)
        else:
            play_button.label = '► Play'
            curdoc().remove_periodic_callback(callback_id)

    play_button = Button(label='► Play', width=60)
    play_button.on_click(animate)

    # Adding Cases/Deaths count
    cases_div = Div(text=f"""
                            <div class="alert alert-dark" role="alert" style="width:300px">
                                <h5>
                                    Global cases: {geo_snapshot_df.cases.sum():,}
                                </h5>
                            </div>""")

    deaths_div = Div(text=f"""
                            <div class="alert alert-dark" role="alert" style="width:300px">
                                <h5>
                                    Global deaths: {geo_snapshot_df.deaths.sum():,}
                                </h5>
                            </div>""")

    # Defining layout of tab
    layout = row(
                widgetbox(
                    date_slider, play_button,
                    cases_deaths_button, total_new_button,
                    cases_div, deaths_div),
                column(continent_button,row(p,p2)))

    # Creating lockdown tab
    global_tab = Panel(child=layout, title='Global', name='global_tab')

    return(global_tab)

def main_tab():

    global_by_day_df = pd.read_csv(
                        os.path.join(
                        os.path.dirname(__file__),
                        'data', 'data_view',
                        'global_by_day.csv'))
 
    global_by_day_df.date = pd.to_datetime(global_by_day_df.date)

    latest_date = global_by_day_df.date.max()

    latest_values = global_by_day_df.loc[
                        global_by_day_df.date == latest_date]

    global_cases = latest_values.cases.values[0]
    global_deaths = latest_values.deaths.values[0]
    new_cases = latest_values.new_cases.values[0]
    new_deaths = latest_values.new_deaths.values[0]


    layout = Div(
                text=f"""
                        <div>
                            <h2>
                                Global cases: {int(global_cases):,} (+{int(new_cases):,})
                            </h2>
                        </div>
                        <div>
                            <h2>
                                Global deaths: {int(global_deaths):,} (+{int(new_deaths):,})
                            </h2>
                        </div>
                        """)

    # Creating lockdown tab
    main_tab = Panel(child=layout, title='Main', name='main_tab')

    return(main_tab)
