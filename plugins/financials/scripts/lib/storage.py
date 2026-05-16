from pathlib import Path
from datetime import date
import pandas as pd

BANK_SCHEMA = {
    "amex": {
        "date": "Date",
        "description": "Description",
        "amount": "Amount",
        "type": "Type",
        "person": "Card Member",
    },
    "truist": {
        "date": "Date",
        "description": "Description",
        "amount": "Amount",
        "type": "Type",
        "person": None,  # update if cardholder column exists after first pull
    },
    "citi": {
        "date": "Transaction Date",
        "description": "Description",
        "amount": None,  # computed from Debit/Credit columns
        "type": "Transaction Type",
        "person": None,  # update if cardholder column exists after first pull
    },
}


def get_snapshot_dir(base_dir: str, snapshot_date: str = None) -> str:
    d = snapshot_date or date.today().isoformat()
    path = Path(base_dir) / d
    path.mkdir(parents=True, exist_ok=True)
    return str(path)


def normalize_csv(df: pd.DataFrame, bank: str) -> pd.DataFrame:
    schema = BANK_SCHEMA[bank]
    result = pd.DataFrame()
    result["date"] = df[schema["date"]]
    result["description"] = df[schema["description"]]

    if bank == "citi":
        debit = pd.to_numeric(df.get("Debit", pd.Series(0, index=df.index)), errors="coerce").fillna(0)
        credit = pd.to_numeric(df.get("Credit", pd.Series(0, index=df.index)), errors="coerce").fillna(0)
        result["amount"] = credit - debit
    elif bank == "amex":
        # Amex exports purchases as positive amounts; negate so outflow is negative
        result["amount"] = -pd.to_numeric(df[schema["amount"]], errors="coerce")
    else:
        result["amount"] = pd.to_numeric(df[schema["amount"]], errors="coerce")

    type_col = schema.get("type")
    result["type"] = df[type_col] if (type_col and type_col in df.columns) else None
    person_col = schema.get("person")
    result["person"] = df[person_col] if (person_col and person_col in df.columns) else None
    result["bank"] = bank
    return result


def load_snapshot(snapshot_dir: str) -> pd.DataFrame:
    frames = []
    for csv_file in sorted(Path(snapshot_dir).glob("*.csv")):
        bank = csv_file.stem.split("_")[0]  # "amex" from "amex_credit.csv"
        frames.append(normalize_csv(pd.read_csv(csv_file), bank))
    return pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()


def latest_snapshot(base_dir: str) -> str:
    snapshots = sorted(Path(base_dir).glob("????-??-??"), reverse=True)
    if not snapshots:
        raise FileNotFoundError(f"No snapshots found in {base_dir}")
    return str(snapshots[0])
