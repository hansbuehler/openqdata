# Commands

Inspect module help before invoking a processing operation:

```sh
python -m oqdata.fred.rates --help
python -m oqdata.vixdata.cboe --help
python -m oqdata.massive.processing --help
python -m oqdata.widb.day --help
```

New adapters expose public functions with JSON keyword parameters:

```sh
python -m oqdata.fred.rates load_fred_rates --params '{"start":"2022-01-01","end":"2022-02-01"}' --output /data/oqdata/runs/example/rates.parquet
```

This example may download data outside test mode. Existing specialized CLIs retain their options. Function adapters accept simple scalar/list/dict JSON parameters and ISO dates for date-annotated arguments; construct complex filter/configuration dataclasses through Python imports. Numerical classes are Python APIs. Outputs belong outside Git working trees, in uniquely named run directories.

Client modules expose public methods as `Client.method` commands, for example:

```sh
python -m oqdata.yahoo.client --help
python -m oqdata.massive.client --help
python -m oqdata.widb.client --help
```

Supply method arguments with `--params`; optional constructor arguments use `--init-params`. Credential-returning helpers are excluded. Use the Python interface for rich configuration objects.
