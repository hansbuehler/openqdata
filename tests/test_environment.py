from __future__ import annotations

from dataclasses import fields
from pathlib import Path

import pytest

from openqdata import Environment, Locations


@pytest.fixture
def clean_settings(monkeypatch, tmp_path):
    for key in ["OQ_DATA_ROOT", "OQ_DATA_RAW", "OQ_DATA_PROCESSED", "OQ_DATA_CONFIG", "OQ_DATA_CACHE_MODE"]:
        monkeypatch.delenv(key, raising=False)
    monkeypatch.setenv("OQ_DATA_TEST_MODE", "0")
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "config"))
    monkeypatch.setattr(Path, "home", classmethod(lambda cls: tmp_path))
    return tmp_path


def test_locations_only_have_two_data_categories():
    assert [field.name for field in fields(Locations)] == ["raw", "processed"]


def test_defaults_do_not_create_storage(clean_settings):
    environment = Environment()
    assert Path(environment.locations.raw.path) == clean_settings / ".local/share/qdata/raw"
    assert Path(environment.locations.processed.path) == clean_settings / ".local/share/qdata/processed"
    assert not (clean_settings / ".local").exists()


@pytest.mark.parametrize("filename", ["openqdata.toml", "qdata.toml"])
def test_toml_relative_paths_and_environment_precedence(clean_settings, monkeypatch, filename):
    config = clean_settings / filename
    config.write_text('[data]\nroot="relative"\nraw="vendor"\n')
    monkeypatch.setenv("OQ_DATA_PROCESSED", str(clean_settings / "override"))
    environment = Environment()
    assert environment.config_file == config
    assert Path(environment.locations.raw.path) == clean_settings / "vendor"
    assert Path(environment.locations.processed.path) == clean_settings / "override"


def test_environment_root_overrides_config_root(clean_settings, monkeypatch):
    (clean_settings / "qdata.toml").write_text('[data]\nroot="config_root"\n')
    monkeypatch.setenv("OQ_DATA_ROOT", str(clean_settings / "env_root"))
    assert Path(Environment().locations.raw.path) == clean_settings / "env_root/raw"


def test_explicit_missing_config_is_an_error(clean_settings):
    with pytest.raises(FileNotFoundError, match="does not exist"):
        Environment(clean_settings / "missing.toml")


@pytest.mark.parametrize("content", ['[data]\ntraining="bad"\n', '[data]\nroot=4\n', '[data]\nroot=""\n'])
def test_bad_config_is_rejected(clean_settings, content):
    config = clean_settings / "qdata.toml"
    config.write_text(content)
    with pytest.raises(ValueError):
        Environment(config)


@pytest.mark.parametrize("package", ["openqdata", "qdata"])
def test_xdg_default_config(clean_settings, package):
    config = clean_settings / f"config/{package}/config.toml"
    config.parent.mkdir(parents=True)
    config.write_text('[data]\nroot="data"\n')
    assert Path(Environment().locations.raw.path) == config.parent / "data/raw"


def test_current_config_precedes_legacy_config(clean_settings):
    for package in ("openqdata", "qdata"):
        (clean_settings / f"{package}.toml").write_text(f'[data]\nroot="{package}-data"\n')
    environment = Environment()
    assert environment.config_file == clean_settings / "openqdata.toml"
    assert Path(environment.locations.raw.path) == clean_settings / "openqdata-data/raw"


def test_test_mode_ignores_production_storage(clean_settings, monkeypatch):
    root = clean_settings / "fixtures"
    for name in ["raw", "processed"]:
        (root / name).mkdir(parents=True)
    monkeypatch.setenv("OQ_DATA_TEST_MODE", "1")
    monkeypatch.setenv("OQ_DATA_TEST_ROOT", str(root))
    monkeypatch.setenv("OQ_DATA_ROOT", str(clean_settings / "production"))
    monkeypatch.setenv("OQ_DATA_CACHE_MODE", "on")
    environment = Environment()
    assert Path(environment.locations.raw.path) == root / "raw"
    assert not (clean_settings / "production").exists()
    with pytest.raises(RuntimeError, match="disabled"):
        environment.require_live("example")


def test_missing_fixture_root_does_not_create_it(clean_settings, monkeypatch):
    root = clean_settings / "missing"
    monkeypatch.setenv("OQ_DATA_TEST_MODE", "1")
    monkeypatch.setenv("OQ_DATA_TEST_ROOT", str(root))
    with pytest.raises(FileNotFoundError, match="fixture"):
        Environment()
    assert not root.exists()


def test_invalid_test_mode(clean_settings, monkeypatch):
    monkeypatch.setenv("OQ_DATA_TEST_MODE", "generate_tests")
    with pytest.raises(ValueError, match="0 or 1"):
        Environment()


@pytest.mark.parametrize("source", ["..", "../escape", "/absolute", ""])
def test_source_names_cannot_escape_locations(source):
    from openqdata import env
    with pytest.raises(ValueError):
        env.locations(source)


@pytest.mark.parametrize("previous", ["oqdata", "qdata"])
def test_renamed_package_reuses_existing_storage(clean_settings, previous):
    stored = clean_settings / ".local/share" / previous
    (stored / "processed").mkdir(parents=True)
    assert Path(Environment().locations.processed.path) == stored / "processed"
    assert not (clean_settings / ".local/share/openqdata").exists()


def test_new_configuration_precedes_previous_name(clean_settings):
    previous = clean_settings / "oqdata.toml"
    previous.write_text('[data]\nroot="existing"\n')
    assert Path(Environment().locations.raw.path) == clean_settings / "existing/raw"
    current = clean_settings / "openqdata.toml"
    current.write_text('[data]\nroot="selected"\n')
    assert Path(Environment().locations.raw.path) == clean_settings / "selected/raw"
