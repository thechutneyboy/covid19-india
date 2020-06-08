import pandas as pd
import numpy as np
import datetime as dt
import requests
import plotly.express as px
import plotly.graph_objects as go

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


if __name__ == '__main__':
    df = prep_data()
    print(df.head())

