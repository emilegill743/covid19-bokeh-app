from bokeh.io import curdoc
from bokeh.models import (Div, ColumnDataSource, DatetimeTickFormatter,
                         DaysTicker, HoverTool, Span, Label, Title)
from bokeh.models.widgets import Tabs, Panel
from bokeh.layouts import row
from bokeh.plotting import figure
from bokeh.palettes import viridis
import pandas as pd
import numpy as np
import math
from datetime import datetime, timedelta
from tabs import lockdown_tab, countries_tab, global_tab
from bokeh.themes import built_in_themes

div = Div(text="""Div""")

global_tab = global_tab.build_global_tab()

countries_tab = countries_tab.build_countries_tab()

regions_tab = Panel(child=div, title='Regions')

lockdown_tab = lockdown_tab.build_lockdown_tab()

tabs = Tabs(
        name="tabs",
        tabs=[global_tab, countries_tab, regions_tab, lockdown_tab])

curdoc().add_root(tabs)
#curdoc().theme = 'dark_minimal'