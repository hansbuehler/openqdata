# Massive

`openqdata.massive` wraps the [Massive](https://massive.com) REST API for stock and option trades, quotes, bars, contracts and corporate actions.

```python
from datetime import date
from openqdata.massive import MassiveClient

client = MassiveClient()
bars = client.fetch_bars("AAPL", date(2020, 1, 1), date(2020, 1, 15), adjusted=False, timespan="second")
```

## Access

1. [Configure the storage locations](../getting-started.md#storage-locations).
2. Create an account. The [Massive quickstart](https://massive.com/docs/rest/quickstart) explains API tokens.
3. Set `MASSIVE_TOKEN` to your token.
4. Run [`notebooks/viz_trades_quotes.ipynb`](../../src/openqdata/massive/notebooks/viz_trades_quotes.ipynb) to check access.

`MassiveClient("work")` adds an optional in-session cache below `processed`. It is meant to speed up an interactive session, not to store data long term.

## Client and endpoints

`MassiveClient` handles paging, retries on transient HTTP errors and caching. It returns raw observations; the only transformation is that trade-condition IDs are packed into a `trade_code` per row.

| Endpoint | Entry points |
|---|---|
| `/v3/trades/{ticker}` | `fetch_trades`, trade-availability helpers |
| `/v3/quotes/{ticker}` | `fetch_quotes`, quote-availability helpers |
| `/v2/aggs/ticker/{ticker}/range/1/{timespan}/{start}/{end}` | `fetch_bars`, `adjustment_factors` |
| `/v1/open-close/{ticker}/{date}` | `fetch_day_summary`, `consistent_prev_close` |
| `/v3/reference/options/contracts` | Contract lists, expiry discovery |
| `/v3/reference/options/contracts/{ticker}` | `option_contract_overview` |
| `/v3/reference/tickers/{ticker}` | `ticker_reference_data` |
| `/stocks/v1/dividends`, `/stocks/v1/splits` | `get_dividends`, `get_splits` |
| `/vX/reference/tickers/{ticker}/events` | `has_ticker_changes`, through the Massive SDK |

The table covers the endpoints this package uses, not Massive's full product. Expired contracts are requested with `as_of`. Option quotes and trades start on 2022-03-07 (`MassiveClient.START_DATE`).

## Trades, quotes and conditions

Use `openqdata.massive.processing.filter_valid_trades` rather than the raw `fetch_trades`. It removes trades with these conditions:

- opening prints and official opens;
- closing prints (condition IDs **8** and **19**), official closes (**15**) and corrected consolidated closes (**38**);
- crosses, contingent trades and the other `NORMAL_TRADE_EXCLUDE_FLAGS`.

Odd lots are kept. Passing `within_session=False` changes only the time window; closing conditions are still removed.

| Function | Closing-condition records |
|---|---|
| `MassiveClient.fetch_trades()` | Kept; condition IDs packed into `trade_code` |
| `filter_valid_trades()` | Removed |
| `align_quotes_to_trades()` / `align_trades_to_quotes()` | Removed, through `filter_valid_trades()` |
| `tickers.data.build_unadjusted_trades()` | Kept; only session timestamps are filtered |
| `tickers.data.build_1s_trade_bars()` | Kept by default |

To build bars from the filtered stream:

```python
from openqdata.massive.processing import filter_valid_trades
from openqdata.massive.tickers.data import build_1s_trade_bars

bars = build_1s_trade_bars(ticker, d, trades=filter_valid_trades(ticker, d))
```

## Option contracts

For Massive, options are tickers. `openqdata.massive.options.contracts` lists and filters the contracts available for an underlying on a given date:

```python
from datetime import date
from openqdata.biz_calendar import DateRange
from openqdata.pool import PoolConfig
from openqdata.massive.options.contracts import ContractsFilter, filter_contracts_between

contracts = filter_contracts_between(
    "SPY",
    DateRange(start=date(2024, 1, 2), end=date(2024, 1, 12), exclude_half_days=True),
    contracts_filter=ContractsFilter(max_dte=25, max_mns=3.0, min_opt_vol_k=1),
    pool_config=PoolConfig(num_workers=8, threading=False),
)
```

| Filter | Meaning |
|---|---|
| `max_dte` | Maximum business days to expiry. |
| `max_mns` | Maximum absolute normalized strike, $\lvert \log(K/S_\mathrm{prev}) \rvert / (0.1\sqrt{T})$ with five-day regularization. $S_\mathrm{prev}$ is the previous close adjusted to today's unadjusted price. |
| `min_opt_vol_k` | Minimum previous-day cash volume, in thousands of USD. |

[`notebooks/download_options_quotes_trades.ipynb`](../../src/openqdata/massive/options/notebooks/download_options_quotes_trades.ipynb) walks through a complete example: it selects one underlying and date, filters the contracts, and downloads quotes and trades for every selected contract.

`openqdata.massive.tickers` builds ticker-level series: unadjusted trades, weighted mids, one-second bars, listing dates and filtered histories. `openqdata.massive.expiries` classifies listed expiries.
