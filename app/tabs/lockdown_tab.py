from bokeh.io import curdoc
from bokeh.models import (Div, ColumnDataSource, DatetimeTickFormatter,
                          DaysTicker, HoverTool, Span, Label, Title,
                          MultiSelect, Button, RadioButtonGroup,
                          FactorRange)
from bokeh.models.widgets import Tabs, Panel
from bokeh.layouts import row, column, widgetbox
from bokeh.plotting import figure
from bokeh.palettes import viridis
import pandas as pd
import numpy as np
import math
from datetime import datetime, timedelta
import pycountry_convert as pc

def get_lockdown_data():

    # Read lockdown data from auravision.ai

    lockdown_url = 'https://covid19-lockdown-tracker.netlify.com/lockdown_dates.csv'
    lockdown_data = pd.read_csv(lockdown_url, parse_dates=True)

    return(lockdown_data)

def prep_lockdown_data(lockdown_data):

    '''Preparing data for lockdown tab'''

    # Selecting only National level data
    lockdown_data = lockdown_data.loc[
                        lockdown_data.Place.isnull()]

    lockdown_data = lockdown_data.loc[                    
                        lockdown_data.Level == 'National',
                        ['Country', 'Start date', 'End date']]

    lockdown_data = lockdown_data.rename(
                        columns={'Start date': 'start_date',
                                 'End date' : 'end_date'})

    # Set datetime columns, sort by start date
    lockdown_data['start_date'] = pd.to_datetime(
                                    lockdown_data['start_date'],
                                    format='%Y-%m-%d',
                                    errors='coerce')
                                    
    lockdown_data['end_date'] = pd.to_datetime(
                                    lockdown_data['end_date'],
                                    format='%Y-%m-%d',
                                    errors='coerce')

    lockdown_data = lockdown_data.sort_values(
                                    'start_date', ascending=False
                                    ).reset_index(drop=True)

    # Assign colors and calculate length of lockdown
    lockdown_data['color'] = pd.Series(
                                viridis(len(lockdown_data))
                                )

    lockdown_data = lockdown_data.assign(length=lambda x: (x.end_date - x.start_date).dt.days)

    # Mapping country to continent
    
    def country_to_continent(country_name):
        try:
            country_code = pc.country_name_to_country_alpha2(
                                    country_name, cn_name_format="default")
            
            continent_code = pc.country_alpha2_to_continent_code(country_code)
            
            continents_dict = {
                'EU': 'Europe',
                'NA': 'North America',
                'SA': 'South America', 
                'AS': 'Asia',
                'OC': 'Oceania',
                'AF': 'Africa'}
            
            continent = continents_dict[continent_code]
        except:
            continent = 'N/A'
        
        return(continent)
        

    lockdown_data['continent'] = lockdown_data.Country.apply(country_to_continent)

    return(lockdown_data)

