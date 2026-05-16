import io
import pytest
import pandas as pd
from pathlib import Path
from datetime import date
from lib.storage import normalize_csv, get_snapshot_dir, load_snapshot, latest_snapshot

AMEX_CSV = """Date,Description,Amount,Card Member,Account #
2026-04-15,WHOLE FOODS MARKET,45.23,DEREK HONERLAW,12345
2026-04-16,NETFLIX,15.99,DEREK HONERLAW,12345
2026-04-17,AMAZON PRIME,12.00,WIFE HONERLAW,67890
2026-04-18,PAYMENT -THANK YOU,-500.00,DEREK HONERLAW,12345
"""

TRUIST_CSV = """Date,Description,Transaction Type,Amount
2026-04-15,PAYCHECK,Credit,2500.00
2026-04-16,RENT CHECK,Debit,-1200.00
"""

CITI_CSV = """Transaction Date,Description,Debit,Credit
2026-04-15,STARBUCKS,5.50,
2026-04-16,PAYCHECK,,500.00
"""


def test_normalize_amex_columns():
    df = pd.read_csv(io.StringIO(AMEX_CSV))
    result = normalize_csv(df, "amex")
    assert list(result.columns) == ["date", "description", "amount", "type", "person", "bank"]


def test_normalize_amex_person():
    df = pd.read_csv(io.StringIO(AMEX_CSV))
    result = normalize_csv(df, "amex")
    assert result.iloc[0]["person"] == "DEREK HONERLAW"
    assert result.iloc[2]["person"] == "WIFE HONERLAW"


def test_normalize_amex_amounts():
    df = pd.read_csv(io.StringIO(AMEX_CSV))
    result = normalize_csv(df, "amex")
    assert result.iloc[0]["amount"] == pytest.approx(-45.23)   # purchase -> negative
    assert result.iloc[3]["amount"] == pytest.approx(500.00)   # payment -> positive


def test_normalize_truist_columns():
    df = pd.read_csv(io.StringIO(TRUIST_CSV))
    result = normalize_csv(df, "truist")
    assert list(result.columns) == ["date", "description", "amount", "type", "person", "bank"]


def test_normalize_truist_amounts():
    df = pd.read_csv(io.StringIO(TRUIST_CSV))
    result = normalize_csv(df, "truist")
    assert result.iloc[0]["amount"] == pytest.approx(2500.00)
    assert result.iloc[1]["amount"] == pytest.approx(-1200.00)


def test_normalize_truist_person_is_none():
    df = pd.read_csv(io.StringIO(TRUIST_CSV))
    result = normalize_csv(df, "truist")
    assert result["person"].isna().all()


def test_normalize_citi_columns():
    df = pd.read_csv(io.StringIO(CITI_CSV))
    result = normalize_csv(df, "citi")
    assert list(result.columns) == ["date", "description", "amount", "type", "person", "bank"]


def test_normalize_citi_amounts():
    df = pd.read_csv(io.StringIO(CITI_CSV))
    result = normalize_csv(df, "citi")
    assert result.iloc[0]["amount"] == pytest.approx(-5.50)   # debit -> negative
    assert result.iloc[1]["amount"] == pytest.approx(500.00)  # credit -> positive


def test_normalize_bank_field():
    df = pd.read_csv(io.StringIO(AMEX_CSV))
    result = normalize_csv(df, "amex")
    assert (result["bank"] == "amex").all()


def test_get_snapshot_dir_creates_folder(tmp_path):
    d = get_snapshot_dir(str(tmp_path), "2026-05-16")
    assert Path(d).exists()
    assert Path(d).name == "2026-05-16"


def test_get_snapshot_dir_defaults_to_today(tmp_path):
    d = get_snapshot_dir(str(tmp_path))
    assert Path(d).name == date.today().isoformat()


def test_get_snapshot_dir_idempotent(tmp_path):
    get_snapshot_dir(str(tmp_path), "2026-05-16")
    get_snapshot_dir(str(tmp_path), "2026-05-16")  # no error on second call
    assert (tmp_path / "2026-05-16").exists()


def test_load_snapshot(tmp_path):
    snap = tmp_path / "2026-05-16"
    snap.mkdir()
    (snap / "amex_credit.csv").write_text(AMEX_CSV)
    result = load_snapshot(str(snap))
    assert len(result) == 4
    assert set(result.columns) == {"date", "description", "amount", "type", "person", "bank"}
    assert (result["bank"] == "amex").all()


def test_load_snapshot_multiple_banks(tmp_path):
    snap = tmp_path / "2026-05-16"
    snap.mkdir()
    (snap / "amex_credit.csv").write_text(AMEX_CSV)
    (snap / "truist_checking.csv").write_text(TRUIST_CSV)
    result = load_snapshot(str(snap))
    assert set(result["bank"].unique()) == {"amex", "truist"}
    assert len(result) == 6


def test_latest_snapshot(tmp_path):
    (tmp_path / "2026-04-01").mkdir()
    (tmp_path / "2026-05-15").mkdir()
    (tmp_path / "2026-05-16").mkdir()
    assert Path(latest_snapshot(str(tmp_path))).name == "2026-05-16"


def test_latest_snapshot_raises_when_empty(tmp_path):
    with pytest.raises(FileNotFoundError):
        latest_snapshot(str(tmp_path))
