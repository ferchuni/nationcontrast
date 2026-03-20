import datetime
from request import request
import pandas as pd
import urllib.parse


class ArgentinaApiManager:

    def __init__(self):
        self.api_base_url = "https://apis.datos.gob.ar/series/api/"
        self.time_series_name_mapping = {'currency': '168.1_T_CAMBIOR_D_0_0_26', 'cpi': '148.3_INIVELNAL_DICI_M_26'}
        self.data = {'currency': [], 'cpi': []}

    def get_api_url_(self, ids, **kwargs):
        kwargs["ids"] = ",".join(ids)
        return "{}{}?{}".format(self.api_base_url, "series", urllib.parse.urlencode(kwargs))

    async def get_data_from_api(self, time_series_name, index_name):
        if index_name == 'cpi':
            params = {'format': "json", 'representation_mode': 'percent_change_a_year_ago', 'start_date': '2022', 'limit': 5000}
        else:
            params = {'format': "json", 'start_date': '2022', 'limit': 5000}
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
        x_values = []
        y_values = []
        for r in self.data[name].get('data'):
            if r[1] is None:
                continue
            if datetime.datetime.strptime(r[0], '%Y-%m-%d') < datetime.datetime(2022, 1, 1):
                continue
            x_values.append(r[0])
            y_values.append(int(r[1] * 100) if name == 'cpi' else float(r[1]))
        return x_values, y_values

    def get_panda_dataframe(self, name):
        x_values, y_values = self.filter_data(name)
        label = 'CPI' if name == 'cpi' else 'Currency'
        df = pd.DataFrame({'x_values': x_values, label: y_values})
        return df
