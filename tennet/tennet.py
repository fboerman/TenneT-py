import requests
from enum import Enum
import pandas as pd
from io import StringIO
from typing import Union

__title__ = "tennet-py"
__version__ = "0.2.1"
__author__ = "Frank Boerman"
__license__ = "MIT"


class DataType(Enum):
    measurementdata = "Measurement data"
    settlementprices = "Imbalance price"
    balansdeltaprices = "Balance delta with prices"
    availablecapacity = "Available capacity"


class OutputType(Enum):
    CSV = "csv"
    XML = "xml"


## documentation of endpoints: https://www.tennet.org/english/operational_management/export_data_explanation.aspx

class TenneTClient:
    BASE_URL = "https://www.tennet.org/english/operational_management/export_data.aspx?exporttype={data_type}" \
               "&format={output_type}&datefrom={d_from}&dateto={d_to}&submit=1"

    DATEFORMAT = '%m/%d/%Y %H:%M'

    def __init__(self, default_output: OutputType = OutputType.CSV):
        self.default_output = default_output
        self.s = requests.Session()
        self.s.headers.update({
            'user-agent': 'tennet-py (github.com/fboerman/TenneT-py)'
        })

    def base_request(self, data_type: DataType, d_from: Union[str, pd.Timestamp], d_to: Union[str, pd.Timestamp],
                      output_type: OutputType = None) -> str:
        if output_type is None:
            output_type = self.default_output
        if type(d_from) == str:
            d_from = pd.Timestamp(d_from)
        if type(d_to) == str:
            d_to = pd.Timestamp(d_to)

        r = self.s.get(self.BASE_URL.format(data_type=data_type.name, output_type=output_type.name.lower(),
                                            d_from=d_from.strftime("%d-%m-%Y"), d_to=d_to.strftime("%d-%m-%Y")))
        r.raise_for_status()
        return r.text

    def query_df(self, data_type: DataType, d_from: Union[str, pd.Timestamp], d_to: Union[str, pd.Timestamp]) -> pd.DataFrame:
        stream = StringIO(self.base_request(data_type, d_from, d_to, output_type=OutputType.CSV))
        stream.seek(0)
        df = pd.read_csv(stream, sep=',')
        df.fillna(0, inplace=True)

        if data_type == DataType.settlementprices or data_type == DataType.measurementdata or \
            data_type == DataType.availablecapacity:
            df['period_from'] = df['Date'] + ' ' + df['period_from']
            df['period_from'] = pd.to_datetime(df['period_from'], format=self.DATEFORMAT)
            df['period_until'] = df['Date'] + ' ' + df['period_until']
            df['period_until'] = pd.to_datetime(df['period_until'], format=self.DATEFORMAT)
            df.drop(columns=['Date', 'PTE'], inplace=True)
        elif data_type == DataType.balansdeltaprices:
            df.rename(columns={'Time': 'timestamp'}, inplace=True)
            df['timestamp'] = df['Date'] + ' ' + df['timestamp']
            df['timestamp'] = pd.to_datetime(df['timestamp'], format=self.DATEFORMAT)
            df.drop(columns=['Date', 'Sequence_number'], inplace=True)

        return df

    def query_curent_imbalance(self) -> pd.DataFrame:
        # structure is clear enough for pandas to pick it up, use build in http support as well
        df = pd.read_xml('https://www.tennet.org/xml/balancedelta2017/balans-delta.xml') \
            .drop(columns=['NUMBER', 'RESERVE_UPWARD_DISPATCH', 'RESERVE_DOWNWARD_DISPATCH', 'TIME'])\
            .rename(columns=lambda x: x.lower())
        S = {}
        h = '23'
        if pd.Timestamp.now(tz='europe/amsterdam').hour == 0:
            # we are in the first hour of the day so overlap with yesterday
            yesterday = (pd.Timestamp.now(tz='europe/amsterdam') - pd.Timedelta(days=1)).strftime("%Y-%m-%d")
            S_yesterday = pd.Series(
                data=pd.date_range(yesterday, f'{yesterday} 23:59', tz='europe/amsterdam', freq='1min')
            )
            S_yesterday.index += 1
            S = S_yesterday[S_yesterday.dt.hour>=23].to_dict()
            h = '01'

        today = pd.Timestamp.now(tz='europe/amsterdam').strftime("%Y-%m-%d")
        S_today = pd.Series(
            data=pd.date_range(today, f'{today} {h}:59', tz='europe/amsterdam', freq='1min')
        )
        S_today.index += 1
        S = S | S_today.to_dict()
        df['timestamp'] = df['sequence_number'].map(S)
        df = df.set_index('timestamp').sort_index()
        df = df.rename(columns={
            'incident_reserve_up_indicator': 'up_indicator',
            'incident_reserve_down_indicator': 'down_indicator'
        })
        df['up_indicator'] = df['up_indicator'].astype(bool)
        df['down_indicator'] = df['down_indicator'].astype(bool)
        return df

    def query_imbalance_settlement(self, date: pd.Timestamp) -> pd.DataFrame:
        #UI: https://www.tennet.org/bedrijfsvoering/Systeemgegevens_afhandeling/verrekenprijzen/index.aspx
        r = self.s.get(f'https://www.tennet.org/xml/imbalanceprice/{date.strftime("%Y%m%d")}.xml')
        r.raise_for_status()
        df = pd.read_xml(StringIO(r.text))[['TAKE_FROM_SYSTEM', 'FEED_INTO_SYSTEM', 'REGULATION_STATE']]\
        .rename(columns={
            'TAKE_FROM_SYSTEM': 'price_feedout',
            'FEED_INTO_SYSTEM': 'price_feedin',
            'REGULATION_STATE': 'state'
        })
        df.index = pd.date_range(date.strftime("%Y-%m-%d"), f'{date.strftime("%Y-%m-%d")} 23:59', tz='europe/amsterdam', freq='15min')

        return df