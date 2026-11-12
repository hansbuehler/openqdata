# Yahoo Finance

`openqdata.yahoo` uses [yfinance](https://ranaroussi.github.io/yfinance/) for price history, dividends and earnings dates. No credentials are needed. Coverage is intentionally small.

```python
from datetime import date
from openqdata.yahoo import YFClient

earnings = YFClient().has_earnings("AAPL", date(2024, 1, 1), date(2024, 12, 31))
```

`YFConnectionConfig` controls retries and timeouts. Inconsistent or insufficient responses raise `DataError`, which carries the request context. Run [`notebooks/viz_history.ipynb`](../../src/openqdata/yahoo/notebooks/viz_history.ipynb) to check access.
