import pytest
from unittest.mock import patch
from lib.browser import launch_browser, pause_for_2fa


def test_launch_browser_returns_page():
    pw, browser, page = launch_browser(headless=True)
    try:
        page.goto("about:blank")
        assert page.url == "about:blank"
    finally:
        browser.close()
        pw.stop()


def test_pause_for_2fa_prints_bank_name(capsys):
    class MockPage:
        def bring_to_front(self):
            pass

    with patch("builtins.input", return_value=""):
        pause_for_2fa(MockPage(), "Test Bank")

    captured = capsys.readouterr()
    assert "Test Bank" in captured.out
    assert "2FA" in captured.out
