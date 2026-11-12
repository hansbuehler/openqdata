"""Shared command line adapter for public data-processing functions."""
from __future__ import annotations

import argparse
import inspect
import json
from datetime import date, datetime
from pathlib import Path
from typing import Any, get_type_hints


def run_module(namespace: dict[str, Any]) -> None:
    """Expose locally defined public functions using JSON keyword arguments.

    Run ``python -m openqdata.<source>.<module> --help`` to list functions.
    Output defaults to stdout; use --output with an external data-root path.
    """
    functions = {
        name: value for name, value in namespace.items()
        if not name.startswith("_") and inspect.isfunction(value)
        and value.__module__ == namespace.get("__name__")
    }
    clients = {
        name: value for name, value in namespace.items()
        if inspect.isclass(value) and name.endswith("Client")
        and value.__module__ == namespace.get("__name__")
    }
    methods = {
        f"{name}.{method}": (client, method)
        for name, client in clients.items()
        for method, value in inspect.getmembers(client)
        if callable(value) and not method.startswith("_")
        and method not in {"get_token", "api_key", "credentials", "connect", "rest_client", "http_session"}
    }
    parser = argparse.ArgumentParser(description=namespace.get("__doc__"))
    parser.add_argument("function", choices=sorted(set(functions) | set(methods)))
    parser.add_argument("--params", default="{}", help="JSON object of keyword arguments; dates use YYYY-MM-DD")
    parser.add_argument("--init-params", default="{}", help="JSON constructor arguments for Client.method commands")
    parser.add_argument("--output", type=Path, help="Output path outside the source checkout (.parquet, .csv or .json)")
    args = parser.parse_args()
    try:
        if args.function in methods:
            client, method = methods[args.function]
            constructor = json.loads(args.init_params)
            if not isinstance(constructor, dict):
                raise ValueError("--init-params must contain a JSON object")
            function = getattr(client(**constructor), method)
        else:
            function = functions[args.function]
        params = json.loads(args.params)
        if not isinstance(params, dict):
            raise ValueError("--params must contain a JSON object")
        signature = inspect.signature(function)
        try:
            hints = get_type_hints(function)
        except (NameError, TypeError):
            # Some APIs use descriptive, non-runtime annotations.
            hints = {}
        for key, value in params.items():
            annotation = hints.get(key)
            if annotation is date and isinstance(value, str):
                params[key] = date.fromisoformat(value)
            elif annotation is datetime and isinstance(value, str):
                params[key] = datetime.fromisoformat(value)
        signature.bind(**params)
        if args.output:
            output = args.output.expanduser().resolve()
            repository = Path(__file__).resolve().parents[2]
            if output.is_relative_to(repository):
                raise ValueError("Store generated output outside the Git checkout")
            if output.suffix not in {".parquet", ".csv", ".json"}:
                raise ValueError("Output must end in .parquet, .csv or .json")
        result = function(**params)
        if not args.output:
            print(result)
            return
        output.parent.mkdir(parents=True, exist_ok=True)
        if output.suffix == ".parquet":
            writer = getattr(result, "write_parquet", None) or getattr(result, "to_parquet", None)
            if writer is None:
                raise ValueError("This result does not support Parquet output")
            writer(output)
        elif output.suffix == ".csv":
            writer = getattr(result, "write_csv", None) or getattr(result, "to_csv", None)
            if writer is None:
                raise ValueError("This result does not support CSV output")
            writer(output)
        else:
            output.write_text(json.dumps(result, default=str, indent=2) + "\n")
    except (ValueError, TypeError) as error:
        parser.error(str(error))
