"""Independent benchmark and model installations share the core namespace."""
import os
import subprocess
import sys
from pathlib import Path

import pytest


@pytest.mark.parametrize("namespace", ["benchmark", "models"])
def test_extensions_from_separate_installations(tmp_path, namespace):
    extensions = [tmp_path / name for name in ("first", "second")]
    for extension in extensions:
        package = extension / "quantdata" / namespace / extension.name
        package.mkdir(parents=True)
        (package / "__init__.py").write_text(f"answer = {extension.name!r}\n")
    core_source = Path(__file__).resolve().parents[1] / "src"
    script = (
        f"from quantdata.{namespace}.first import answer as first; "
        f"from quantdata.{namespace}.second import answer as second; "
        "assert (first, second) == ('first', 'second')"
    )
    result = subprocess.run(
        [sys.executable, "-c", script],
        cwd=tmp_path,
        env={**os.environ, "PYTHONPATH": os.pathsep.join(str(path) for path in [*extensions, core_source])},
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr
