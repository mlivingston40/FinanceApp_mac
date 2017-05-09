import quandl
import numpy as np
import pandas as pd
from bokeh.plotting import figure
from bokeh.resources import CDN
from bokeh.embed import file_html
from bokeh.models import HoverTool, NumeralTickFormatter
from bokeh.charts import Bar
from bokeh.models import BoxAnnotation

from bokeh.layouts import widgetbox
from bokeh.models.widgets import Dropdown

from bokeh.layouts import column
from bokeh.models import CustomJS, ColumnDataSource, Slider



#quandl key#
quandl.ApiConfig.api_key = 'LUc6i68JzC1xFUsauSDm'

class TimeDecaySeries:

    def __init__(self, security, start_date, end_date):
        # need start and end date to be in format of "yyyy-mm-dd"
        self.security = security
        self.start_date = start_date
        self.end_date = end_date

        # need to bake in a 'min' end date for each security since data set no checks for this
        #for example NYSE_VXX doesnt have data til 2009, so any end date before this is no bueno
        self.data = quandl.get("GOOG/{}".format(self.security), start_date=self.start_date, end_date=self.end_date)

    def close_prices_graph (self):

        x, y = self.data.index, self.data.Close.values

        # Basic plot setup
        #plot_width=100, plot_height=400,
        p = figure(responsive = True, x_axis_type="datetime",
                      title="Close Prices vs. Date Range - {}".format(self.security),
                      tools="box_zoom,reset",
                      toolbar_location="right")

        # Title formatting
        p.title.text_color = "blue"
        p.title.text_font_style = "bold"

        # change just some things about the x-axes
        p.xaxis.axis_label = "Date"
        p.xaxis.axis_line_width = 4

        # change just some things about the y-axes
        p.yaxis.axis_label = "Close Price"
        p.yaxis.axis_line_width = 4
        p.yaxis.major_label_orientation = "vertical"

        p.line(x, y, line_dash="dotted", line_width=1, color='blue')

        cr = p.circle(x, y, size=10,
                         fill_color="grey", hover_fill_color="firebrick",
                         fill_alpha=0.05, hover_alpha=0.1,
                         line_color=None, hover_line_color="white")

        p.add_tools(HoverTool(tooltips=None, renderers=[cr], mode='hline'))

        return p

    def gains_data (self):

        ###Fastest way and least amount of code
        # %%timeit
        uniques = pd.DataFrame({'month': self.data.index.month, 'year': self.data.index.year}).drop_duplicates()
        max_date = self.data.index.max()
        maxs = []
        for m, y in zip(uniques.month, uniques.year):
            df = self.data[(self.data.index.month == m) & (self.data.index.year == y)]
            maxs.append(df.index.max())
        # take of the very last max
        maxs.pop()
        # find the special last month of max to know when to stop on how many days out
        maxs_date = np.array(maxs).max()

        # building gains df
        gains = []
        for i in maxs:
            if i == maxs_date:
                # finds the last max date available and the length going forward month
                days_out = list(range(0, len(self.data[(self.data.index.month == max_date.month)
                                                  & (self.data.index.year == max_date.year)])))
            else:
                # days out that we want to bucket on - currently set at 15 days
                days_out = list(range(0, 15))
            for x in days_out:
                points_gain = (self.data.shift(-(x + 1)).Close[i].item()) - self.data.Close[i].item()
                percent_gain = points_gain / (self.data.Close[i].item())
                gains.append({'date': i, 'days_out': x + 1, 'points_gain': points_gain,
                              'percent_gain': percent_gain})
        gains = pd.DataFrame(gains)
        # accounting for when last max day has greater than 15 data points ahead of it
        gains = gains[gains.days_out <= 15]

        return gains

    def gains_average (self):

        summary_count = self.gains_data().groupby('days_out').agg('count')
        summary_count.drop(summary_count.columns[[1, 2]], axis=1, inplace=True)
        summary_mean = self.gains_data().groupby('days_out').agg('mean')
        summary_mean.drop(summary_mean.columns[1], axis=1, inplace=True)
        summary = pd.concat([summary_mean, summary_count], axis=1)
        summary.columns = [['Average_Percent_Gain', 'Number_of_Points']]
        summary.index.rename('Selling_Days_Out', inplace=True)

        return summary

    def gains_summary_graph (self):

        source = self.gains_average()
        # add a column for green for positive and red for negative, this doesnt work w/ Bar, may have to build out
        #custom glyphs if really want like rect etc.....dont thing hover tools work tho...

        ##source['Colors'] = np.where(source['Average_Percent_Gain'] >= 0, 'green', 'red')

        tooltips = ([('Average Gain', '@height{0.00%}'), ('Days Out', '@index'), ('Data Points', '@Number_of_Points')])

        s = Bar(source, responsive= True, label='index', values='Average_Percent_Gain', stack='Number_of_Points',
                title="Average Percent Gain by Selling Days Out - {}".format(self.security), color = 'cornflowerblue', legend=False,
                tooltips=tooltips, xlabel='Selling Days Out', ylabel='Average Gain')

        pos_box = BoxAnnotation(plot=s, bottom=0, fill_alpha=0.2, fill_color='green')
        neg_box = BoxAnnotation(plot=s, top=0, fill_alpha=0.2, fill_color='red')

        s.renderers.extend([pos_box, neg_box])

        s.yaxis[0].formatter = NumeralTickFormatter(format="0.00%")

        return s

    def boxplot_scatter_graph (self):

        return "This was reached"

    def dropdown (self):

        menu = []
        for i in self.gains_data().days_out.unique():
            menu.append(("{}".format(i), "item{}".format(i)))
        dropdown = Dropdown(label="Days Out", button_type="warning", menu=menu)



        return widgetbox(dropdown)

    def testing (self):

        x = [x * 0.005 for x in range(0, 200)]
        y = x

        source = ColumnDataSource(data=dict(x=x, y=y))

        plot = figure(plot_width=400, plot_height=400)
        plot.line('x', 'y', source=source, line_width=3, line_alpha=0.6)

        callback = CustomJS(args=dict(source=source), code="""
                var data = source.get('data');
                var f = cb_obj.get('value')
                x = data['x']
                y = data['y']
                for (i = 0; i < x.length; i++) {
                    y[i] = Math.pow(x[i], f)
                }
                source.trigger('change');
            """)

        #slider = Slider(start=1, end=15, value=1, step=1, title="power", callback=callback)

        menu = []
        for i in self.gains_data().days_out.unique():
            menu.append(("{}".format(i), "{}".format(i)))
        dropdown = Dropdown(label="Days Out", button_type="warning", menu=menu, callback=callback)


        layout = column(dropdown, plot)

        return layout
