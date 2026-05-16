import sys
import os
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from banks import amex, truist, citi
from lib.storage import get_snapshot_dir

SNAPSHOT_BASE = os.path.expanduser("~/Documents/financials/snapshots")

BANK_NAMES = ["amex", "truist", "citi"]


def _bank_modules():
    return {
        "amex": amex,
        "truist": truist,
        "citi": citi,
    }


def run(banks=None):
    bank_modules = _bank_modules()
    targets = banks or list(BANK_NAMES)
    for bank in targets:
        if bank not in bank_modules:
            raise ValueError(f"Unknown bank: {bank}. Valid: {list(bank_modules.keys())}")

    snapshot_dir = get_snapshot_dir(SNAPSHOT_BASE)
    print(f"Saving to: {snapshot_dir}\n")

    results = {}
    for bank in targets:
        try:
            path = bank_modules[bank].pull(snapshot_dir)
            results[bank] = ("ok", path)
        except Exception as e:
            results[bank] = ("error", str(e))
            print(f"[{bank}] ERROR: {e}")

    print("\n--- Summary ---")
    for bank, (status, detail) in results.items():
        icon = "✓" if status == "ok" else "✗"
        print(f"{icon} {bank}: {detail}")

    return results


if __name__ == "__main__":
    banks_arg = sys.argv[1:] or None
    run(banks=banks_arg)
