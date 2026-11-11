# openqdata.massive

Massive market-data client, quote/trade processing, option contracts and ticker histories.

```python
from openqdata.massive import MassiveClient
client = MassiveClient()
```

MASSIVE_TOKEN. Data paths come from `openqdata.env`: `OQ_DATA_ROOT`, `OQ_DATA_RAW`, and `OQ_DATA_PROCESSED`.

Set `OQ_DATA_TEST_MODE=1` and `OQ_DATA_TEST_ROOT` to an existing fixture root to read local caches without provider access.

- `__init__.py`: Massive.com Data Module. Public entry points: package exports.
- `client.py`: openqdata.massive.client. Public entry points: `MassiveClient`.
- `expiries.py`: openqdata.massive.expiries. Public entry points: `classify_expiry`, `ticker_expiries_day`, `ticker_expiries`.
- `processing.py`: openqdata.massive.processing. Public entry points: `filter_valid_trades`, `filter_valid_quotes`, `TradeQuoteAlignmentConfig`, `align_quotes_to_trades`, `align_trades_to_quotes`.
- `trade_conds.py`: openqdata.massive.trade_conds. Public entry points: `ConditionCode`, `ConditionFlag`, `pack_conditions`.

Processing modules provide `python -m openqdata.<source>.<module> --help`. New adapters accept a function name and `--params` containing JSON keyword arguments. Existing specialized commands retain their own options.

## Trade-condition defaults

`filter_valid_trades()` excludes closing prints (IDs 8 and 19), official closes
(15), and corrected consolidated closes (38), as well as opening prints/official
opens, crosses, contingent trades and the other `NORMAL_TRADE_EXCLUDE_FLAGS`.
Both alignment functions inherit this filter. `within_session=False` changes
only the time window; closing conditions remain excluded. Odd lots remain included.

`MassiveClient.fetch_trades()` retains raw condition records.
`build_unadjusted_trades()` filters session timestamps only, and
`build_1s_trade_bars()` uses that stream by default, including closing prints.
Pass `trades=filter_valid_trades(ticker, d)` to the bar builder to exclude them.

## Original module documentation

# [Massive](http://www.massive.com) Data Access

This directory contains Ivy DB data processing in the following files:

* [client.py](client.py) provides the ``MassiveClient`` class which wraps various minutae of downloading data from massive (e.g. paging). This class has self-explanatory functions such
  as ``fetch_trades``, ``fetch_quotes``, ``fetch_bars`` and a few others; see documentation.
  This functionality is basically raw access to data. It provides very little processing, except that it packs trade-condition IDs into a ``trade_code`` per row.

  It is recommended that you use [processing.py](processing.py) ``filter_valid_trades`` instead of the raw ``fetch_trades`` to obtain trades.
  The former applies a few standard trade filters.

* [options/contracts.py](options/contracts.py) gives access to all option contracts listed for a given ticker on a given date.

## Data Access

To access this data:

  1. Make sure you configure the python environment for **openqdata** following [the introduction](../../../README.md) which means to set at
  least the ``OQ_DATA_ROOT`` environment variable.
  [See the configuration guide for data locations](../../../docs/configuration.md).

  2. Ensure you have an account and test it. The [Massive quickstart](https://massive.com/docs/rest/quickstart) contains some helpful information.

  3. Set the ``MASSIVE_TOKEN`` environment variable to your API token.

  4. Try the code:

      ```python
      from datetime import date
      from openqdata.massive import MassiveClient
      client = MassiveClient()
      adj_bars = client.fetch_bars("AAPL", date(2020,1,1), date(2020,1,15), adjusted=False, timespan="second")
      print(adj_bars)
      ```
  5. The notebook [``notebooks/viz_trades_quotes.ipynb``](notebooks/viz_trades_quotes.ipynb) shows how to download trades and quotes by tick.

### Option Contracts

Options are just tickers for Massive.
In order to retrieve the option tickers for listed options of a given underlying ticker on a given date, use ``openqdata/massive/options/contracts.py``.



```python
  from datetime import date
  from openqdata.massive.options.contracts import (
    Context,
    ContractsFilter,
    DateRange,
    PoolConfig,
    filter_contracts_between,
   )

  date_range = DateRange(start=date(2024, 1, 1), end=date(2024, 1, 15), exclude_half_days=True)
    pool_config = PoolConfig(num_workers=8, threading=False)
    contracts_filter = ContractsFilter(max_dte=25, max_mns=3.0, min_opt_vol_k=1)

  contracts = filter_contracts_between(
        "SPY",
        date_range,
        contracts_filter=contracts_filter,
        refresh=False,
        pool_config=pool_config,
        verbose=Context.all,
    )
```

The ``ContractsFilter`` filter offers the following filters:

* ``max_dte``: maximum days to expiry in business days.
* ``max_mns``: maximum normalized strike, i.e.
   $$
   \left| 10\, \log\left(\frac{K}{S_{prev}}\right)   \sqrt{\frac{1+e}{T+e}} \right| \approx \left| \log\left(\frac{K}{S_{prev}}\right) \frac1{ 0.1\sqrt{T}} \right|
   $$, where $S_prev$ is the previous close adjusted for stock splits and dividends to match todays unadjusted price, and T is time to expiry in years. This is a measure of moneyness that accounts for both distance to the money and time to expiry.
* ``min_opt_vol_k``: Minimum volume trades the previous day, in 1000 USD.

