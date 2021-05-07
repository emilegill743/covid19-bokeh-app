from bokeh.io import curdoc
from bokeh.models import ColumnDataSource, HoverTool, HBar
from bokeh.models.widgets import Tabs, Panel
from bokeh.plotting import figure
from bokeh.layouts import widgetbox
from bokeh.palettes import Spectral11
import pandas as pd
import numpy as np
from pathlib import Path
import geopandas as gpd
from datetime import datetime, timedelta


def build_summary_tab():

    s3_root = 'https://covid19-bokeh-app.s3.eu-west-2.amazonaws.com'

    # Import global by day dataset
    global_by_day_df = pd.read_csv(f'{s3_root}/data/global_by_day.csv')

    global_by_day_df.date = pd.to_datetime(global_by_day_df.date)

    latest_cases_date = global_by_day_df.loc[
                            ~global_by_day_df.cases.isna()
                            ].date.max()

    latest_cases_values = global_by_day_df.loc[
                        global_by_day_df.date == latest_cases_date]

    latest_vaccinations_date = global_by_day_df.loc[
                                    ~global_by_day_df.total_vaccinations.isna()
                                    ].date.max()

    latest_vaccinations_values = global_by_day_df.loc[
                        global_by_day_df.date == latest_vaccinations_date]

    global_cases = latest_cases_values.cases.values[0]
    global_deaths = latest_cases_values.deaths.values[0]
    new_cases = latest_cases_values.new_cases.values[0]
    new_deaths = latest_cases_values.new_deaths.values[0]

    global_vaccinations = (latest_vaccinations_values
                           .total_vaccinations.values[0])
    new_vaccinations = (latest_vaccinations_values
                        .daily_vaccinations.values[0])
    global_percentage_vaccinated = (latest_vaccinations_values
                                    .people_vaccinated_per_hundred.values[0])
    global_percentage_fully_vaccinated = (latest_vaccinations_values
                                          .people_fully_vaccinated_per_hundred
                                          .values[0])

    curdoc().template_variables['summary'] = {
                "global_cases": f"{int(global_cases):,}",
                "new_cases": f"{int(new_cases):,}",
                "global_deaths": f"{int(global_deaths):,}",
                "new_deaths": f"{int(new_deaths):,}",
                "latest_cases_date": latest_cases_date.strftime("%d/%m/%Y"),
                "global_vaccinations": f"{int(global_vaccinations):,}",
                "new_vaccinations": f"{int(new_vaccinations):,}",
                "latest_vaccinations_date": latest_vaccinations_date.strftime("%d/%m/%Y")}

    # Import continents by day dataset
    continents_by_day_df = pd.read_csv(f'{s3_root}/data/continents_by_day.csv')

    continents_by_day_df.date = pd.to_datetime(continents_by_day_df.date,
                                               format='%Y-%m-%d')

    # Adding vaccinations tabs
    vaccinations_by_continent_df = pd.read_csv(
                                        f'{s3_root}/data/vaccinations_by_continent_by_day.csv')

    vaccinations_by_continent_df.date = pd.to_datetime(
                                            vaccinations_by_continent_df.date,
                                            format='%Y-%m-%d')

    merged_continents_df = continents_by_day_df.merge(
                                vaccinations_by_continent_df,
                                how='outer', on=['date', 'continent'],
                                validate='one_to_one')

    # Daily cases/deaths plots
    panel_dict = {}
    data_views = ["cases", "new_cases", "deaths", "new_deaths",
                  "total_vaccinations", "daily_vaccinations"]

    for data_view in data_views:

        continents_pivot_df = merged_continents_df.pivot(
                                                    index='date',
                                                    columns='continent',
                                                    values=data_view)

        continent_names = list(continents_pivot_df.columns)

        continents_pivot_df['total'] = continents_pivot_df.sum(axis=1)

        continents_by_day_cds = ColumnDataSource(continents_pivot_df)

        # Creating figure
        fig = figure(
                name=f"{data_view}_vbar",
                sizing_mode="scale_width",
                x_axis_type="datetime",
                plot_height=200)

        colors = [Spectral11[i] for i in range(len(continent_names))]

        # Adding vbar for data view
        vbar = fig.vbar_stack(
                    continent_names,
                    x="date",
                    width=timedelta(days=0.5),
                    color=colors,
                    legend_label=continent_names,
                    source=continents_by_day_cds)

        fig.legend.location = "top_left"

        # Adding hover tool
        hover = HoverTool(
                    tooltips=[
                        ("Date", "@date{%F}"),
                        ("Continent", "$name"),
                        (f"{data_view.replace('_', ' ').title()}",
                         "@$name{(0.0 a)}"),
                        (f"Global {data_view.replace('_', ' ').title()}",
                         "@total{(0.0 a)}")],
                    formatters={"@date": "datetime"})

        fig.add_tools(hover)

        # Creating panel for plot, filling panel dict
        panel = Panel(child=fig, title=data_view)
        panel_dict[data_view] = panel

    # Creating tab layouts and adding to root
    cases_tabs = Tabs(
                    tabs=[panel_dict["cases"],
                          panel_dict["new_cases"]],
                    name="daily_cases_tabs")
    curdoc().add_root(cases_tabs)

    deaths_tabs = Tabs(
                    tabs=[panel_dict["deaths"],
                          panel_dict["new_deaths"]],
                    name="daily_deaths_tabs")
    curdoc().add_root(deaths_tabs)

    vaccinations_tabs = Tabs(
                    tabs=[panel_dict["total_vaccinations"],
                          panel_dict["daily_vaccinations"]],
                    name="daily_vaccinations_tabs")
    curdoc().add_root(vaccinations_tabs)
