"""Tests for terminal.py CI helpers."""
from unittest.mock import patch

import pytest

from anubis.terminal import clear, error, is_ci, pause


def test_is_ci_false_by_default(monkeypatch):
    monkeypatch.delenv("CI", raising=False)
    monkeypatch.delenv("ANUBIS_CI", raising=False)
    assert is_ci() is False


def test_is_ci_true_when_ci_env(monkeypatch):
    monkeypatch.setenv("CI", "true")
    monkeypatch.delenv("ANUBIS_CI", raising=False)
    assert is_ci() is True


def test_is_ci_true_when_anubis_ci_env(monkeypatch):
    monkeypatch.delenv("CI", raising=False)
    monkeypatch.setenv("ANUBIS_CI", "1")
    assert is_ci() is True


def test_is_ci_false_when_ci_not_true(monkeypatch):
    monkeypatch.setenv("CI", "false")
    monkeypatch.delenv("ANUBIS_CI", raising=False)
    assert is_ci() is False


def test_error_ci_exits_1(monkeypatch, capsys):
    monkeypatch.setenv("ANUBIS_CI", "1")
    with pytest.raises(SystemExit) as exc_info:
        error("something went wrong")
    assert exc_info.value.code == 1
    captured = capsys.readouterr()
    assert "something went wrong" in captured.err


def test_error_ci_does_not_pause(monkeypatch):
    monkeypatch.setenv("ANUBIS_CI", "1")
    with patch("anubis.terminal.pause") as mock_pause, pytest.raises(SystemExit):
        error("oops")
    mock_pause.assert_not_called()


def test_clear_noop_in_ci(monkeypatch):
    monkeypatch.setenv("ANUBIS_CI", "1")
    with patch("os.system") as mock_sys:
        clear()
    mock_sys.assert_not_called()


def test_pause_noop_in_ci(monkeypatch):
    monkeypatch.setenv("ANUBIS_CI", "1")
    with patch("builtins.input") as mock_input, patch("os.system") as mock_sys:
        pause()
    mock_input.assert_not_called()
    mock_sys.assert_not_called()
