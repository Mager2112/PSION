from app.models import Event, Client
from app.profiling import ClientProfile

EVENT_SIGNAL_MAP = {
    "rate": ["credit_exposure", "deposit_holder"],
    "inflation": ["credit_exposure", "deposit_holder"],
    "sanctions": ["foreign_trade"],
    "currency": ["foreign_trade"],
    "regulation": ["large_business", "mature_company"],
    "consumption": ["industry:Ритейл", "industry:Производство"],
    "logistics": ["foreign_trade", "counterparties"],
    "commodities": ["foreign_trade", "large_business"],
}

WEAK_SIGNALS = {"large_business", "mature_company", "counterparties"}


def score_event(event: Event, client: Client, profile: ClientProfile | None = None) -> dict:
    if profile is None:
        profile = ClientProfile(client)

    matched = []
    for tag in event.tags:
        for signal in EVENT_SIGNAL_MAP.get(tag, []):
            if signal in profile.signals:
                matched.append(signal)

    industry_signal = f"industry:{client.industry}"
    if industry_signal in profile.signals and any(
        t in event.tags for t in ("consumption", "regulation")
    ):
        matched.append(industry_signal)

    matched = sorted(set(matched))
    strong = [m for m in matched if m not in WEAK_SIGNALS]

    # Мягкий скор: сильный сигнал 0.4, слабый 0.1
    score = 0.4 * len(strong) + 0.1 * (len(matched) - len(strong))
    score = min(round(score, 2), 1.0)

    # Если вообще ничего не совпало — 0 (новость не показываем)
    if not matched:
        score = 0.0

    return {
        "event_id": event.id,
        "client_id": client.id,
        "score": score,
        "matched_signals": matched,
        "explanation": (
            f"Теги события {event.tags} совпали с сигналами клиента: "
            f"{', '.join(matched) or 'нет прямых совпадений'}"
        ),
    }