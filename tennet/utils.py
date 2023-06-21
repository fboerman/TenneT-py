import pandas as pd

# the api for this is broken, so download manually file and then parse it with this function
def parse_imbalance2017_csv_download(fname):
    df = pd.read_csv(fname).rename(columns=lambda c: c.lower())\
        .drop(columns=['to regulate up_reserve', 'to regulate down_reserve'])
    df = df.rename(columns={
        'to regulate up': 'upward_dispatch',
        'to regulate down': 'downward_dispatch',
        'incident_reserve_up_indicator': 'up_indicator',
        'incident_reserve_down_indicator': 'down_indicator',
        'mid_price_upward': 'mid_price',
        'highest_price_upward': 'max_price',
        'lowest_price_downward': 'min_price'
    })
    df['up_indicator'] = df['up_indicator'].astype(bool)
    df['down_indicator'] = df['down_indicator'].astype(bool)
    df['date'] = pd.to_datetime(df['date'], format='%m/%d/%Y')

    def group_func(df_):
        date = df_['date'].iloc[0]
        S_today = pd.Series(
            data=pd.date_range(date.strftime('%Y-%m-%d'), f'{date.strftime("%Y-%m-%d")} 23:59',
                          tz='europe/amsterdam', freq='1min')
        )
        S_today.index += 1

        df_['timestamp'] = df_['sequence_number'].map(S_today.to_dict())

        return df_

    return df.groupby('date').apply(group_func).reset_index(drop=True).set_index('timestamp').drop(columns=['date', 'time'])
