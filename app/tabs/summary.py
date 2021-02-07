from bokeh.io import curdoc
from bokeh.models import ColumnDataSource, HoverTool
from bokeh.models.widgets import Tabs, Panel
from bokeh.plotting import figure
from bokeh.layouts import widgetbox
import pandas as pd
import numpy as np
from pathlib import Path
import geopandas as gpd
from datetime import datetime, timedelta


def build_summary_tab():

    root_dir = Path(__file__).parent.parent

    # Import global by day dataset
    global_by_day_df = pd.read_csv(
                            root_dir.joinpath(
                                'data', 'data_view',
                                'global_by_day.csv'))
 
    global_by_day_df.date = pd.to_datetime(global_by_day_df.date)

    global_by_day_cds = ColumnDataSource(global_by_day_df)

    latest_date = global_by_day_df.date.max()

    latest_values = global_by_day_df.loc[
                        global_by_day_df.date == latest_date]

    global_cases = latest_values.cases.values[0]
    global_deaths = latest_values.deaths.values[0]
    new_cases = latest_values.new_cases.values[0]
    new_deaths = latest_values.new_deaths.values[0]

    curdoc().template_variables['summary'] = {
                "global_cases": f"{int(global_cases):,}",
                "new_cases": f"{int(new_cases):,}",
                "global_deaths": f"{int(global_deaths):,}",
                "new_deaths": f"{int(new_deaths):,}"}

    # Daily cases/deaths plots
    panel_dict = {}
    data_views = ["cases", "new_cases", "deaths", "new_deaths"]

    for data_view in data_views:
        
        # Creating figure
        fig = figure(
                name=f"{data_view}_vbar",
                sizing_mode="scale_width",
                x_axis_type="datetime",
                plot_height=200)
        
        # Adding vbar for data view
        vbar = fig.vbar(
                    x="date",
                    top=data_view,
                    width=timedelta(days=0.5),
                    source=global_by_day_cds)

        # Adding hover tool
        hover = HoverTool(
                    tooltips=[
                        ("Date", "@date{%F}"),
                        (f"{data_view.replace('_', ' ').title()}",
                         f"@{data_view}{{(0.0 a)}}")],
                    formatters={"@date": "datetime"})

        fig.add_tools(hover)

        # Creating panel for plot, filling panel dict
        panel = Panel(child=fig, title=data_view)
        panel_dict[data_view] = panel

    # Creating tab layouts and adding to root
    cases_tabs = Tabs(
                    tabs=[panel_dict["cases"],
                          panel_dict["new_cases"]],
                    name=f"daily_cases_tabs")
    curdoc().add_root(cases_tabs)

    deaths_tabs = Tabs(
                    tabs=[panel_dict["deaths"],
                          panel_dict["new_deaths"]],
                    name=f"daily_deaths_tabs")
    curdoc().add_root(deaths_tabs)
