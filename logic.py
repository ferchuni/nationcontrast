import asyncio  # important!!
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



class ApiManager:

    def __init__(self):
        self.api_base_url = "https://apis.datos.gob.ar/series/api/"
        self.time_series_name_mapping = {'currencies': {'Argentina': '168.1_T_CAMBIOR_D_0_0_26', 'Norway': ''},
                                         'cpi': {'Argentina': '105.1_I2N_2016_M_14', 'Norway': ''}}
        self.data = {'currencies': {'Argentina': [], 'Norway': []}, 'cpi': {'Argentina': [], 'Norway': []}}

    def get_api_url(self, ids, **kwargs):
        kwargs["ids"] = ",".join(ids)
        return "{}{}?{}".format(self.api_base_url, "series", urllib.parse.urlencode(kwargs))

    async def get_data_from_api(self, time_series_name):
        api_url = self.get_api_url([time_series_name], format="json", start_date=2022)
        headers = {"Content-type": "application/json"}
        response = await request(api_url, method="GET", headers=headers)
        result = await response.json()
        return result

    async def get_time_series(self, index_name):
        for country, series_name in self.time_series_name_mapping[index_name].items():
            if series_name:
                result = await self.get_data_from_api(series_name)
                self.data[index_name][country] = result

    async def get_all_time_series(self):
        await self.get_time_series('currencies')
        await self.get_time_series('cpi')


class DataManager:

    def __init__(self, data):
        self.data = data

    def filter_data(self, name, country):
        x_values = [r[0] for r in self.data[name][country].get('data') if r[1] is not None]
        y1_values = [float(r[1]) for r in self.data[name][country].get('data') if r[1] is not None]
        return x_values, y1_values

    def get_panda_dataframe(self, name, country):
        x_values, y1_values = self.filter_data(name, country)
        if name == 'currencies':
            df = pd.DataFrame({'x_values': x_values, 'Currency': y1_values})
        else:
            df = pd.DataFrame({'x_values': x_values, 'CPI': y1_values})

        return df


class PlotManager:
    plots = {}

    def __init__(self, dataframe):
        self.df = dataframe

    def plot_dataframe(self, name, div_id):
        index = self.df.columns
        fig, ax = plt.subplots()
        ax.plot(index[0], index[1], data=self.df, marker='o', markerfacecolor='blue', markersize=4,
                color='skyblue',
                linewidth=4)

        if name == 'currencies':
            ax.set_yticks(np.arange(int(min(self.df[index[1]])), int(max(self.df[index[1]])) + 1, 0.5))
            ax.xaxis.set_major_locator(mdates.DayLocator(interval=7))
        fig.autofmt_xdate()
        plt.legend()
        PlotManager.plots[div_id] = fig
        pyscript.write(div_id, fig)
        return fig

    @classmethod
    def get_plot(cls, name):
        return cls.plots[name]


class PageManager:

    def __init__(self):
        self.plots_names = ['plot1', 'plot2']
        self.modal = None

    def zoom_plot(self, name):
        figure = PlotManager.get_plot(name)
        figure.set_size_inches(13, 7)
        pyscript.write('plot-modal', figure)
        self.modal.show()

    def init_modal(self):
        self.modal = bootstrap.Modal.new(document.getElementById('full-plot'), {'keyboard': False})

    def add_zoom_events(self, plot_names):
        def evt(e=None):
            id = e.currentTarget.id
            self.zoom_plot(id.replace('zoom-', ''))
            if e:
                e.preventDefault()
            return False

        for name in plot_names:
            refresh_link = document.getElementById(f'zoom-{name}')
            refresh_link.onclick = evt

    def init_page(self):
        self.init_modal()
        self.add_zoom_events(self.plots_names)


async def main():
    PageManager().init_page()
    am = ApiManager()
    await am.get_all_time_series()
    dm = DataManager(am.data)
    df1 = dm.get_panda_dataframe('currencies', 'Argentina')
    df2 = dm.get_panda_dataframe('cpi', 'Argentina')
    pm = PlotManager(df1)
    pm2 = PlotManager(df2)
    pm.plot_dataframe('currencies', 'plot1')
    pm2.plot_dataframe('cpi', 'plot2')


main()
