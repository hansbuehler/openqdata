# Synthetic offline inputs

`synthetic_widb.py` constructs WIDB-shaped markets from fixed invented parameters and an independent Black–Scholes formula using SciPy's normal CDF. It reads no licensed observations. Dates and ticker names exercise calendar and cache conventions. Above-IV-ceiling quotes and a butterfly-arbitrage expiry exercise rejection.

`synthetic_massive.py` constructs endpoint payloads, quotes, trades, bars and contracts from fixed invented values. Tests run real conversions, filtering, alignment, aggregation, adjustment factors and contract rejection. No downloaded provider responses are retained.

`processed/fred/rates.csv` and `processed/yahoo/prices.csv` are small synthetic transformation inputs. All other caches and model round trips are written only beneath pytest's temporary output directory.
