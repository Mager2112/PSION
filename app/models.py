from pydantic import BaseModel, Field
from typing import List, Optional


class Client(BaseModel):
    id: str
    name: str
    industry: str
    region: str
    revenue: float
    bank_products: List[str] = Field(default_factory=list)
    age_years: int = 5
    fts_countries: List[str] = Field(default_factory=list)
    counterparties: List[str] = Field(default_factory=list)


class Source(BaseModel):
    title: str
    url: Optional[str] = None
    type: str  # "news" | "alfa_analytics"


class Consequences(BaseModel):
    risks: List[str] = Field(default_factory=list)
    opportunities: List[str] = Field(default_factory=list)


class Event(BaseModel):
    id: str
    client_id: str
    title: str
    what_happened: str
    why_important: str
    consequences: Consequences = Field(default_factory=Consequences)
    actions: List[str] = Field(default_factory=list)
    bank_view: str = ""
    ai_view: str = ""
    sources: List[Source] = Field(default_factory=list)
    client_signals: List[str] = Field(default_factory=list)
    relevance_score: float = 0.0
    tags: List[str] = Field(default_factory=list)


class AskRequest(BaseModel):
    question: str


class AskResponse(BaseModel):
    answer: str
    sources: List[Source] = Field(default_factory=list)