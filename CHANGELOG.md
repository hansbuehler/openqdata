# Changelog

## 0.2.0

First public release of openqdata.

- Storage and caching: two configured locations, `raw` and `processed`; versioned caches keyed by scope and configuration; an offline test mode.
- Connectors, each with a `Client` class: WRDS OptionMetrics IvyDB (`WIDBClient`), Massive (`MassiveClient`), Yahoo Finance (`YFClient`), FRED (`FREDClient`) and Cboe VIX (`CboeClient`).
- WIDB benchmark data: cleaned daily option quotes with an arbitrage-free SANOS interpolation (`openqdata.widb.sanos.fit_sanos_day`).
- The `arbfree` toolkit for linear (DLV) and SANOS arbitrage-free option surfaces.
- Namespaces for extension packages: `openqdata.models` and `openqdata.benchmark`.
