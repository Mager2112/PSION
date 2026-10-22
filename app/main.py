from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from typing import List, Optional

app = FastAPI(
    title="ПСИОН",
    description="Программа Сканирования И Организации Новостей",
    version="0.2.1",
)

# ---------- Модели (то, как выглядит JSON) ----------

class Client(BaseModel):
    id: str
    name: str
    industry: str
    region: str
    revenue: float
    bank_products: List[str] = Field(default_factory=list)

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
    consequences: Consequences
    actions: List[str] = Field(default_factory=list)
    bank_view: str
    ai_view: str
    sources: List[Source] = Field(default_factory=list)
    client_signals: List[str] = Field(default_factory=list)
    relevance_score: float = 0.0

class AskRequest(BaseModel):
    question: str

class AskResponse(BaseModel):
    answer: str
    sources: List[Source] = Field(default_factory=list)

# ---------- Фейковые данные (потом заменим на CSV/БД) ----------

CLIENTS = [
    Client(id="c1", name="ООО Ромашка", industry="Производство",
           region="Москва", revenue=20_000_000_000,
           bank_products=["RKO", "LOAN"]),
    Client(id="c2", name="АО Лютик", industry="Ритейл",
           region="Санкт-Петербург", revenue=18_000_000_000,
           bank_products=["RKO", "DEP"]),
]

EVENTS = [
    Event(
        id="e1", client_id="c1",
        title="ЦБ сохранил ключевую ставку на уровне 14%",
        what_happened="Совет директоров Банка России сохранил ключевую ставку на уровне 14% годовых.",
        why_important="У компании есть кредитные продукты — сохранение ставки означает, что стоимость обслуживания долга не снизится.",
        consequences=Consequences(
            risks=["Рост процентных расходов", "Давление на маржу"],
            opportunities=["Пересмотр графика платежей", "Хеджирование ставки"],
        ),
        actions=["Пересмотреть кредитный портфель", "Оценить рефинансирование"],
        bank_view="Аналитики Альфа-Банка ожидают паузу в цикле смягчения ДКП.",
        ai_view="Модель связала событие с наличием кредитных продуктов у клиента.",
        sources=[Source(title="Ключевая ставка ЦБ РФ", type="alfa_analytics")],
        client_signals=["CL_PRODUCT_LOA_MARK=1", "отрасль: Производство"],
        relevance_score=0.92,
    ),
    Event(
        id="e2", client_id="c2",
        title="Рост потребления в ритейле",
        what_happened="Данные макростатистики указывают на рост потребления.",
        why_important="Клиент работает в ритейле — рост потребления может увеличить выручку.",
        consequences=Consequences(
            risks=["Рост закупочных цен"],
            opportunities=["Рост выручки", "Расширение ассортимента"],
        ),
        actions=["Проанализировать спрос по категориям"],
        bank_view="Аналитика банка: потребление на пике.",
        ai_view="Модель связала событие с отраслью клиента.",
        sources=[Source(title="Потребление на пике", type="alfa_analytics")],
        client_signals=["MAINOKVED_NAME=Ритейл"],
        relevance_score=0.85,
    ),
]

# ---------- Служебные эндпоинты ----------

@app.get("/", tags=["root"])
def root():
    return {"service": "ПСИОН", "docs": "/docs", "health": "/health"}

@app.get("/health", tags=["root"])
def health_check():
    return {"status": "ok", "service": "ПСИОН"}

# ---------- Клиенты ----------

@app.get("/clients", response_model=List[Client], tags=["clients"])
def list_clients():
    return CLIENTS

@app.get("/clients/{client_id}", response_model=Client, tags=["clients"])
def get_client(client_id: str):
    for c in CLIENTS:
        if c.id == client_id:
            return c
    raise HTTPException(status_code=404, detail="Клиент не найден")

# ---------- Лента и события ----------

@app.get("/clients/{client_id}/feed", response_model=List[Event], tags=["events"])
def get_feed(client_id: str):
    feed = [e for e in EVENTS if e.client_id == client_id]
    if not feed:
        raise HTTPException(status_code=404, detail="Для этого клиента событий нет")
    return sorted(feed, key=lambda e: e.relevance_score, reverse=True)

@app.get("/events/{event_id}", response_model=Event, tags=["events"])
def get_event(event_id: str):
    for e in EVENTS:
        if e.id == event_id:
            return e
    raise HTTPException(status_code=404, detail="Событие не найдено")

@app.post("/events/{event_id}/ask", response_model=AskResponse, tags=["events"])
def ask_event(event_id: str, req: AskRequest):
    for e in EVENTS:
        if e.id == event_id:
            return AskResponse(
                answer=f"[Заглушка] Вы спросили: «{req.question}». Ответ по событию «{e.title}» будет сгенерирован LLM позже.",
                sources=e.sources,
            )
    raise HTTPException(status_code=404, detail="Событие не найдено")