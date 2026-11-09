"""Invented provider payloads for offline conversion and pipeline tests."""
from __future__ import annotations

from datetime import date, datetime, time
from urllib.parse import urlsplit

import numpy as np
import polars as pl
import requests

from quantdata.biz_calendar import TZ_NY, session_open_close
from quantdata.massive import MassiveClient


def trades(day: date, count: int = 1000) -> pl.DataFrame:
    start, _, _ = session_open_close(day)
    ns = int(start.timestamp()) * 10**9 + np.arange(count) * 100_000_000
    return pl.DataFrame(dict(ts_ns=ns, price=np.full(count, 101.), size=np.full(count, 2.),
                             trade_code=np.zeros(count), sequence_number=np.arange(count)),
                        schema=MassiveClient.SCHEMA_TRADES)


def quotes(day: date) -> pl.DataFrame:
    result = trades(day)
    return result.select('ts_ns', pl.lit(100.).alias('bid_price'), pl.lit(10.).alias('bid_size'),
                         pl.lit(102.).alias('ask_price'), pl.lit(20.).alias('ask_size'),
                         'sequence_number').cast(MassiveClient.SCHEMA_QUOTES)


def contract(ticker: str = 'O:SPY240102C00475000', *, expiry: str = '2024-01-02', strike: float = 100.) -> dict:
    return dict(cfi='OCASPS', contract_type='call', exercise_style='american',
                expiration_date=expiry, primary_exchange='TEST', shares_per_contract=100,
                strike_price=strike, ticker=ticker, underlying_ticker='SPY')


def request(url: str, params: dict | None = None) -> dict:
    """Respond only to supported endpoint families, without reading any files."""
    path = urlsplit(url).path
    params = params or {}
    if path.startswith(('/v3/trades/', '/v3/quotes/')):
        day = date.fromisoformat(str(params['timestamp']))
        start, _, _ = session_open_close(day)
        ns = int(start.timestamp()) * 10**9
        option = '/O:' in path
        if '/trades/' in path:
            return {'results': [dict(price=.5 if option else 101., size=2., sequence_number=1,
                                     sip_timestamp=ns, conditions=[])]}
        return {'results': [dict(bid_price=.49 if option else 100., ask_price=.51 if option else 102.,
                                 bid_size=10., ask_size=20., sequence_number=1, sip_timestamp=ns)]}
    if path.startswith('/v2/aggs/ticker/'):
        start, end = [date.fromisoformat(x) for x in path.split('/')[-2:]]
        results = []
        for day in [d for d in np.arange(np.datetime64(start), np.datetime64(end) + np.timedelta64(1, 'D')).astype(date) if d.weekday() < 5]:
            ns = int(datetime.combine(day, time(12), TZ_NY).timestamp() * 1000)
            adjusted = str(params.get('adjusted', 'false')).lower() == 'true'
            scale = .25 if adjusted and '/AAPL/' in path and day < date(2020, 8, 31) else 1.
            results.append(dict(t=ns, o=101.*scale, h=104.*scale, l=100.*scale, c=103.*scale,
                                v=123456., vw=102.*scale, n=2345))
        return {'results': results}
    if path.startswith('/v1/open-close/'):
        day = path.rsplit('/', 1)[-1]
        if day == '2024-01-06':
            response = requests.Response()
            response.status_code = 404
            raise requests.HTTPError(response=response)
        return dict(open=101., close=103., high=104., low=100., volume=123456.)
    if path.startswith('/v3/reference/tickers/'):
        return {'results': dict(active=True, list_date='1990-01-02', ticker=path.rsplit('/', 1)[-1])}
    if path.startswith('/vX/reference/tickers/'):
        return {'results': {'events': []}}
    if path.startswith('/v3/reference/options/contracts/'):
        return {'results': contract(path.rsplit('/', 1)[-1])}
    if path == '/v3/reference/options/contracts':
        expiry = str(params.get('expiration_date', params.get('expiration_date.gte', '2024-01-02')))
        return {'results': [contract(expiry=expiry)]}
    if path == '/stocks/v1/dividends':
        return {'results': [dict(ticker='SPY', ex_dividend_date='2023-12-15', cash_amount=1.,
                                 split_adjusted_cash_amount=1., historical_adjustment_factor=1.)]}
    if path == '/stocks/v1/splits':
        return {'results': [dict(ticker='AAPL', execution_date='2020-08-31', split_from=1., split_to=4.,
                                 historical_adjustment_factor=.25)]}
    raise AssertionError(f'Unexpected synthetic endpoint: {path} {params}')


def responses() -> dict:
    """Two synthetic pagination pages and normal/closing-condition trade payloads."""
    pages = [{'results': [contract('SYNTHETIC-A')],
              'next_url': MassiveClient.BASE_URL + '/v3/reference/options/contracts?cursor=synthetic'},
             {'results': [contract('SYNTHETIC-B')]}]
    normal = request('/v3/trades/KWR', {'timestamp': '2024-01-02'})['results'][0]
    closing = dict(normal, conditions=[15], sequence_number=2, sip_timestamp=normal['sip_timestamp'] + 10**9)
    return dict(pagination_pages=pages, closing_trade_sample=[normal, closing])
