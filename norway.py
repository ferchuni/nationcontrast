from datetime import datetime
from request import request
import pandas as pd
import urllib.parse


class NorwayApiManager:

    def __init__(self):
        self.currency_base_url = "https://data.norges-bank.no/api/"
        self.cpi_base_url = "https://data.ssb.no/api/pxwebapi/v2/"
        self.data = {'currency': [], 'cpi': []}

    def get_currency_api_url(self, series_id, **kwargs):
        return "{}{}/{}?{}".format(self.currency_base_url, "data/EXR", series_id, urllib.parse.urlencode(kwargs))

    def get_cpi_api_url(self):
        params = {
            'lang': 'en',
            'valueCodes[VareTjenesteGrp]': '00',
            'valueCodes[ContentsCode]': 'Tolvmanedersendring',
            'valueCodes[Tid]': 'from(2022M01)',
            'outputFormat': 'json-stat2'
        }
        return "{}tables/14700/data?{}".format(self.cpi_base_url, urllib.parse.urlencode(params))

    async def get_currency_data(self):
        today = datetime.now().strftime('%Y-%m-%d')
        api_url = self.get_currency_api_url('B.USD.NOK.SP', format="sdmx-json",
                                             startPeriod='2022-01-01', endPeriod=today)
        headers = {"Content-type": "application/json"}
        response = await request(api_url, method="GET", headers=headers)
        result = await response.json()
        self.data['currency'] = result

    async def get_cpi_data(self):
        api_url = self.get_cpi_api_url()
        response = await request(api_url, method="GET")
        result = await response.json()
        self.data['cpi'] = result

    async def get_all_time_series(self):
        await self.get_currency_data()
        await self.get_cpi_data()


class NorwayDataManager:

    def __init__(self, data):
        self.data = data

    def filter_currency_data(self):
        values = self.data['currency'].get('data').get('dataSets')[0].get('series').get("0:0:0:0").get('observations')
        dates = self.data['currency'].get('data').get('structure').get('dimensions').get('observation')[0].get('values')
        x_values = [r.get('name') for r in dates if r.get('name') is not None]
        y_values = [float(r[0]) for r in values.values() if r[0] is not None]
        return x_values, y_values

    def filter_cpi_data(self):
        cpi_data = self.data['cpi']
        time_index = cpi_data['dimension']['Tid']['category']['index']
        values = cpi_data['value']
        sorted_times = sorted(time_index.items(), key=lambda x: x[1])
        x_values = []
        y_values = []
        for time_code, idx in sorted_times:
            if values[idx] is not None:
                year, month = time_code.replace('M', '-').split('-')
                x_values.append(f"{year}-{month}-01")
                y_values.append(float(values[idx]))
        return x_values, y_values

    def get_panda_dataframe(self, name):
        if name == 'currency':
            x_values, y_values = self.filter_currency_data()
        else:
            x_values, y_values = self.filter_cpi_data()
        label = 'CPI' if name == 'cpi' else name.capitalize()
        df = pd.DataFrame({'x_values': x_values, label: y_values})
        return df