def build_lockdown_tab():

    # Get data for lockdown tab
    lockdown_data = get_lockdown_data()
    lockdown_data = prep_lockdown_data(lockdown_data)

    source_gantt = ColumnDataSource(lockdown_data.dropna())
    source_points = ColumnDataSource(lockdown_data)

    # Create lockdown figure
    lockdown_fig = figure(
                    y_range=FactorRange(factors=lockdown_data.Country.unique().tolist()),
                    x_axis_type='datetime',
                    title="Lockdown Status by Nation",
                    x_range=(
                        lockdown_data['start_date'].min() - timedelta(days=3),
                        lockdown_data['end_date'].max() + timedelta(days=3)),
                    outline_line_color=None,
                    width=1000, height=650)

    # Adding hbar glyph of lockdown dates
    gantt_plot = lockdown_fig.hbar(
                                y="Country",
                                left='start_date',
                                right='end_date',
                                height=0.4,
                                source=source_gantt,
                                color='color')
    
    # Adding start point circle glyph
    start_point = lockdown_fig.circle(
                                    x='start_date',
                                    y='Country',
                                    source=source_points,
                                    size=5,
                                    line_color='blue',
                                    fill_color='white')

    # Adding end point circle glyph
    end_point = lockdown_fig.circle(
                                x='end_date',
                                y='Country',
                                source=source_points,
                                size=5,
                                line_color='blue',
                                fill_color='white')

    # Formatting x-axis
    lockdown_fig.xaxis.axis_label = "Date"
    lockdown_fig.xaxis.formatter = DatetimeTickFormatter(days='%d/%m/%Y')
    lockdown_fig.xaxis.ticker = DaysTicker(days=np.arange(5, 365, 7))
    lockdown_fig.xaxis.major_label_orientation = math.pi/6

    # Formatting y-axis
    lockdown_fig.yaxis.axis_label = "Country"
    lockdown_fig.yaxis.major_label_orientation = math.pi/12
    lockdown_fig.yaxis.major_label_text_font_size = "7pt"
    lockdown_fig.yaxis.major_label_text_font_style = "bold"
    lockdown_fig.ygrid.grid_line_color = None
    lockdown_fig.y_range.range_padding = 0.05

    # Align grid and axis tickers
    lockdown_fig.xgrid[0].ticker = lockdown_fig.xaxis[0].ticker

    # Adding hover tools
    gantt_hover = HoverTool(
                    renderers=[gantt_plot],
                    tooltips=[('Country', '@Country'),
                            ('Start Date', '@start_date{%d/%m/%Y}'),
                            ('End Date', '@end_date{%d/%m/%Y}'),
                            ('Length', '@length{%d days}')],
                    formatters={'@start_date' : 'datetime',
                                '@end_date' : 'datetime',
                                '@length' : 'printf'})
    
    start_hover = HoverTool(
                    renderers=[start_point],
                    tooltips=[('Country', '@Country'),
                            ('Start Date', '@start_date{%d/%m/%Y}')],
                    formatters={'@start_date' : 'datetime'})
    
    end_hover = HoverTool(
                    renderers=[end_point],
                    tooltips=[('Country', '@Country'),
                            ('End Date', '@end_date{%d/%m/%Y}')],
                    formatters={'@end_date' : 'datetime'})


    lockdown_fig.add_tools(gantt_hover, start_hover, end_hover)

    # Adding vertical span for today's date
    today_date_span = Span(
                        location=datetime.today(),
                        dimension='height',
                        line_color='blue',
                        line_width=3,
                        line_dash=[6,6])

    lockdown_fig.add_layout(today_date_span)

    # Labelling span
    span_label = Label(
                    x=datetime.today() + timedelta(hours=12),
                    y=-1.2,
                    y_units='screen',
                    text='Current Date',
                    text_font_size='12pt')

    lockdown_fig.add_layout(span_label)

    # Adding CheckboxButtonGroup for continents
    continents = lockdown_data['continent'].unique().tolist()

    continent_rbg = RadioButtonGroup(labels=continents,
                                     active=None,
                                     width=500)

    def continent_rbg_callback(attr, old, new):
        if continent_rbg.active != None:
            selected_continent = continent_rbg.labels[continent_rbg.active]

            filtered_df = lockdown_data.loc[
                            lockdown_data.continent == selected_continent]

            gantt_cds = ColumnDataSource(filtered_df.dropna())

            points_cds = ColumnDataSource(filtered_df)

            source_gantt.data.update(gantt_cds.data)
            source_points.data.update(points_cds.data)
            
            lockdown_fig.y_range.factors = filtered_df.Country.unique().tolist()

            # Synchronise country filter
            country_multiselect.options = filtered_df['Country'].unique().tolist()
            country_multiselect.value = filtered_df['Country'].unique().tolist()

    continent_rbg.on_change('active', continent_rbg_callback)

    # Adding MultiSelect Widget for filtering by country
    countries = lockdown_data['Country'].unique().tolist()

    country_multiselect = MultiSelect(
                            title='Countries:',
                            options=countries,
                            value=countries,
                            height=500)

    def country_multiselect_callback(attr, old, new):
        
        selected_countries = country_multiselect.value

        filter_condition = lockdown_data.Country.isin(selected_countries)
        filtered_df = lockdown_data.loc[filter_condition]

        gantt_cds = ColumnDataSource(filtered_df.dropna())

        points_cds = ColumnDataSource(filtered_df)

        source_gantt.data.update(gantt_cds.data)
        source_points.data.update(points_cds.data)

        lockdown_fig.y_range.factors = filtered_df.Country.unique().tolist()

        # Synchronise continent filter
        continent_rbg.active = None

    country_multiselect.on_change('value', country_multiselect_callback)

    # Creating Clear All, Select All Buttons

    def clear_button_callback(event):

        country_multiselect.options = countries
        country_multiselect.value = []
        continent_rbg.active = None

        lockdown_fig.y_range.factors = lockdown_data.Country.unique().tolist()
        

    def select_all_button_callback(event):

        country_multiselect.options = countries
        country_multiselect.value = countries
        continent_rbg.active = None

        lockdown_fig.y_range.factors = lockdown_data.Country.unique().tolist()

    clear_button = Button(label="Clear Selection", button_type="success")
    clear_button.on_click(clear_button_callback)

    select_all_button = Button(label="Select All", button_type="success")
    select_all_button.on_click(select_all_button_callback)

    # Add the plot to the current document and add a title

    layout = row(widgetbox(clear_button, select_all_button,
                           continent_rbg, country_multiselect),
                 lockdown_fig)
    layout.sizing_mode = 'scale_width'

    # Creating lockdown tab
    lockdown_tab = Panel(child=layout, title='Lockdown')

    return(lockdown_tab)