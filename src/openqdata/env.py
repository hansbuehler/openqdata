"""Data locations configured by OQ_DATA_* variables or a TOML file.

Precedence: environment, explicit config, first discovered config, defaults.
Importing this module does not create directories or connect to providers.
"""
from __future__ import annotations

import os
import tomllib
from dataclasses import dataclass
from pathlib import Path

from cdxcore.err import verify_inp
from cdxcore.subdir import CacheController, SubDir


@dataclass(frozen=True)
class Locations:
    """Raw vendor observations and processed reusable data products."""

    raw: SubDir
    processed: SubDir

    def __post_init__(self) -> None:
        for name in ("raw", "processed"):
            verify_inp(isinstance(getattr(self, name), SubDir), lambda: f"{name} must be a SubDir")

    def __call__(self, name: str, *, default_fmt=None, fmt_raw=None, fmt_processed=None) -> Locations:
        """Return source-specific locations, optionally selecting storage formats."""
        verify_inp(bool(name) and not Path(name).is_absolute() and ".." not in Path(name).parts,
                   lambda: f"Invalid source subdirectory: {name!r}")
        return Locations(
            raw=self.raw(name, fmt=default_fmt if fmt_raw is None else fmt_raw, create_directory=False),
            processed=self.processed(name, fmt=default_fmt if fmt_processed is None else fmt_processed, create_directory=False),
        )

    @staticmethod
    def create_from_root(root: str | Path | SubDir) -> Locations:
        """Describe the two locations below a root without creating files."""
        root = SubDir(str(root) if isinstance(root, Path) else root, create_directory=False)
        return Locations(root("raw", create_directory=False), root("processed", create_directory=False))


class Environment:
    """Resolve storage once at import; construct another instance to reload settings.

    Configuration uses a [data] table with root, raw, processed and cache_mode.
    Relative paths in a configuration file resolve against that file's directory.
    Test mode reads existing local fixtures with cacheonly and blocks providers.
    """

    CACHE_EXCLUDE_ARGS = ["self", "Context", "WRDSClient", "WIDBClient", "MassiveClient"]

    def __init__(self, config_file: str | Path | None = None) -> None:
        self.config_file: Path | None = None
        explicit = config_file if config_file is not None else os.environ.get("OQ_DATA_CONFIG")
        candidates = [Path(explicit).expanduser()] if explicit is not None else [
            Path.cwd() / "openqdata.toml",
            Path.cwd() / "qdata.toml",
            Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config")) / "openqdata/config.toml",
            Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config")) / "qdata/config.toml",
            Path.home() / ".openqdata.toml",
            Path.cwd() / "oqdata.toml",
            Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config")) / "oqdata/config.toml",
            Path.home() / ".oqdata.toml",
            Path.home() / ".qdata.toml",
        ]
        settings = {}
        for candidate in candidates:
            if candidate.is_file():
                self.config_file = candidate.resolve()
                with candidate.open("rb") as handle:
                    settings = tomllib.load(handle).get("data", {})
                if not isinstance(settings, dict):
                    raise ValueError("The TOML [data] section must be a table")
                unknown = settings.keys() - {"root", "raw", "processed", "cache_mode"}
                if unknown:
                    raise ValueError(f"Unknown [data] settings: {sorted(unknown)}")
                break
        if explicit is not None and self.config_file is None:
            raise FileNotFoundError(f"Configuration file does not exist: {explicit}")

        def location(key: str, default: Path) -> Path:
            value = os.environ.get(f"OQ_DATA_{key.upper()}")
            configured = value is None and key in settings
            value = settings.get(key, default) if value is None else value
            if not isinstance(value, (str, Path)) or not str(value).strip():
                raise ValueError(f"{key} must be a non-empty path")
            path = Path(os.path.expandvars(str(value))).expanduser()
            if configured and not path.is_absolute():
                path = self.config_file.parent / path
            return path.resolve()

        mode = os.environ.get("OQ_DATA_TEST_MODE", "0")
        if mode not in {"0", "1"}:
            raise ValueError("OQ_DATA_TEST_MODE must be 0 or 1; fixture generation is explicit")
        self.test_mode = mode == "1"
        self.generate_test_data_mode = False
        # Keep the established default so a package rename cannot hide existing caches.
        default_root = Path.home() / ".local/share/openqdata"
        # Existing storage keeps its path; changing the import name must not hide caches.
        if not default_root.exists():
            for previous in ("oqdata", "qdata"):
                candidate = Path.home() / ".local/share" / previous
                if candidate.is_dir():
                    default_root = candidate
                    break
        root = location("root", default_root)
        fixture_root = Path(os.environ.get("OQ_DATA_TEST_ROOT", Path(__file__).resolve().parents[2] / "tests/stored_data")).expanduser().resolve()
        self._test_data_locations = Locations.create_from_root(fixture_root)
        cache_mode = "cacheonly" if self.test_mode else os.environ.get("OQ_DATA_CACHE_MODE", settings.get("cache_mode", "on"))
        controller = CacheController(exclude_arg_types=self.CACHE_EXCLUDE_ARGS, cache_mode=cache_mode)
        self.locations = Locations(**{
            name: SubDir(str(fixture_root / name if self.test_mode else location(name, root / name)),
                         cache_controller=controller, create_directory=False)
            for name in ("raw", "processed")
        })
        if self.test_mode:
            for name in ("raw", "processed"):
                if not (fixture_root / name).is_dir():
                    raise FileNotFoundError(f"Missing local fixture directory: {fixture_root / name}")

    def require_live(self, provider: str) -> None:
        """Refuse provider access before credentials or network are consulted."""
        if self.test_mode:
            raise RuntimeError(f"{provider} access disabled by OQ_DATA_TEST_MODE=1; supply local fixtures")


env = Environment()
