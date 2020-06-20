import pandas as pd
import numpy as np
import datetime as dt
from functools import partial

import plotly.express as px
import plotly.graph_objects as go
import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output


URL = r"https://api.covid19india.org/states_daily.json"
githublink='https://github.com/thechutneyboy/covid19-india'
videourl='https://www.youtube.com/watch?v=54XLXg4fYsc'

STATE_GLOSSARY = {
    'ap': 'Andhra Pradesh',
    'ar': 'Arunachal Pradesh',
    'as': 'Assam',
    'br': 'Bihar',
    'ct': 'Chhattisgarh',
    'ga': 'Goa',
    'gj': 'Gujarat',
    'hr': 'Haryana',
    'hp': 'Himachal Pradesh',
    'jh': 'Jharkhand',
    'ka': 'Karnataka',
    'kl': 'Kerala',
    'mp': 'Madhya Pradesh',
    'mh': 'Maharashtra',
    'mn': 'Manipur',
    'ml': 'Meghalaya',
    'mz': 'Mizoram',
    'nl': 'Nagaland',
    'or': 'Odisha',
    'pb': 'Punjab',
    'rj': 'Rajasthan',
    'sk': 'Sikkim',
    'tn': 'Tamil Nadu',
    'tg': 'Telangana',
    'tr': 'Tripura',
    'tt': 'Total',
    'un': 'Unassigned',
    'ut': 'Uttarakhand',
    'up': 'Uttar Pradesh',
    'wb': 'West Bengal',
    'an': 'Andaman and Nicobar Islands',
    'ch': 'Chandigarh',
    'dn': 'Dadra and Nagar Haveli',
    'dd': 'Daman and Diu',
    'dl': 'Delhi',
    'jk': 'Jammu and Kashmir',
    'la': 'Ladakh',
    'ld': 'Lakshadweep',
    'py': 'Puducherry'
}


def prep_data():
    df = pd.read_json(path_or_buf=URL, orient=['records', 'index'])
    df = pd.DataFrame(df['states_daily'].tolist())
    col_state = [c for c in df.columns if c not in ['date', 'status']]
    col_new_order = ['date', 'status'] + col_state
    df[col_state] = df[col_state].applymap(int)
    df = df[col_new_order]

    """Unpivot/melt the state columns"""
    df_states = df.melt(id_vars=['date', 'status']).rename(
        columns={'variable': 'state', 'value': 'cases'}
    )

    df_resolved = df_states[df_states['status'].isin(
        ['Recovered', 'Deceased']
    )].groupby(['date', 'state']).agg(
        {'cases': 'sum'}
    ).reset_index().rename(columns={'cases': 'resolved_cases'})

    df_plot = df_states[
        (df_states['status'] == 'Confirmed') & (~df_states['state'].isin(['un']))
        ][['date', 'state', 'cases']]
    df_plot = pd.merge(left=df_plot, right=df_resolved, on=['date', 'state'], how='left')

    df_plot['total_resolved_cases'] = df_plot.groupby(['state'])['resolved_cases'].cumsum()
    df_plot['total_cases'] = df_plot.groupby(['state'])['cases'].cumsum()
    df_plot['weekly_cases'] = df_plot.groupby(['state'])['cases'].apply(lambda x: x.rolling(7).sum())
    df_plot['active_cases'] = df_plot['total_cases'] - df_plot['total_resolved_cases']
    df_plot['state'] = df_plot['state'].map(lambda x: STATE_GLOSSARY[x])
    df_plot['date_f'] = df_plot['date'].map(lambda x: dt.datetime.strptime(x, '%d-%b-%y'))

    """Filter for daily data for last 21 days and weekly data before that"""
    dates = df_plot['date_f'].unique()
    filtered_dates = [d for i, d in enumerate(dates) if i >= len(dates)-21 or i % 7 == 0]
    df_plot = df_plot[df_plot['date_f'].isin(filtered_dates)]

    return df_plot


