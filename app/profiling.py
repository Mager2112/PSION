from typing import List, Dict
from app.models import Client

class ClientProfile:
    """
    Обогащённый профиль клиента: сырые данные + вычисленные сигналы.
    Именно этот объект потом сравнивается с событиями.
    """
    def __init__(self, client: Client):
        self.client = client
        self.signals: List[str] = []
        self.risks: List[str] = []
        self.opportunities: List[str] = []
        self._analyze()

    def _analyze(self):
        c = self.client

        # 1. Кредитная нагрузка — критично для новостей о ставке
        if "LOAN" in c.bank_products or "LEA" in c.bank_products:
            self.signals.append("credit_exposure")
            self.risks.append("Зависимость от заёмного финансирования")
            self.opportunities.append("Хеджирование процентного риска")

        # 2. Депозиты — чувствительны к ставке и инфляции
        if "DEP" in c.bank_products:
            self.signals.append("deposit_holder")
            self.risks.append("Риск переоценки депозитной доходности")
            self.opportunities.append("Фиксация ставки по депозитам")

        # 3. Внешнеэкономическая деятельность — чувствительна к санкциям, курсам
        if c.fts_countries:
            self.signals.append("foreign_trade")
            self.signals.append(f"fts_countries:{','.join(c.fts_countries)}")
            self.risks.append("Валютный и санкционный риск")
            self.opportunities.append("Диверсификация поставок")

        # 4. Возраст бизнеса
        if c.age_years < 3:
            self.signals.append("young_company")
            self.risks.append("Ограниченная кредитная история")
        elif c.age_years > 10:
            self.signals.append("mature_company")
            self.opportunities.append("Доступ к более выгодным условиям финансирования")

        # 5. Масштаб — крупный бизнес чувствителен к макро
        if c.revenue > 10_000_000_000:
            self.signals.append("large_business")
            self.risks.append("Высокая чувствительность к макроэкономике")

        # 6. Контрагенты — зависимость от конкретных партнёров
        if c.counterparties:
            self.signals.append(f"counterparties:{len(c.counterparties)}")
            if len(c.counterparties) < 3:
                self.risks.append("Высокая концентрация на контрагентах")

        # 7. Отрасль — базовый сигнал
        self.signals.append(f"industry:{c.industry}")

    def to_dict(self) -> Dict:
        return {
            "client_id": self.client.id,
            "name": self.client.name,
            "industry": self.client.industry,
            "signals": self.signals,
            "risks": self.risks,
            "opportunities": self.opportunities,
        }