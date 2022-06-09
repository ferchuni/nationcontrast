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

from argentina import ArgentinaApiManager, ArgentinaDataManager, ArgentinaPlotManager
from norway import NorwayApiManager, NorwayDataManager, NorwayPlotManager


class PageManager:

    def __init__(self, arg_plot_manager=None, norway_plot_manager=None):
        self.div_ids = ['currency', 'cpi']
        self.modal = None
        self.current_fig = None
        self.arg_plot_manager = arg_plot_manager
        self.norway_plot_manager = norway_plot_manager

    def init_modal(self):
        self.modal = bootstrap.Modal.new(document.getElementById('full-plot'), {'keyboard': False})

    def plot_init_images(self):
        for div in self.div_ids:
            select = document.getElementById(f'select-country-{div}')
            country = select.options.item(select.selectedIndex).text
            if country == 'Argentina':
                fig = self.arg_plot_manager.get_figure(div)
            # Disabled for CPI. I have to find a time series for that.
            if country == 'Norway':
                fig = self.norway_plot_manager.get_figure(div)
            pyscript.write(div, fig)

    def add_zoom_events(self, plot_names):
        def evt(e=None):
            id = e.currentTarget.id
            index_type = id.replace('zoom-', '')
            select = document.getElementById(f'select-country-{index_type}')
            country = select.options.item(select.selectedIndex).text
            self.zoom_plot(index_type, country)
            if e:
                e.preventDefault()
            return False

        for name in plot_names:
            zoom_link = document.getElementById(f'zoom-{name}')
            zoom_link.onclick = evt

    def add_select_country_events(self, div_names):
        def evt(e=None):
            value = e.target.value
            select_name = e.target.id
            div_name = fig_name = select_name.replace('select-country-', '')
            if value == 'Argentina':
                pyscript.write(div_name, self.arg_plot_manager.get_figure(fig_name))
            if value == 'Norway':
                pyscript.write(div_name, self.norway_plot_manager.get_figure(fig_name))
            if e:
                e.preventDefault()
            return False

        for name in div_names:
            select_link = document.getElementById(f'select-country-{name}')
            console.log(select_link)
            select_link.onchange = evt

    def zoom_plot(self, index_type, country):
        if country == 'Argentina':
            fig = self.arg_plot_manager.get_figure(index_type)

        if country == 'Norway':
            fig = self.norway_plot_manager.get_figure(index_type)

        old_width, old_height = fig.get_size_inches()
        fig.set_size_inches(13, 7)
        pyscript.write('plot-modal', fig)
        self.modal.show()
        fig.set_size_inches(old_width, old_height)

    def init_page(self):
        self.init_modal()
        self.add_zoom_events(self.div_ids)
        self.add_select_country_events(self.div_ids)
        self.plot_init_images()


async def main():
    # Use API Manager to get time series from different sources
    aam = ArgentinaApiManager()
    nam = NorwayApiManager()
    await aam.get_all_time_series()
    await nam.get_all_time_series()
    # Use Data Manager to parse data properly and get a dataframe
    ndm = NorwayDataManager(nam.data)
    adm = ArgentinaDataManager(aam.data)
    df2 = adm.get_panda_dataframe('currency')
    df3 = adm.get_panda_dataframe('cpi')
    df1 = ndm.get_panda_dataframe('currency')
    # Use Plot Manager to create figures from dataframes
    apm = ArgentinaPlotManager({'currency': df2, 'cpi': df3})
    apm.plot_dataframe("currency")
    apm.plot_dataframe("cpi")
    # Use a csv file as data source for CPI
    # TODO - refactor/improve the manager logic
    ndm2 = NorwayDataManager(csv_mode=True)
    data = await ndm2.get_cpi_data_from_csv()
    df4 = await ndm2.get_panda_dataframe_cpi(data)
    # Use Plot Manager to plot both indices
    npm = NorwayPlotManager({'currency': df1, 'cpi': df4})
    npm.plot_dataframe("currency")
    npm.plot_dataframe("cpi")
    # Use Page Manager to register events and handle the page logic
    page_manager = PageManager(apm, npm)
    page_manager.init_page()


main()
