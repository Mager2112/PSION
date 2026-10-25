from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from typing import List, Optional
import os

from app.data_loader import (
    load_companies, get_company, get_company_counterparties,
    get_company_persons,
)
from app.models import Client, Event, Source, Consequences
from app.profiling import ClientProfile
from app.matching import score_event
from app.news_parser import fetch_news, news_to_event, _interpret
from app.demo_events import get_demo_events

app = FastAPI(
    title="ПСИОН",
    description="Программа Сканирования И Организации Новостей",
    version="0.3.3",
)

STATIC_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "static")
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


class AskRequest(BaseModel):
    question: str


class AskResponse(BaseModel):
    answer: str
    sources: List[Source] = Field(default_factory=list)


def _bank_products(row: dict) -> list[str]:
    mapping = {
        "CL_PRODUCT_RKO_MARK": "RKO",
        "CL_PRODUCT_GAR_MARK": "GAR",
        "CL_PRODUCT_LOA_MARK": "LOAN",
        "CL_PRODUCT_LEA_MARK": "LEASING",
        "CL_PRODUCT_DEP_MARK": "DEPOSIT",
        "CL_PRODUCT_ZPP_MARK": "SALARY",
        "FACTORING_MARK": "FACTORING",
    }
    return [name for col, name in mapping.items() if row.get(col) in ("1", "1.0", "True", "true")]


def _age_years(row: dict) -> int:
    grad = (row.get("COMPANY_AGE_YEARS_GRADATION") or "").lower()
    if "<1" in grad or "до 1" in grad: return 1
    if "1-3" in grad or "1–3" in grad: return 2
    if "3-5" in grad or "3–5" in grad: return 4
    if "5-10" in grad or "5–10" in grad: return 7
    if ">10" in grad or "более 10" in grad or "10+" in grad: return 15
    return 5


def _client_from_row(uid: str, row: dict) -> Client:
    fts_raw = row.get("FTS_COUNTRY_NAME") or ""
    fts_countries = [c.strip() for c in fts_raw.replace(";", ",").split(",") if c.strip()]
    payments = get_company_counterparties(uid)
    counterparts = sorted({
        p["PAYER"] if p.get("BENEFICIARY") == uid else p.get("BENEFICIARY")
        for p in payments
        if p.get("PAYER") and p.get("BENEFICIARY")
    })
    return Client(
        id=uid,
        name=f"Компания {uid}",
        industry=row.get("MAINOKVED_NAME") or "—",
        region=row.get("REGION") or "—",
        revenue=float(row.get("REVENUE_COMPANY") or 0),
        bank_products=_bank_products(row),
        age_years=_age_years(row),
        fts_countries=fts_countries,
        counterparties=counterparts,
    )


@app.get("/", include_in_schema=False)
def index():
    return FileResponse(os.path.join(STATIC_DIR, "index.html"))


@app.get("/health", tags=["root"])
def health_check():
    return {"status": "ok", "service": "ПСИОН"}


@app.get("/clients/search", response_model=List[Client], tags=["clients"])
def search_clients(
    q: str = Query(..., min_length=1),
    limit: int = Query(20, ge=1, le=100),
):
    q_low = q.strip().lower()
    found = []
    for uid, r in load_companies().items():
        haystack = " ".join([
            uid, r.get("REGION") or "", r.get("CITY") or "",
            r.get("MAINOKVED_NAME") or "", r.get("OKFS_NAME") or "",
        ]).lower()
        if q_low in haystack:
            found.append((uid, r))
        if len(found) >= limit:
            break
    return [_client_from_row(u, r) for u, r in found]


@app.get("/clients", response_model=List[Client], tags=["clients"])
def list_clients(
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
    industry: Optional[str] = None,
    region: Optional[str] = None,
):
    rows = list(load_companies().items())
    if industry:
        rows = [(u, r) for u, r in rows if industry.lower() in (r.get("MAINOKVED_NAME") or "").lower()]
    if region:
        rows = [(u, r) for u, r in rows if region.lower() in (r.get("REGION") or "").lower()]
    page = rows[offset: offset + limit]
    return [_client_from_row(u, r) for u, r in page]


@app.get("/clients/{client_id}", response_model=Client, tags=["clients"])
def get_client(client_id: str):
    row = get_company(client_id)
    if not row:
        raise HTTPException(status_code=404, detail="Клиент не найден")
    return _client_from_row(client_id, row)


@app.get("/clients/{client_id}/context", tags=["clients"])
def get_client_context(client_id: str):
    row = get_company(client_id)
    if not row:
        raise HTTPException(status_code=404, detail="Клиент не найден")
    client = _client_from_row(client_id, row)
    profile = ClientProfile(client)
    payments = get_company_counterparties(client_id)
    return {
        "company": client.model_dump(),
        "signals": profile.signals,
        "risks": profile.risks,
        "opportunities": profile.opportunities,
        "persons_count": len(get_company_persons(client_id)),
        "payments_total": sum(float(p.get("PAY_AMT") or 0) for p in payments),
    }


@app.get("/news/search", tags=["news"])
def search_news(q: str = Query(..., min_length=2), limit: int = Query(20, ge=1, le=100)):
    q_low = q.lower()
    results = []
    for n in fetch_news(limit=200):
        text = f"{n['title']} {n.get('summary', '')}".lower()
        if q_low in text:
            results.append(n)
        if len(results) >= limit:
            break
    return results


@app.get("/clients/{client_id}/feed", response_model=List[Event], tags=["events"])
def get_feed(client_id: str, limit: int = Query(30, ge=1, le=100)):
    row = get_company(client_id)
    if not row:
        raise HTTPException(status_code=404, detail="Клиент не найден")
    client = _client_from_row(client_id, row)
    profile = ClientProfile(client)

    scored: list[Event] = []

    # 1. Реальные новости из RSS
    for n in fetch_news(limit=100):
        ev = news_to_event(n, client_id)
        if not ev:
            continue
        result = score_event(ev, client, profile=profile)
        ev.relevance_score = result["score"]
        ev.client_signals = result["matched_signals"]
        _interpret(ev, ev.tags, ev.client_signals)
        # берём всё, что дало хоть какой-то скор (даже слабый)
        if result["score"] > 0:
            scored.append(ev)

    # 2. Демо-события (всегда, чтобы лента была содержательной)
    demo = get_demo_events(client_id)
    for ev in demo:
        result = score_event(ev, client, profile=profile)
        ev.client_signals = result["matched_signals"] or ["demo_event"]
        _interpret(ev, ev.tags, ev.client_signals)
        scored.append(ev)

    scored.sort(key=lambda e: e.relevance_score, reverse=True)
    return scored[:limit]


@app.get("/events/{event_id}", response_model=Event, tags=["events"])
def get_event(event_id: str):
    if event_id.startswith("demo-"):
        # demo-{client_id}-{n}
        parts = event_id.split("-")
        if len(parts) >= 3:
            client_id = parts[1]
            for ev in get_demo_events(client_id):
                if ev.id == event_id:
                    return ev
    for n in fetch_news(limit=200):
        ev = news_to_event(n, client_id="")
        if ev and ev.id == event_id:
            _interpret(ev, ev.tags, [])
            return ev
    raise HTTPException(status_code=404, detail="Событие не найдено")


@app.post("/events/{event_id}/ask", response_model=AskResponse, tags=["events"])
def ask_event(event_id: str, req: AskRequest):
    ev = get_event(event_id)
    return AskResponse(
        answer=(
            f"[Заглушка] Вопрос: «{req.question}». "
            f"По событию «{ev.title}». LLM-ответ будет здесь."
        ),
        sources=ev.sources,
    )