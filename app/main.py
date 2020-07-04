from bokeh.io import curdoc
from bokeh.models import (Div, ColumnDataSource, DatetimeTickFormatter,
                         DaysTicker, HoverTool, Span, Label, Title, Tabs)
from bokeh.models.widgets import Panel
from bokeh.layouts import row
from bokeh.plotting import figure
from bokeh.palettes import viridis
import pandas as pd
import numpy as np
import math
from datetime import datetime, timedelta
from layouts import main_tab, global_tab, countries_tab
from bokeh.themes import built_in_themes

main_tab = main_tab()
global_tab = global_tab()
countries_tab = countries_tab()

apptabs = Tabs(
        name="apptabs",
        tabs=[main_tab, global_tab, countries_tab])

curdoc().add_root(apptabs)
#curdoc().theme = 'dark_minimal'