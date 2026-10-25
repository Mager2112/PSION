import csv
import os
from functools import lru_cache
from typing import Optional

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")

COMPANIES_CSV = os.path.join(DATA_DIR, "df_Uid_data_hack.csv")
PERSONS_CSV   = os.path.join(DATA_DIR, "df_Fid_Uid_link_hack.csv")
PAYMENTS_CSV  = os.path.join(DATA_DIR, "df_Uid_payment_hack.csv")


def _read_csv(path: str) -> list[dict]:
    """Читает CSV и возвращает список словарей (по одной на строку)."""
    if not os.path.exists(path):
        raise FileNotFoundError(f"Файл не найден: {path}")
    with open(path, encoding="utf-8-sig") as f:  # utf-8-sig — на случай BOM в начале
        reader = csv.DictReader(f)
        return list(reader)


@lru_cache(maxsize=1)
def load_companies() -> dict[str, dict]:
    """Все компании: SYNTHETIC_U -> строка с признаками."""
    rows = _read_csv(COMPANIES_CSV)
    return {r["SYNTHETIC_U"]: r for r in rows}


@lru_cache(maxsize=1)
def load_persons() -> list[dict]:
    """Связи физлиц с компаниями (сырой список)."""
    return _read_csv(PERSONS_CSV)


@lru_cache(maxsize=1)
def load_payments() -> list[dict]:
    """Платежи между компаниями (сырой список)."""
    return _read_csv(PAYMENTS_CSV)


def get_company(uid: str) -> Optional[dict]:
    return load_companies().get(uid)


def get_company_persons(uid: str) -> list[dict]:
    """Все физлица, связанные с компанией."""
    return [p for p in load_persons() if p["SYNTHETIC_U"] == uid]


def get_company_counterparties(uid: str) -> list[dict]:
    """Все платежи, где компания — либо отправитель, либо получатель."""
    return [
        p for p in load_payments()
        if p["PAYER"] == uid or p["BENEFICIARY"] == uid
    ]