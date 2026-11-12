# openqdata.widb

WRDS OptionMetrics IvyDB connector (`WIDBClient`) and the WIDB benchmark pipeline, which produces cleaned option data with an arbitrage-free interpolation: `day` (cleaning and enrichment), `arbfree` (linear fits), `options_filter` (eligible options), `sanos` (selected SANOS fits) and `timeseries` (packing).

Documentation: [connectors/widb.md](https://github.com/hansbuehler/openqdata/blob/main/docs/connectors/widb.md)