def create_streaklines(df: pd.DataFrame):
    """Streak Data"""
    streak_total = []
    streak_weekly = []
    for i, row in df.iterrows():
        filter_cond = (df['state'] == row['state']) & (df['date_f'] <= row['date_f'])
        streak_total.append(df.loc[filter_cond, 'total_cases'].tolist())
        streak_weekly.append(df.loc[filter_cond, 'weekly_cases'].tolist())
    df = df.assign(**pd.Series({'streak_total': streak_total, 'streak_weekly': streak_weekly}))

    streak_scatter = partial(go.Scatter, mode='lines', showlegend=False, line=dict(color='lightgrey'), opacity=0.5)

    df['scatter'] = np.vectorize(streak_scatter)(
        x=df['streak_total'], y=df['streak_weekly'], legendgroup=df['state'], name=df['state'])

    return df


df_plot = prep_data()

"""Initiate the dash app"""
app = dash.Dash(__name__)
server = app.server
app.title = 'India COVID-19 States Growth Trend'

app.layout = html.Div(children=[
    html.H1('India COVID-19 States Growth Trend'),
    dcc.Loading(
        id="loading",
        type="default",
        fullscreen=True,
        children=dcc.Graph(id='bubble_graph')
    ),
    dcc.Interval(
        id='fire_graph',
        interval=0,
        max_intervals=0,
        n_intervals=0
    ),
    html.A('Code on Github', href=githublink),
    html.Br(),
    html.A('Watch video by Minute Physics to understand "If we are really beating COVID-19? "', href=videourl),
])


@app.callback(Output('bubble_graph', 'figure'),
              [Input('fire_graph', 'n_intervals')])
def update_figure(n):
    global df_plot
    df_plot = create_streaklines(df_plot)
    df_plot = df_plot[~pd.isnull(df_plot['weekly_cases'])]  # remove null days
    x_max = 10 ** (int(np.log10(df_plot['total_cases'].max())) + 2)
    y_max = 10 ** (int(np.log10(df_plot['weekly_cases'].max())) + 2)
    fig = px.scatter(
        data_frame=df_plot,
        x='total_cases', y='weekly_cases',
        size='active_cases', size_max=100,
        color='state', hover_name='state',
        text='state',
        log_x=True, log_y=True,
        template='plotly_white',
        range_x=[100, x_max], range_y=[10, y_max],
        labels={
            'date': 'Date',
            'state': 'State',
            'total_cases': 'Total Cases',
            'weekly_cases': 'New Cases in the Past Week',
            'active_cases': 'Active Cases'
        },
        animation_group='state',
        animation_frame='date',
    )

    """Add streaklines for each bubble in each frame"""
    fig.add_traces([go.Scatter(x=[0, 10], y=[0, 10], showlegend=False) for i in df_plot['state'].unique()])
    dates = df_plot['date_f'].unique()
    for i, f in enumerate(fig.frames):
        f.data = tuple(df_plot.loc[df_plot['date_f'] == dates[i], 'scatter']) + f.data

    fig.update_traces(textposition='top center')

    annotations = []
    doubling_time = [2, 7, 21]
    for i in doubling_time:
        fig.add_trace(go.Scatter(x=[100, 1000000], y=[(1 - 1 / 2 ** (7 / i)) * 100, (1 - 1 / 2 ** (7 / i)) * 1000000],
                                 name=f'{i}-Day Doubling', mode='lines',
                                 line=dict(dash='dot', color='grey')))
        annotations.append(dict(x=np.log10(1000000), y=np.log10((1 - 1 / 2 ** (7 / i)) * 1000000),
                                text=f'{i}-Day Doubling', showarrow=False,
                                xshift=50, align='left'))

    fig.update_layout(annotations=annotations, height=700)
    return fig


if __name__ == '__main__':
    app.run_server()

