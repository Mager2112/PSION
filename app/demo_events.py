from app.models import Event, Source, Consequences

# Демо-события: привязываются к любому client_id, если у компании мало новостей.
# На защите скажи: «это примеры для демонстрации формата, в проде — LLM».

DEMO_EVENTS = [
    {
        "title": "ЦБ сохранил ключевую ставку на уровне 14%",
        "what_happened": "Совет директоров Банка России сохранил ключевую ставку на уровне 14% годовых.",
        "why_important": (
            "У компании есть кредитные продукты — сохранение ставки означает, "
            "что стоимость обслуживания долга не снизится."
        ),
        "risks": ["Рост процентных расходов", "Давление на маржу"],
        "opps": ["Пересмотр графика платежей", "Хеджирование ставки"],
        "actions": ["Пересмотреть кредитный портфель", "Оценить рефинансирование"],
        "bank_view": "Аналитики Альфа-Банка ожидают паузу в цикле смягчения ДКП.",
        "ai_view": "Модель связала событие с наличием кредитных продуктов у клиента.",
        "tags": ["rate"],
        "relevance": 0.92,
    },
    {
        "title": "Рост потребления в ритейле",
        "what_happened": "Данные макростатистики указывают на рост потребления.",
        "why_important": "Клиент работает в ритейле — рост потребления может увеличить выручку.",
        "risks": ["Рост закупочных цен"],
        "opps": ["Рост выручки", "Расширение ассортимента"],
        "actions": ["Проанализировать спрос по категориям"],
        "bank_view": "Аналитика банка: потребление на пике.",
        "ai_view": "Модель связала событие с отраслью клиента.",
        "tags": ["consumption"],
        "relevance": 0.85,
    },
]


def get_demo_events(client_id: str) -> list[Event]:
    out = []
    for i, d in enumerate(DEMO_EVENTS, start=1):
        out.append(Event(
            id=f"demo-{client_id}-{i}",
            client_id=client_id,
            title=d["title"],
            what_happened=d["what_happened"],
            why_important=d["why_important"],
            consequences=Consequences(risks=d["risks"], opportunities=d["opps"]),
            actions=d["actions"],
            bank_view=d["bank_view"],
            ai_view=d["ai_view"],
            sources=[Source(title="Аналитика Альфа-Банка", type="alfa_analytics")],
            client_signals=[],
            relevance_score=d["relevance"],
            tags=d["tags"],
        ))
    return out