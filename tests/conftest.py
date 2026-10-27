"""Tests always use local fixtures and refuse network access."""
import os
import socket
from pathlib import Path

import pytest

os.environ["OQ_DATA_TEST_MODE"] = "1"
os.environ["OQ_DATA_TEST_ROOT"] = str(Path(__file__).parent / "stored_data")

@pytest.fixture(autouse=True)
def no_network(monkeypatch):
    def blocked(*args, **kwargs):
        raise AssertionError("Network access is forbidden in qdata tests")
    monkeypatch.setattr(socket.socket, "connect", blocked)
    monkeypatch.setattr(socket, "create_connection", blocked)
