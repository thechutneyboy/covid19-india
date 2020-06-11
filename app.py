import pandas as pd
import numpy as np
import datetime as dt
import plotly.express as px
import plotly.graph_objects as go
import dash
import dash_core_components as dcc
import dash_html_components as html

URL = r"https://api.covid19india.org/states_daily.json"

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
        (df_states['status'] == 'Confirmed') # & (~df_states['state'].isin(states_to_hide))
        ][['date', 'state', 'cases']]
    df_plot = pd.merge(left=df_plot, right=df_resolved, on=['date', 'state'], how='left')

    df_plot['total_resolved_cases'] = df_plot.groupby(['state'])['resolved_cases'].cumsum()
    df_plot['total_cases'] = df_plot.groupby(['state'])['cases'].cumsum()
    df_plot['weekly_cases'] = df_plot.groupby(['state'])['cases'].apply(lambda x: x.rolling(7).sum())
    df_plot['active_cases'] = df_plot['total_cases'] - df_plot['total_resolved_cases']
    df_plot['state'] = df_plot['state'].map(lambda x: STATE_GLOSSARY[x])
    df_plot['date_f'] = df_plot['date'].map(lambda x: dt.datetime.strptime(x, '%d-%b-%y'))

    return df_plot


def create_figure(df_plot):
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
        title='India COVID-19 States Growth Trend<br>' + '<sub>Size of bubble indicates active cases</sub>',
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
    fig.update_traces(textposition='top center')

    """Add streaklines for each bubble in each frame"""
    fig.add_traces([go.Scatter(x=[0, 10], y=[0, 10], showlegend=False) for i in df_plot['state'].unique()])
    for i, f in enumerate(fig.frames):
        for s in df_plot['state'].unique():
            df_data = df_plot[(df_plot['date_f'] <= df_plot['date_f'].unique()[i]) & (df_plot['state'] == s)]
            f.data = f.data + (go.Scatter(
                x=df_data['total_cases'], y=df_data['weekly_cases'],
                mode='lines', legendgroup=s, name=s, showlegend=False,
                line=dict(color='lightgrey'), opacity=0.5
            ),)
    annotations = []
    doubling_time = [2, 7, 21]
    for i in doubling_time:
        fig.add_trace(go.Scatter(x=[100, 300000], y=[(1 - 1 / 2 ** (7 / i)) * 100, (1 - 1 / 2 ** (7 / i)) * 300000],
                                 name=f'{i}-Day Doubling', mode='lines',
                                 line=dict(dash='dot', color='grey')))
        annotations.append(dict(x=np.log10(300000), y=np.log10((1 - 1 / 2 ** (7 / i)) * 300000),
                                text=f'{i}-Day Doubling', showarrow=False,
                                xshift=50, align='left'))

    fig.update_layout(annotations=annotations, height=700)
    return fig


df = prep_data()
fig_covid = create_figure(df)

"""Initiate the dash app"""
app = dash.Dash()
server = app.server
app.layout = html.Div([
    dcc.Graph(
        id='COVID-19-india',
        figure=fig_covid
    )
])

if __name__ == '__main__':
    app.run_server()

