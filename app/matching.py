from app.models import Event, Client
from app.profiling import ClientProfile

# Какие признаки клиента делают событие релевантным.
# Ключ — тег события, значение — сигналы клиента, которые его "ловят".
EVENT_SIGNAL_MAP = {
    "rate": ["credit_exposure", "deposit_holder", "large_business"],
    "inflation": ["credit_exposure", "deposit_holder", "large_business"],
    "sanctions": ["foreign_trade", "large_business"],
    "currency": ["foreign_trade"],
    "regulation": ["large_business", "mature_company"],
    "consumption": ["industry:Ритейл", "industry:Производство"],
    "logistics": ["foreign_trade", "counterparties"],
}

def score_event(event: Event, client: Client) -> dict:
    """
    Возвращает словарь: score, совпавшие сигналы, объяснение.
    """
    profile = ClientProfile(client)
    matched = []

    for tag in event.tags:
        for signal in EVENT_SIGNAL_MAP.get(tag, []):
            if signal in profile.signals:
                matched.append(signal)

    # Базовая релевантность: сколько сигналов совпало
    base_score = len(set(matched)) * 0.25
    # Отраслевое совпадение — сильный бонус
    if f"industry:{client.industry}" in profile.signals and any(
        t in event.tags for t in ("consumption", "regulation")
    ):
        base_score += 0.3

    score = min(round(base_score, 2), 1.0)
    return {
        "event_id": event.id,
        "client_id": client.id,
        "score": score,
        "matched_signals": sorted(set(matched)),
        "explanation": (
            f"Событие тегов {event.tags} совпало с сигналами клиента: "
            f"{', '.join(sorted(set(matched))) or 'нет прямых совпадений'}"
        ),
    }