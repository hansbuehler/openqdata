import sys

import pytest

from quantdata.cli import run_module


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
