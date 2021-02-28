from bokeh.io import curdoc
from bokeh.models import (
    HoverTool, TapTool, GeoJSONDataSource, ColorBar,
    ColumnDataSource, Select)
from bokeh.plotting import Figure
from bokeh.palettes import brewer
from bokeh.transform import linear_cmap
import pandas as pd
import numpy as np
from pathlib import Path
import geopandas as gpd
import json
from datetime import timedelta


def build_local_uk_tab(): 

    # Importing geographical shapefile for local authority boundaries
    root_dir = Path(__file__).parent.parent

    la_boundaries_gdf = (gpd.read_file(
                                root_dir.joinpath(
                                    'data', 'geo_data',
                                    'la_districts_dec19',
                                    'simplified',
                                    'Local_Authority_Districts__December_2019'
                                    '__Boundaries_UK_BFC.shp'))
                         .loc[:, ['lad19cd', 'lad19nm', 'geometry']])

    # Importing uk local authority data
    la_cases_df = pd.read_csv(
                        root_dir.joinpath(
                            'data', 'data_view',
                            'local_uk.csv'))

    # Filter for latest date
    la_cases_latest_df = la_cases_df.loc[
                            la_cases_df.date == la_cases_df.date.max()]

    # Import local authority population data
    la_pop_df = (pd.read_csv(
                    root_dir.joinpath(
                        'data', 'geo_data',
                        'local_authority_populations.csv'))
                 .loc[:, ['code', 'population']])
    
    # Remove commas and convert to numeric dtype
    la_pop_df['population'] = pd.to_numeric(
                                    (la_pop_df['population']
                                        .str.replace(",", "")))
    
    # Merge cases and population datasets
    la_cases_latest_df = la_cases_latest_df.merge(
                                la_pop_df,
                                left_on="area_code",
                                right_on="code",
                                how="left")

    # Merge geo-boundaries GeoDataFrame with cases, pop dataset
    la_cases_gdf = la_boundaries_gdf.merge(
                                        la_cases_latest_df,
                                        left_on="lad19cd",
                                        right_on="area_code",
                                        how="left")

    # Calculate weekly cases per 100,000
    la_cases_gdf['cases_per_pop'] = (100000 * la_cases_gdf['weekly_cases'] /
                                     la_cases_gdf['population']
                                     ).fillna(0).astype(int)

    # Convert dataset to GeoJSONDataSource to feed geo-plot
    geosource = GeoJSONDataSource(
                    geojson=la_cases_gdf.to_json())

    # Adding figure and geographical patches from shapefile
    local_uk_geo_plot = Figure(
                            title="Weekly Cases per 100,000",
                            plot_height=500,
                            plot_width=500,
                            name="local_uk_geo_plot",
                            output_backend="webgl")

    # Add linear colour mapper for case density
    mapper = linear_cmap(
                field_name='cases_per_pop',
                palette=brewer['YlOrRd'][9][:7][::-1],
                low=min(la_cases_gdf['cases_per_pop']),
                high=max(la_cases_gdf['cases_per_pop']))

    # Add local authority patches to figure
    geo_patches = local_uk_geo_plot.patches(
                                        'xs', 'ys',
                                        source=geosource,
                                        alpha=0.8,
                                        color=mapper)

    # Adding hover tool and tap tool
    hover = HoverTool(tooltips=[
                ('Local Authority', '@lad19nm'),
                ('Daily Cases', '@new_cases'),
                ('Population', '@population{0,0}'),
                ('Weekly Cases per 100,000', '@cases_per_pop')])

    local_uk_geo_plot.add_tools(hover)
    local_uk_geo_plot.add_tools(TapTool())

    # Adding color bar
    color_bar = ColorBar(
                    color_mapper=mapper['transform'],
                    location=(0, 0))

    local_uk_geo_plot.add_layout(color_bar, 'right')

    # Adding recent trend figure
    area_name = "Wandsworth"
    cases_trend_df = la_cases_df.loc[la_cases_df.area_name == area_name]
    cases_trend_df.date = pd.to_datetime(cases_trend_df.date,
                                         format="%Y-%m-%d")
    ninety_days_back = cases_trend_df.date.max() - timedelta(days=90)
    cases_trend_df = cases_trend_df.loc[
                        cases_trend_df.date >= ninety_days_back]
    cases_trend_cds = ColumnDataSource(cases_trend_df)

    cases_trend_plot = Figure(
            title=f"New Cases in {area_name}",
            plot_height=500,
            plot_width=500,
            name="cases_trend_plot",
            x_axis_type="datetime")

    cases_trend_plot.line(x='date',
                          y='new_cases',
                          legend="New Cases",
                          source=cases_trend_cds)

    cases_trend_plot.line(x='date',
                          y='weekly_average',
                          line_color="orange",
                          legend="Weekly Average",
                          source=cases_trend_cds)

    cases_trend_hover = HoverTool(
                            tooltips=[
                                ('Date', '@date{%F}'),
                                ('Daily Cases', '@new_cases'),
                                ('Weekly Average', '@weekly_average{int}')],
                            formatters={"@date": "datetime"})

    cases_trend_plot.add_tools(cases_trend_hover)

    def callback(attr, old, new):
        index = geosource.selected.indices[0]
        geojson = json.loads(geosource.geojson)
        area_name = geojson['features'][index]['properties']['area_name']

        # Adding recent trend figure
        cases_trend_df = la_cases_df.loc[la_cases_df.area_name == area_name]
        cases_trend_df.date = pd.to_datetime(cases_trend_df.date,
                                             format="%Y-%m-%d")
        ninety_days_back = cases_trend_df.date.max() - timedelta(days=90)
        cases_trend_df = cases_trend_df.loc[
                            cases_trend_df.date >= ninety_days_back]

        cases_trend_cds.data = cases_trend_df

        cases_trend_plot.title.text = f"New Cases in {area_name}"

    geosource.selected.on_change('indices', callback)

    # Add the plots to the current document
    curdoc().add_root(local_uk_geo_plot)
    curdoc().add_root(cases_trend_plot)

