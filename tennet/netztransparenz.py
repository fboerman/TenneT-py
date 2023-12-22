import requests
import pandas as pd
from io import BytesIO


class NetztransparenzClient:
    ACCESS_TOKEN_URL = "https://identity.netztransparenz.de/users/connect/token"
    BASE_URL = "https://ds.netztransparenz.de/api/v1/data/"

    def __init__(self, client_token: str, secret_token: str):
        self.client_token = client_token
        self.secret_token = secret_token
        self.access_token = ""
        self.s = requests.Session()
        self.s.headers.update({
            'user-agent': 'tennet-py (github.com/fboerman/TenneT-py)'
        })
        self.login()

    def login(self):
        r = self.s.post(self.ACCESS_TOKEN_URL,
                        data={
                            'grant_type': 'client_credentials',
                            'client_id': self.client_token,
                            'client_secret': self.secret_token
                        })
        r.raise_for_status()
        self.access_token = r.json()['access_token']
        self.s.headers.update({
            'Authorization': 'Bearer {}'.format(self.access_token)
        })

    def _base_request(self, url: str) -> str:
        r = self.s.get(self.BASE_URL + url)
        if r.status_code == 401:
            self.login()
            r = self.s.get(url)

        r.raise_for_status()
        return r.text

    def query_imbalance(self, start: pd.Timestamp, end: pd.Timestamp) -> pd.DataFrame:
        if start.tzinfo is None or end.tzinfo is None:
            raise Exception('Please use a timezoned pandas object for start and end')
        text = self._base_request(
            url=f'NrvSaldo/AktivierteSRL/Betrieblich/{start.tz_convert("UTC").strftime("%Y-%m-%dT%H:%M:%S")}'
                f'/{end.tz_convert("UTC").strftime("%Y-%m-%dT%H:%M:%S")}/'
        )

        df = pd.read_csv(BytesIO(text.encode('utf-8')), sep=';').drop(columns=['Datenkategorie', 'Datentyp', 'Einheit', 'Zeitzone'])
        df['mtu'] = pd.to_datetime(df['Datum'] + df['von'], format='%d.%m.%Y%H:%M').dt.tz_localize('UTC').dt.tz_convert('europe/amsterdam')

        df = df.set_index('mtu').drop(columns=['Datum', 'von', 'bis']).sort_index().replace('N.A.', None)
        for c in df:
            # fix decimal point (grr why is this not the same worldwide)
            df[c] = df[c].str.replace(',', '.').astype(float)

        # dropna because those are incomplete lines with N.A.
        # if data is zero a proper zero will be inserted by the api so nan is really incomplete
        return df.dropna()\
            .rename(columns=lambda c: c.replace('(Positiv)', '_up')\
                    .replace('(Negativ)', '_down').replace('TSO', '')\
                    .replace(' ', ''))
