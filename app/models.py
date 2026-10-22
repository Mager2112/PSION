from pydantic import BaseModel, Field
from typing import List, Optional

class Client(BaseModel):
    id: str
    name: str
    industry: str
    region: str
    revenue: float
    bank_products: List[str] = Field(default_factory=list)
    # новые поля для анализа
    age_years: int = 5
    fts_countries: List[str] = Field(default_factory=list)
    counterparties: List[str] = Field(default_factory=list)

class Event(BaseModel):
    # ... всё, что было ...
    tags: List[str] = Field(default_factory=list)  # rate, inflation, sanctions, currency...