import asyncio
import warnings
warnings.filterwarnings('ignore', message='.*Pyarrow.*')
import matplotlib
matplotlib.use('agg')
import matplotlib.pyplot as plt
from js import console
from js import bootstrap
from js import document
from pyscript import display

from argentina import ArgentinaApiManager, ArgentinaDataManager
from norway import NorwayApiManager, NorwayDataManager
from plot import PlotManager

# Set matplotlib dark style for all plots
plt.style.use('dark_background')
plt.rcParams['figure.facecolor'] = 'none'
plt.rcParams['savefig.facecolor'] = 'none'
plt.rcParams['savefig.transparent'] = True
plt.rcParams['axes.facecolor'] = '#161b22'
plt.rcParams['text.color'] = '#c9d1d9'
plt.rcParams['axes.labelcolor'] = '#c9d1d9'
plt.rcParams['xtick.color'] = '#8b949e'
plt.rcParams['ytick.color'] = '#8b949e'

LOADING_HTML = '''<div class="d-flex justify-content-center py-4">
    <strong class="text-secondary me-2">Gathering data in real time ... </strong>
    <div class="spinner-border spinner-border-sm text-info" role="status">
        <span class="visually-hidden">Loading...</span>
    </div>
</div>'''


class PageManager:

    def __init__(self, arg_plot_manager=None):
        self.div_ids = ['currency', 'cpi']
        self.modal = None
        self.arg_plot_manager = arg_plot_manager
        self.norway_plot_manager = None

    def init_modal(self):
        self.modal = bootstrap.Modal.new(document.getElementById('full-plot'), {'keyboard': False})

    def plot_init_images(self):
        for div in self.div_ids:
            fig = self.arg_plot_manager.get_figure(div)
            display(fig, target=div, append=False)

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
        page = self

        def evt(e=None):
            value = e.target.value
            select_name = e.target.id
            div_name = fig_name = select_name.replace('select-country-', '')
            if value == 'Argentina':
                display(page.arg_plot_manager.get_figure(fig_name), target=div_name, append=False)
            if value == 'Norway':
                if page.norway_plot_manager is not None:
                    display(page.norway_plot_manager.get_figure(fig_name), target=div_name, append=False)
                else:
                    document.getElementById(div_name).innerHTML = LOADING_HTML
            if e:
                e.preventDefault()

        for name in div_names:
            select_link = document.getElementById(f'select-country-{name}')
            select_link.onchange = evt

    def set_norway_plot_manager(self, npm):
        self.norway_plot_manager = npm
        # If user already selected Norway, update the visible charts
        for div in self.div_ids:
            select = document.getElementById(f'select-country-{div}')
            country = select.options.item(select.selectedIndex).text
            if country == 'Norway':
                display(npm.get_figure(div), target=div, append=False)

    def zoom_plot(self, index_type, country):
        if country == 'Argentina':
            fig = self.arg_plot_manager.get_figure(index_type)

        if country == 'Norway':
            if self.norway_plot_manager is None:
                return
            fig = self.norway_plot_manager.get_figure(index_type)

        title = f"{country} {index_type.replace('cpi', 'CPI').replace('currency', 'Currency')}"
        document.getElementById('ModalLabel').textContent = title
        display(fig, target='plot-modal', append=False)
        self.modal.show()

    def init_page(self):
        self.init_modal()
        self.add_zoom_events(self.div_ids)
        self.add_select_country_events(self.div_ids)
        self.plot_init_images()


async def main():
    try:
        # Start Norway loading in background
        aam = ArgentinaApiManager()
        nam_task = asyncio.ensure_future(load_norway_data())

        # Load Argentina and show immediately
        await aam.get_all_time_series()
        adm = ArgentinaDataManager(aam.data)
        df_arg_currency = adm.get_panda_dataframe('currency')
        df_arg_cpi = adm.get_panda_dataframe('cpi')
        apm = PlotManager({'currency': df_arg_currency, 'cpi': df_arg_cpi})
        apm.plot_dataframe("currency")
        apm.plot_dataframe("cpi")

        # Show Argentina charts, init page
        page_manager = PageManager(apm)
        page_manager.init_page()

        # Wait for Norway to finish and attach to page
        npm = await nam_task
        page_manager.set_norway_plot_manager(npm)

    except Exception as e:
        console.error(f"Error loading dashboard: {e}")
        for div_id in ['currency', 'cpi']:
            el = document.getElementById(div_id)
            el.innerHTML = f'<p class="text-danger text-center p-4">Error loading data. Please refresh.</p>'


async def load_norway_data():
    nam = NorwayApiManager()
    await nam.get_all_time_series()
    ndm = NorwayDataManager(nam.data)
    df_nor_currency = ndm.get_panda_dataframe('currency')
    df_nor_cpi = ndm.get_panda_dataframe('cpi')
    npm = PlotManager({'currency': df_nor_currency, 'cpi': df_nor_cpi})
    npm.plot_dataframe("currency")
    npm.plot_dataframe("cpi")
    return npm


await main()
