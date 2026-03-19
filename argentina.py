import asyncio
import datetime
import json
from request import request
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import numpy as np
import pandas as pd
import urllib.parse
from js import console
from js import bootstrap
from pyodide.ffi import to_js


class ArgentinaApiManager:

    def __init__(self):
        self.api_base_url = "https://apis.datos.gob.ar/series/api/"
        self.time_series_name_mapping = {'currency': '168.1_T_CAMBIOR_D_0_0_26', 'cpi': '105.1_I2N_2016_M_14'}
        self.data = {'currency': [], 'cpi': []}

    def get_api_url_(self, ids, **kwargs):
        kwargs["ids"] = ",".join(ids)
        return "{}{}?{}".format(self.api_base_url, "series", urllib.parse.urlencode(kwargs))

    async def get_data_from_api(self, time_series_name, index_name):
        if index_name == 'cpi':
            params = {'format': "json", 'representation_mode': 'percent_change_a_year_ago'}
        else:
            params = {'format': "json", 'start_date': '2022'}
        api_url = self.get_api_url_([time_series_name], **params)
        headers = {"Content-type": "application/json"}
        response = await request(api_url, method="GET", headers=headers)
        result = await response.json()
        return result

    async def get_time_series(self, index_name):
        series_name = self.time_series_name_mapping[index_name]
        if series_name:
            result = await self.get_data_from_api(series_name, index_name)
            self.data[index_name] = result

    async def get_all_time_series(self):
        await self.get_time_series('currency')
        await self.get_time_series('cpi')


class ArgentinaDataManager:

    def __init__(self, data):
        self.data = data

    def filter_data(self, name):
        x_values = [r[0] for r in self.data[name].get('data') if
                    datetime.datetime.strptime(r[0], '%Y-%m-%d') >= datetime.datetime(2022, 1, 1) and r[1] is not None]
        y_values = [int(r[1] * 100) if name == 'cpi' else float(r[1]) for r in self.data[name].get('data') if
                    datetime.datetime.strptime(r[0], '%Y-%m-%d') >= datetime.datetime(2022, 1, 1) and r[1] is not None]
        return x_values, y_values

    def get_panda_dataframe(self, name):
        x_values, y_values = self.filter_data(name)
        if name == 'currency':
            df = pd.DataFrame({'x_values': x_values, 'Currency': y_values})
        else:
            df = pd.DataFrame({'x_values': x_values, 'CPI': y_values})
        return df


class ArgentinaPlotManager:

    def __init__(self, dataframes):
        self.dfs = dataframes
        self.figures = {}

    def plot_dataframe(self, plot_type):
        index = self.dfs[plot_type].columns
        fig, ax = plt.subplots()
        fig.set_facecolor('#1a1a2e')
        ax.set_facecolor('#1a1a2e')
        ax.plot(index[0], index[1], data=self.dfs[plot_type], marker='o', markerfacecolor='#66ffdd',
                markersize=3, color='#00d4aa', linewidth=2)
        ax.tick_params(colors='#8b949e')
        ax.xaxis.label.set_color('#c9d1d9')
        ax.yaxis.label.set_color('#c9d1d9')
        ax.grid(True, alpha=0.15, color='#8b949e')
        for spine in ax.spines.values():
            spine.set_color('#30363d')
        if plot_type == 'currency':
            min_tick_value = int(min(self.dfs.get(plot_type)[index[1]]))
            max_tick_value = int(max(self.dfs.get(plot_type)[index[1]])) + 1
            ax.set_yticks(np.arange(min_tick_value, max_tick_value, 0.5))
            ax.xaxis.set_major_locator(mdates.DayLocator(interval=7))
        fig.autofmt_xdate()
        plt.legend(facecolor='#1a1a2e', edgecolor='#30363d', labelcolor='#c9d1d9')
        fig.tight_layout()
        self.figures[plot_type] = fig
        return fig

    def get_figure(self, name):
        return self.figures[name]
