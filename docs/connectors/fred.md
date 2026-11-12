# FRED

`openqdata.fred` downloads short-term US rates from [FRED](https://fred.stlouisfed.org). Set `FRED_API_KEY` to a [FRED API key](https://fred.stlouisfed.org/docs/api/api_key.html).

```python
from openqdata.fred import FREDClient

client = FREDClient()
rates = client.load_rates("2024-01-02", "2024-03-28")      # cached
sofr = client.fetch_series("SOFR", start, end)             # one series, uncached
```

`load_rates` (also available as `openqdata.fred.load_fred_rates`) returns these columns:

- `date`;
- `sofr`, `effr`, `dgs1mo`, `dgs3mo` and `dgs6mo`, as `Float32` decimals (`0.05` means 5%);
- `on`, the overnight rate: SOFR when available, otherwise EFFR, otherwise the one-month Treasury rate.

Rows whose rates are all zero or missing are dropped, and the remaining columns are forward-filled.

FRED accepts the API key only as a URL parameter. openqdata removes it from request error messages.
