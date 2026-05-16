import pytest
from unittest.mock import patch, MagicMock


def test_pull_all_banks(tmp_path):
    with patch("pull.amex") as mock_amex, \
         patch("pull.truist") as mock_truist, \
         patch("pull.citi") as mock_citi, \
         patch("pull.get_snapshot_dir", return_value=str(tmp_path)):
        mock_amex.pull.return_value = str(tmp_path / "amex_credit.csv")
        mock_truist.pull.return_value = str(tmp_path / "truist_checking.csv")
        mock_citi.pull.return_value = str(tmp_path / "citi_credit.csv")

        from pull import run
        results = run(banks=None)

        mock_amex.pull.assert_called_once_with(str(tmp_path))
        mock_truist.pull.assert_called_once_with(str(tmp_path))
        mock_citi.pull.assert_called_once_with(str(tmp_path))
        assert all(status == "ok" for status, _ in results.values())


def test_pull_single_bank(tmp_path):
    with patch("pull.amex") as mock_amex, \
         patch("pull.truist") as mock_truist, \
         patch("pull.get_snapshot_dir", return_value=str(tmp_path)):
        mock_amex.pull.return_value = str(tmp_path / "amex_credit.csv")

        from pull import run
        results = run(banks=["amex"])

        mock_amex.pull.assert_called_once()
        mock_truist.pull.assert_not_called()


def test_pull_unknown_bank_raises():
    from pull import run
    with pytest.raises(ValueError, match="Unknown bank"):
        run(banks=["unknown"])


def test_pull_bank_error_captured(tmp_path):
    with patch("pull.amex") as mock_amex, \
         patch("pull.get_snapshot_dir", return_value=str(tmp_path)):
        mock_amex.pull.side_effect = Exception("login failed")

        from pull import run
        results = run(banks=["amex"])

        status, detail = results["amex"]
        assert status == "error"
        assert "login failed" in detail
