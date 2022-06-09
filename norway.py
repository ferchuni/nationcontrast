import asyncio
import json
from datetime import datetime

from request import request
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import numpy as np
import pandas as pd
import urllib.parse
from js import console
from js import bootstrap
from pyodide import to_js


class NorwayApiManager:

    def __init__(self):
        self.api_base_url = "https://data.norges-bank.no/api/"
        self.time_series_name_mapping = {'currency': 'B.USD.NOK.SP', 'cpi': ''}
        self.data = {'currency': [], 'cpi': []}

    def get_api_url(self, series_id, **kwargs):
        return "{}{}/{}?{}".format(self.api_base_url, "data/EXR", series_id, urllib.parse.urlencode(kwargs))

    async def get_data_from_api(self, time_series_name):
        api_url = self.get_api_url(time_series_name, format="sdmx-json", startPeriod='2022-01-01',
                                   endPeriod='2022-04-10')
        headers = {"Content-type": "application/json"}
        response = await request(api_url, method="GET", headers=headers)
        result = await response.json()
        return result

    async def get_time_series(self, index_name):
        series_name = self.time_series_name_mapping[index_name]
        if series_name:
            result = await self.get_data_from_api(series_name)
            self.data[index_name] = result

    async def get_all_time_series(self):
        await self.get_time_series('currency')


class NorwayDataManager:

    def __init__(self, data=None, csv_mode=None):
        self.data = data
        if csv_mode:
            self.csv_url = '''https://www.norges-bank.no/globalassets/marketdata/ppo/kpi/kpi_tab_en.csv?v=05/11/2022140203&ft=.csv'''

    def filter_data(self, name):
        values = self.data[name].get('data').get('dataSets')[0].get('series').get("0:0:0:0").get('observations')
        dates = self.data[name].get('data').get('structure').get('dimensions').get('observation')[0].get('values')
        x_values = [r.get('name') for r in dates if r.get('name') is not None]
        y_values = [float(r[0]) for r in values.values() if r[0] is not None]
        return x_values, y_values

    def get_panda_dataframe(self, name):
        x_values, y_values = self.filter_data(name)
        df = pd.DataFrame({'x_values': x_values, name.capitalize(): y_values})
        return df

    def filter_cpi_data(self, data):
        lines = data.split()
        values = [c.split(',') for c in lines[3:]]
        result = [(datetime.strptime(e[0], '%b.%y'), e[1]) for e in values if
                  datetime.strptime(e[0], '%b.%y') >= datetime(2022, 1, 1)]
        x_values = [e[0] for e in result]
        y_values = [e[1] for e in result]
        return x_values, y_values

    async def get_panda_dataframe_cpi(self, data):
        x_values, y_values = self.filter_cpi_data(data)
        df = pd.DataFrame({'x_values': x_values, 'CPI': y_values})
        return df

    async def get_cpi_data_from_csv(self):
        response = await request(self.csv_url, method="GET")
        result = await response.string()
        return result


class NorwayPlotManager:

    def __init__(self, dataframes):
        self.dfs = dataframes
        self.figures = {}

    def plot_dataframe(self, plot_type):
        index = self.dfs[plot_type].columns
        fig, ax = plt.subplots()
        ax.plot(index[0], index[1], data=self.dfs[plot_type], marker='o', markerfacecolor='blue', markersize=4,
                color='skyblue',
                linewidth=4)
        if plot_type == 'currency':
            min_tick_value = int(min(self.dfs.get(plot_type)[index[1]]))
            max_tick_value = int(max(self.dfs.get(plot_type)[index[1]])) + 1
            ax.set_yticks(np.arange(min_tick_value, max_tick_value, 0.5))
            ax.xaxis.set_major_locator(mdates.DayLocator(interval=7))
        fig.autofmt_xdate()
        plt.legend()
        self.figures[plot_type] = fig
        return fig

    def get_figure(self, name):
        return self.figures[name]
