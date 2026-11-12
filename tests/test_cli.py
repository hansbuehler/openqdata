import sys

import pytest

from openqdata.cli import run_module


def _run(monkeypatch, function, arguments):
    monkeypatch.setattr(sys, "argv", ["example", *arguments])
    run_module({"__name__": function.__module__, function.__name__: function})


def test_cli_accepts_json_and_prints_result(monkeypatch, capsys):
    def add(left: int, right: int) -> int:
        return left + right
    _run(monkeypatch, add, ["add", "--params", '{"left": 2, "right": 3}'])
    assert capsys.readouterr().out.strip() == "5"


def test_cli_rejects_non_object_arguments(monkeypatch):
    def example():
        raise AssertionError("Must validate parameters before execution")
    with pytest.raises(SystemExit) as result:
        _run(monkeypatch, example, ["example", "--params", "[]"])
    assert result.value.code == 2


def test_cli_refuses_output_inside_checkout(monkeypatch):
    from pathlib import Path
    def example():
        raise AssertionError("Must validate output before execution")
    with pytest.raises(SystemExit) as result:
        _run(monkeypatch, example, ["example", "--output", str(Path(__file__).parents[1] / "output.json")])
    assert result.value.code == 2


@pytest.mark.parametrize("module", ["openqdata.fred.client", "openqdata.massive.client", "openqdata.widb.client"])
def test_cli_does_not_expose_credential_helpers(monkeypatch, capsys, module):
    import importlib
    namespace = vars(importlib.import_module(module))
    monkeypatch.setattr(sys, "argv", ["example", "--help"])
    with pytest.raises(SystemExit):
        run_module(namespace)
    listed = capsys.readouterr().out
    for helper in ("api_key", "get_token", "credentials", "connect"):
        assert f"Client.{helper}" not in listed
