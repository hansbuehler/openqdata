# Cboe VIX

`openqdata.vixdata` provides two things:

- the official Cboe daily VIX history, as an independent market-level benchmark for 30-day S&P 500 implied variance;
- Cboe's discrete-strike VIX formula.

The VIX history is not option-quote data, and it does not replace an option surface.

```python
from openqdata.vixdata import CboeClient

client = CboeClient()
vix = client.load_vix("2025-01-01", "2025-02-01")   # inclusive
client.refresh_vix()                                # re-download the full history
```

## Dataset

**Source:** Cboe's public [`VIX_History.csv`](https://cdn.cboe.com/api/global/us_indices/daily_prices/VIX_History.csv). No credentials are needed. `load_vix` downloads the file once if no cache exists, and reads the cache after that.

**Schema:** `date` (`Date`), and `open`, `high`, `low`, `close` (`Float64`), in annualized implied-volatility percentage points. `close` is the official end-of-day level.

**Storage:** the data is under the `vixdata` raw location (`env.locations("vixdata").raw`) as `cboe/vix_eod`. Next to it, `cboe/vix_eod_metadata` records the source URL, the UTC retrieval time, the observation count, the date range and the units.

**Validation:**
- The source schema must match, and levels must be positive and unique per date.
- Some early Cboe rows have intraday high/low values that don't bracket the open or close. The source columns are kept, and valid closing levels are retained.

## Formula

`openqdata.vixdata.formula` implements Cboe's model-free calculation:

- `select_vix_strip` infers the forward by put–call parity, then selects out-of-the-money strikes using the two-consecutive-zero-bid cutoff.
- `discrete_total_variance` computes the variance for one expiry.
- `constant_maturity_vix` interpolates to 30 days.
