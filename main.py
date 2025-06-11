# main.py

from survey import survey_questions
from analysis import analyze_responses
from recommendations import get_recommendations

def run_assessment():
    responses = {}

    print("Добро пожаловать в опрос по психологическому состоянию.\n")

    for section in survey_questions:
        print(f"--- {section['section']} ---")
        for q in section['questions']:
            print(q['text'])
            for i, option in enumerate(q['options']):
                print(f"{i + 1}. {option}")
            
            if q.get("multi"):
                choice = input("Введите номера через запятую: ")
                selected = [q['options'][int(i.strip()) - 1] for i in choice.split(',') if i.strip().isdigit()]
                responses[q['id']] = selected
            else:
                choice = input("Введите номер: ")
                selected = q['options'][int(choice.strip()) - 1]
                responses[q['id']] = selected
        print()

    print("Анализ ваших ответов...")
    analysis_result = analyze_responses(responses)
    print(f"Уровень тревожности: {analysis_result['level']}")

    print("\nРекомендации:")
    for rec in get_recommendations(analysis_result):
        print(f"- {rec}")

if __name__ == "__main__":
    run_assessment()
