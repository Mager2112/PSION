import hashlib
import re
from typing import Optional
from functools import lru_cache

import feedparser

from app.models import Event, Source, Consequences

RSS_SOURCES = [
    ("ЦБ РФ", "https://www.cbr.ru/rss/RssNews"),
    ("РБК", "https://rssexport.rbc.ru/rbcnews/news/30/full.rss"),
    ("Интерфакс", "https://www.interfax.ru/rss.asp"),
]

TAG_KEYWORDS = {
    "rate": ["ключев", "ставк", "цб", "банк россии", "дкп", "денежно-кредитн"],
    "inflation": ["инфляц", "рост цен", "потребительск"],
    "sanctions": ["санкц", "ограничен", "запрет", "эмбарго"],
    "currency": ["курс", "валют", "доллар", "евро", "юан", "рубл"],
    "regulation": ["закон", "регулир", "налог", "пошлин", "штраф", "фас"],
    "consumption": ["потреблен", "ритейл", "продаж", "спрос"],
    "logistics": ["логистик", "поставк", "транспорт", "грузооборот"],
    "commodities": ["нефт", "газ", "золот", "металл", "сырь"],
}


def _classify(text: str) -> list[str]:
    low = text.lower()
    return [tag for tag, words in TAG_KEYWORDS.items() if any(w in low for w in words)]


def _make_id(url: str, title: str) -> str:
    return hashlib.sha1(f"{url}|{title}".encode("utf-8")).hexdigest()[:16]


def _strip_html(text: str) -> str:
    return re.sub(r"<[^>]+>", "", text or "").strip()


@lru_cache(maxsize=1)
def _fetch_all_cached() -> tuple:
    items = []
    for source_name, url in RSS_SOURCES:
        try:
            feed = feedparser.parse(url)
            for entry in feed.entries[:20]:
                title = _strip_html(entry.get("title", ""))
                summary = _strip_html(entry.get("summary", entry.get("description", "")))
                link = entry.get("link", "")
                items.append({
                    "source": source_name,
                    "title": title,
                    "summary": summary,
                    "url": link,
                    "published": entry.get("published", ""),
                })
        except Exception as e:
            print(f"[news_parser] Ошибка {source_name}: {e}")
    return tuple(items)


def fetch_news(limit: int = 50) -> list[dict]:
    return list(_fetch_all_cached())[:limit]


# ---------- Шаблонная интерпретация ----------

_TAG_EXPLANATIONS = {
    "rate": {
        "why": "Изменение ключевой ставки влияет на стоимость заёмного финансирования и доходность депозитов.",
        "risks": ["Рост процентных расходов", "Давление на маржу"],
        "opps": ["Пересмотр графика платежей", "Хеджирование ставки"],
        "action": "Пересмотреть кредитный портфель и график платежей.",
    },
    "inflation": {
        "why": "Инфляция влияет на себестоимость, цены и покупательную способность.",
        "risks": ["Рост затрат", "Снижение спроса"],
        "opps": ["Индексация цен", "Пересмотр договоров"],
        "action": "Оценить влияние на себестоимость и pricing.",
    },
    "sanctions": {
        "why": "Санкционные ограничения затрагивают внешнеторговые операции и контрагентов.",
        "risks": ["Блокировка платежей", "Потеря поставщиков"],
        "opps": ["Диверсификация поставок", "Новые рынки"],
        "action": "Проверить контрагентов и альтернативные каналы поставок.",
    },
    "currency": {
        "why": "Валютный курс влияет на экспорт/импорт и валютную выручку.",
        "risks": ["Курсовые убытки", "Рост стоимости импорта"],
        "opps": ["Хеджирование", "Пересмотр контрактов"],
        "action": "Оценить валютную экспозицию.",
    },
    "regulation": {
        "why": "Изменения регулирования требуют адаптации процессов и могут повлечь затраты.",
        "risks": ["Штрафы", "Дополнительные издержки"],
        "opps": ["Ранняя адаптация", "Конкурентное преимущество"],
        "action": "Проверить соответствие новым требованиям.",
    },
    "consumption": {
        "why": "Динамика потребления напрямую влияет на выручку и спрос.",
        "risks": ["Снижение спроса", "Рост конкуренции"],
        "opps": ["Рост выручки", "Расширение ассортимента"],
        "action": "Проанализировать спрос по категориям.",
    },
    "logistics": {
        "why": "Логистика влияет на сроки, стоимость поставок и доступность товаров.",
        "risks": ["Рост логистических затрат", "Срывы поставок"],
        "opps": ["Оптимизация маршрутов", "Новые перевозчики"],
        "action": "Пересмотреть логистические цепочки.",
    },
    "commodities": {
        "why": "Цены на сырьё влияют на себестоимость и выручку.",
        "risks": ["Рост затрат на сырьё"],
        "opps": ["Фиксация цен", "Пересмотр контрактов"],
        "action": "Оценить сырьевую экспозицию.",
    },
}


def _interpret(ev: Event, tags: list[str], client_signals: list[str]) -> None:
    if not tags:
        ev.why_important = (
            "Событие общего характера. Прямой связи с профилем компании не выявлено, "
            "но новость может быть полезна для мониторинга рынка."
        )
        ev.bank_view = "Позиция Альфа-Банка будет добавлена из аналитических материалов (RAG)."
        ev.ai_view = "AI не нашёл сильных совпадений с профилем компании."
        return

    tag = tags[0]
    info = _TAG_EXPLANATIONS.get(tag, {})
    signals_str = ", ".join(client_signals) if client_signals else "профиль компании"

    ev.why_important = (
        f"{info.get('why', 'Событие может влиять на бизнес компании.')} "
        f"Релевантно для компании по признакам: {signals_str}."
    )
    ev.consequences = Consequences(
        risks=info.get("risks", []),
        opportunities=info.get("opps", []),
    )
    ev.actions = [info.get("action", "Провести дополнительный анализ.")]
    ev.bank_view = "Позиция Альфа-Банка будет добавлена из аналитических материалов (RAG)."
    ev.ai_view = (
        f"AI связал событие с тегом «{tag}» и сигналами клиента: {signals_str}."
    )


def news_to_event(item: dict, client_id: str = "") -> Optional[Event]:
    if not item.get("title"):
        return None
    text_for_tags = f"{item['title']} {item.get('summary', '')}"
    tags = _classify(text_for_tags)
    return Event(
        id=_make_id(item.get("url", ""), item["title"]),
        client_id=client_id,
        title=item["title"],
        what_happened=item.get("summary") or item["title"],
        why_important="",
        consequences=Consequences(),
        actions=[],
        bank_view="",
        ai_view="",
        sources=[Source(
            title=item["source"],
            url=item.get("url") or None,
            type="news",
        )],
        client_signals=[],
        relevance_score=0.0,
        tags=tags,
    )