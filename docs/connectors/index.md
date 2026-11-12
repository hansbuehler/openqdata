# Data connectors

Each data source is a subpackage with a `Client` class. They all follow the same pattern:

| Element | Convention |
|---|---|
| Authentication | Read lazily from the provider's own environment variable by a static helper (`credentials()`, `get_token()`, `api_key()`). It is called only when the client first needs network access. |
| Live-access guard | Every network entry point calls `env.require_live(...)`. It refuses to run in [test mode](../caching.md#test-mode). |
| Storage | `Client.locations` gives the source's `raw` and `processed` subdirectories below the configured roots. |
| Caching | Fetch and processing methods are cached and versioned by scope and configuration. See [caching](../caching.md). |
| Commands | Public client methods are available as `python -m openqdata.<source>.client Client.method --params '{...}'`. Credential helpers are never exposed. |

| Source | Client | Data | Credentials |
|---|---|---|---|
| [WIDB](widb.md) | `openqdata.widb.WIDBClient` | WRDS OptionMetrics IvyDB: option quotes, spot, forwards, zero curves | `WRDS_USERNAME`, `.pgpass` |
| [Massive](massive.md) | `openqdata.massive.MassiveClient` | Stock and option trades, quotes, bars, contracts, corporate actions | `MASSIVE_TOKEN` |
| [Yahoo Finance](yahoo.md) | `openqdata.yahoo.YFClient` | Price history, dividends, earnings dates | none |
| [FRED](fred.md) | `openqdata.fred.FREDClient` | SOFR, EFFR and short Treasury rates | `FRED_API_KEY` |
| [Cboe VIX](vixdata.md) | `openqdata.vixdata.CboeClient` | Official daily VIX history; discrete VIX formula | none |

Some modules derive data from these connectors:

- **Ticker calendars.** `openqdata.tickers` combines Massive and Yahoo data into standard expiries, dividend and split flags, and earnings dates. See `build_ticker_calendar`.
- **Business-day calendar.** `openqdata.biz_calendar` provides NYSE business days, half days and the `NMS5` normalized moneyness. All connectors use it.
