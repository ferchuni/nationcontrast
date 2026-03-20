import matplotlib.pyplot as plt


class PlotManager:

    def __init__(self, dataframes):
        self.dfs = dataframes
        self.figures = {}

    def plot_dataframe(self, plot_type):
        index = self.dfs[plot_type].columns
        fig, ax = plt.subplots()
        fig.set_facecolor('none')
        ax.set_facecolor('#161b22')
        n_points = len(self.dfs[plot_type])
        marker = 'o' if n_points < 100 else None
        markersize = 3 if n_points < 100 else 0
        ax.plot(index[0], index[1], data=self.dfs[plot_type], marker=marker, markerfacecolor='#66ffdd',
                markersize=markersize, color='#00d4aa', linewidth=2)
        ax.tick_params(colors='#8b949e')
        ax.xaxis.label.set_color('#c9d1d9')
        ax.yaxis.label.set_color('#c9d1d9')
        ax.grid(True, alpha=0.15, color='#8b949e')
        for spine in ax.spines.values():
            spine.set_visible(False)
        ax.xaxis.set_major_locator(plt.MaxNLocator(nbins=8))
        ax.yaxis.set_major_locator(plt.MaxNLocator(nbins=10))
        ax.tick_params(axis='x', rotation=45, labelsize=7)
        fig.autofmt_xdate()
        plt.legend(facecolor='#161b22cc', edgecolor='#30363d', labelcolor='#c9d1d9')
        fig.tight_layout()
        self.figures[plot_type] = fig
        return fig

    def get_figure(self, name):
        return self.figures[name]
