import csv
import os
from functools import lru_cache
from typing import Optional

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")

COMPANIES_CSV = os.path.join(DATA_DIR, "df_Uid_data_hack.csv")
PERSONS_CSV   = os.path.join(DATA_DIR, "df_Fid_Uid_link_hack.csv")
PAYMENTS_CSV  = os.path.join(DATA_DIR, "df_Uid_payment_hack.csv")


def _read_csv(path: str) -> list[dict]:
    if not os.path.exists(path):
        raise FileNotFoundError(f"Файл не найден: {path}")
    with open(path, encoding="utf-8-sig") as f:
        sample = f.read(2048)
        f.seek(0)
        delimiter = ";" if sample.count(";") > sample.count(",") else ","
        reader = csv.DictReader(f, delimiter=delimiter)
        rows = []
        for r in reader:
            clean = {(k or "").strip(): (v.strip() if isinstance(v, str) else v)
                     for k, v in r.items()}
            rows.append(clean)
        return rows


@lru_cache(maxsize=1)
def load_companies() -> dict[str, dict]:
    rows = _read_csv(COMPANIES_CSV)
    if not rows:
        raise ValueError("CSV пустой")
    if "SYNTHETIC_U" not in rows[0]:
        raise ValueError(f"В CSV нет колонки SYNTHETIC_U. Есть: {list(rows[0].keys())}")
    return {r["SYNTHETIC_U"]: r for r in rows if r.get("SYNTHETIC_U")}


@lru_cache(maxsize=1)
def load_persons() -> list[dict]:
    return _read_csv(PERSONS_CSV)


@lru_cache(maxsize=1)
def load_payments() -> list[dict]:
    return _read_csv(PAYMENTS_CSV)


def get_company(uid: str) -> Optional[dict]:
    return load_companies().get(uid)


def get_company_persons(uid: str) -> list[dict]:
    return [p for p in load_persons() if p.get("SYNTHETIC_U") == uid]


def get_company_counterparties(uid: str) -> list[dict]:
    return [
        p for p in load_payments()
        if p.get("PAYER") == uid or p.get("BENEFICIARY") == uid
    ]