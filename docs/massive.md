# Massive API coverage and trade defaults

Set `MASSIVE_TOKEN` and an external `OQ_DATA_ROOT` before importing `oqdata`.

## Supported endpoint families

The live validation on 27 October 2026 passed all 43 checks with fresh provider
requests, including pagination, every supported aggregate timespan, adjusted and
unadjusted summaries, stocks/options observations and higher-level processing.

| Endpoint | Package entry points |
| --- | --- |
| `/v3/trades/{ticker}` | `fetch_trades`, trade-availability helpers |
| `/v3/quotes/{ticker}` | `fetch_quotes`, quote-availability helpers |
| `/v2/aggs/ticker/{ticker}/range/1/{timespan}/{start}/{end}` | `fetch_bars`, `adjustment_factors` |
| `/v1/open-close/{ticker}/{date}` | `fetch_day_summary`, `consistent_prev_close` |
| `/v3/reference/options/contracts` | Contract-list methods, expiry discovery |
| `/v3/reference/options/contracts/{ticker}` | `option_contract_overview` |
| `/v3/reference/tickers/{ticker}` | `ticker_reference_data` |
| `/stocks/v1/dividends` | `get_dividends` |
| `/stocks/v1/splits` | `get_splits` |
| `/vX/reference/tickers/{ticker}/events` | `has_ticker_changes`, through the Massive SDK |

This covers the endpoints used by this package, rather than every endpoint in
Massive's broader product. The latest overview is tested with an active option;
historical expired contracts are requested with `as_of`.

The sweep exposed and fixed option symbols being rejected in bar-cache paths,
nonempty split-response date parsing, and bar timestamps not retaining their
declared millisecond dtype. Small real responses are retained for offline tests.

The live report is kept with the external run outputs, outside Git.

## Closing-trade handling

| Function | Closing-condition records |
| --- | --- |
| `MassiveClient.fetch_trades()` | Retained; condition IDs are packed into `trade_code` |
| `filter_valid_trades()` | Excluded through `NORMAL_TRADE_EXCLUDE_FLAGS` |
| `align_quotes_to_trades()` / `align_trades_to_quotes()` | Excluded through `filter_valid_trades()` |
| `build_unadjusted_trades()` | Retained; only session timestamps are filtered |
| `build_1s_trade_bars()` | Retained by default, using `build_unadjusted_trades()` |

The condition filter removes closing prints (IDs **8 and 19**), official closes
(**15**) and corrected consolidated closes (**38**), alongside opening prints and
other excluded conditions. **`within_session=False` does not restore closing
records:** it changes only the session-time restriction. Odd lots are retained.
A trade is not excluded merely because its timestamp is at the close; its
condition flags determine this exclusion.

To construct bars from the condition-filtered stream:

```python
from oqdata.massive.processing import filter_valid_trades
from oqdata.massive.tickers.data import build_1s_trade_bars

trades = filter_valid_trades(ticker, d)
bars = build_1s_trade_bars(ticker, d, trades=trades)
```
