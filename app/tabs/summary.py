from bokeh.io import curdoc
from bokeh.models import (ColumnDataSource, HoverTool, MultiSelect, Button,
                          Panel, GeoJSONDataSource, DateSlider, RadioButtonGroup,
                          Range1d, BoxZoomTool, Div, FactorRange, LabelSet)
from bokeh.plotting import figure, show
from bokeh.palettes import Spectral11
from bokeh.layouts import widgetbox, row, column
import pandas as pd
import numpy as np
from pathlib import Path
import geopandas as gpd
import math
from datetime import datetime, timedelta

def build_summary_tab():

    root_dir = Path(__file__).parent.parent

    global_by_day_df = pd.read_csv(
                            root_dir.joinpath(
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

    curdoc().template_variables['summary'] = {
                "global_cases" : f"{int(global_cases):,}",
                "new_cases" : f"{int(new_cases):,}",
                "global_deaths" : f"{int(global_deaths):,}",
                "new_deaths" : f"{int(new_deaths):,}"
                }

    # Daily cases plot
    daily_cases_fig = figure(
                        plot_height = 450,
                        plot_width = 475,
                        name="time_evolution_vbar_plot",
                        sizing_mode="scale_width")
