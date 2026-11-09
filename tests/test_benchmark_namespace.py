"""Benchmark extensions can share the namespace owned by the core package."""
import os
import subprocess
import sys
from pathlib import Path


def test_benchmark_extension_from_separate_installation(tmp_path):
    extension = tmp_path / "extension"
    package = extension / "quantdata/benchmark/example"
    package.mkdir(parents=True)
    (package / "__init__.py").write_text("answer = 42\n")
    core_source = Path(__file__).resolve().parents[1] / "src"
    result = subprocess.run(
        [sys.executable, "-c", "from quantdata.benchmark.example import answer; assert answer == 42"],
        cwd=tmp_path,
        env={**os.environ, "PYTHONPATH": os.pathsep.join((str(extension), str(core_source)))},
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr
