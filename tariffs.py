# tariffs.py

AGENTS = {
    "⚡ Быстрый (YandexGPT 5 Lite)": "fvtp590q2aec9sirbfd4",
    "⚖️ Стандарт (YandexGPT 5 Pro)": "fvtan6sh64v0qptovitu",
    "🧠 Умный (YandexGPT 5.1 Pro)": "fvttfdflmeapltgq6q3c",
}

TARIFFS = {
    "free": {
        "generations_per_day": 2,
        "available_agents": ["⚡ Быстрый (YandexGPT 5 Lite)"],
        "price": 0
    },
    "basic": {
        "generations_per_day": 5,
        "available_agents": ["⚡ Быстрый (YandexGPT 5 Lite)", "⚖️ Стандарт (YandexGPT 5 Pro)"],
        "price": 299
    },
    "pro": {
        "generations_per_day": 8,
        "available_agents": list(AGENTS.keys()),
        "price": 599
    }
}