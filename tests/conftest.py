import os

import pytest


@pytest.fixture
def mock_mac(monkeypatch):
    monkeypatch.setattr(os, "name", "posix")
    monkeypatch.setenv("USER", "testuser")
    monkeypatch.setenv("HOME", "/Users/testuser")


@pytest.fixture
def mock_windows(monkeypatch):
    monkeypatch.setattr(os, "name", "nt")
    monkeypatch.setenv("USERNAME", "testuser")
    monkeypatch.setenv("LOCALAPPDATA", "C:\\Users\\testuser\\AppData\\Local")
    monkeypatch.setenv("USERPROFILE", "C:\\Users\\testuser")
