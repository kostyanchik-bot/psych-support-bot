# analysis.py

def analyze_responses(responses: dict):
    score = 0

    stress_map = {
        "Почти всегда": 5,
        "Часто": 4,
        "Иногда": 3,
        "Редко": 2,
        "Никогда": 1
    }

    emotional_difficulty_map = {
        "Очень сложно": 5,
        "Скорее сложно": 4,
        "Нейтрально": 3,
        "Скорее легко": 2,
        "Очень легко": 1
    }

    score += stress_map.get(responses.get("stress_frequency", "Иногда"), 3)
    score += emotional_difficulty_map.get(responses.get("emotional_difficulty", "Нейтрально"), 3)

    symptoms = responses.get("symptoms", [])
    if "Мысли о самоповреждении" in symptoms:
        return {"level": "Критический", "score": 100}
    
    score += len(symptoms)

    return {
        "level": "Высокий" if score >= 10 else "Средний" if score >= 6 else "Низкий",
        "score": score
    }
