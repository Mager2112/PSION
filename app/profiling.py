from typing import List, Dict
from app.models import Client

INDUSTRY_SHORT = {
    "торговля": "Ритейл", "розничн": "Ритейл", "оптов": "Ритейл",
    "производств": "Производство", "обрабатыва": "Производство",
    "строительств": "Строительство",
    "финанс": "Финансы", "страхов": "Финансы",
    "сельск": "Агро", "лесн": "Агро",
    "транспорт": "Логистика", "логистик": "Логистика",
    "добыч": "Сырьё", "нефт": "Сырьё", "газ": "Сырьё",
    "энерг": "Энергетика",
    "ит": "IT", "информац": "IT", "связ": "IT",
}


def _short_industry(name: str) -> str:
    low = (name or "").lower()
    for key, val in INDUSTRY_SHORT.items():
        if key in low:
            return val
    return "Прочее"


class ClientProfile:
    def __init__(self, client: Client):
        self.client = client
        self.signals: List[str] = []
        self.risks: List[str] = []
        self.opportunities: List[str] = []
        self._analyze()

    def _analyze(self):
        c = self.client

        if "LOAN" in c.bank_products or "LEASING" in c.bank_products:
            self.signals.append("credit_exposure")
            self.risks.append("Зависимость от заёмного финансирования")
            self.opportunities.append("Хеджирование процентного риска")

        if "DEPOSIT" in c.bank_products:
            self.signals.append("deposit_holder")
            self.risks.append("Риск переоценки депозитной доходности")
            self.opportunities.append("Фиксация ставки по депозитам")

        if c.fts_countries:
            self.signals.append("foreign_trade")
            self.signals.append(f"fts_countries:{','.join(c.fts_countries)}")
            self.risks.append("Валютный и санкционный риск")
            self.opportunities.append("Диверсификация поставок")

        if c.age_years < 3:
            self.signals.append("young_company")
            self.risks.append("Ограниченная кредитная история")
        elif c.age_years > 10:
            self.signals.append("mature_company")
            self.opportunities.append("Доступ к более выгодным условиям финансирования")

        if c.revenue > 10_000_000_000:
            self.signals.append("large_business")
            self.risks.append("Высокая чувствительность к макроэкономике")

        if c.counterparties:
            self.signals.append(f"counterparties:{len(c.counterparties)}")
            if len(c.counterparties) < 3:
                self.risks.append("Высокая концентрация на контрагентах")
            else:
                self.signals.append("counterparties")

        short = _short_industry(c.industry)
        self.signals.append(f"industry:{short}")

    def to_dict(self) -> Dict:
        return {
            "client_id": self.client.id,
            "name": self.client.name,
            "industry": self.client.industry,
            "signals": self.signals,
            "risks": self.risks,
            "opportunities": self.opportunities,
        }