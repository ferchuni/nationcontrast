import asyncio
import json
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
        await self.get_time_series('cpi')


class NorwayDataManager:

    def __init__(self, data):
        self.data = data

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


class NorwayPlotManager:

    def __init__(self, dataframe):
        self.df = dataframe
        self.figures = {}

    def plot_dataframe(self, plot_type):
        index = self.df.columns
        fig, ax = plt.subplots()
        ax.plot(index[0], index[1], data=self.df, marker='o', markerfacecolor='blue', markersize=4,
                color='skyblue',
                linewidth=4)
        if plot_type == 'currency':
            min_tick_value = int(min(self.df[index[1]]))
            max_tick_value = int(max(self.df[index[1]])) + 1
            ax.set_yticks(np.arange(min_tick_value, max_tick_value, 0.5))
            ax.xaxis.set_major_locator(mdates.DayLocator(interval=7))
        fig.autofmt_xdate()
        plt.legend()
        self.figures[plot_type] = fig
        return fig

    def get_figure(self, name):
        return self.figures[name]
