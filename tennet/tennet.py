import requests
from enum import Enum
import pandas as pd
from io import StringIO
from typing import Union

__title__ = "tennet-py"
__version__ = "0.1.0"
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

    def query_df(self, data_type: DataType, d_from: Union[str, pd.Timestamp], d_to: Union[str, pd.Timestamp]):
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
