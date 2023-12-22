# TenneT-py
Python client for ingesting the TenneT System & transmission data API which can be found [here](https://www.tennet.org/english/operational_management/export_data_explanation.aspx).
It is a public API for which no API key is needed.

The library currently supports four data items:

* Measurement data
* Imbalance price
* Balance delta with prices
* Available capacity

Data can be retrieved as raw text or a Pandas DataFrame.

The client currently has two methods:
* ```base_request```: retrieves specified data in csv or xml text format
* ```query_df```: retrieves specified data and returnes a Pandas DataFrame

## Installation
```pip install tennet-py```

## Example Usages
```python
from tennet import TenneTClient, DataType, OutputType
import pandas as pd

start = pd.Timestamp("2021-01-01")
end = pd.Timestamp("2021-01-31")

# initiate the client, you can specify a default output to not always specify it per call
client = TenneTClient(default_output=OutputType.CSV)
# retrieve data as text in default output (in this case csv)
data = client.base_request(DataType.settlementprices, d_from=start, d_to=end)
# retrieve data as xml
data = client.base_request(DataType.settlementprices, d_from=start, d_to=end, output_type=OutputType.XML)

# retrieve same data as a dataframe
df = client.query_df(DataType.settlementprices, d_from=start, d_to=end)
```

## Netztransparenz
Also supported is a limited number of endpoints of the german TenneT from the Netztransparenz platform. First register and get oauth credentials as explained on the documentation page [here](https://www.netztransparenz.de/en/Web-API)
Then can be used as follows:
```python
from tennet import NetztransparenzClient
import pandas as pd

client = NetztransparenzClient(oauth_client_id, oauth_client_secret)
df = client.query_imbalance(start=pd.Timestamp('2023-12-22', tz='europe/amsterdam'), end=pd.Timestamp('2023-12-22 23:59', tz='europe/amsterdam'))
```

## Disclaimer
This is an unoffical package which is not supported or endorsed in any way by TenneT TSO.