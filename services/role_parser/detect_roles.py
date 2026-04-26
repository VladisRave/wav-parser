import re
import json
from pathlib import Path

from llm import generate_llm

MAX_DIALOG_CHARS = 6000

# ПРОМПТЫ
ROLE_PROMPT = """    Определи роль каждого Speaker в диалоге.

    Возможные роли:
    - USER — клиент, который звонит в компанию
    - ASSISTANT — сотрудник компании (оператор)
    - ROBOT — автоответчик или IVR-система

    ФОРМАТ ОТВЕТА:
    Верни только JSON:
    {"Speaker 0": "ROLE", "Speaker 1": "ROLE", ...}

    ОБЩИЕ ПРАВИЛА:
    - Количество Speaker в ответе должно совпадать с входом
    - Анализируй все реплики каждого Speaker
    - Без пояснений, только JSON

    ОПРЕДЕЛЕНИЕ РОЛЕЙ:

    ROBOT:
    - шаблонные системные фразы
    - "вы позвонили", "разговор может быть записан"
    - "ожидайте", "оставайтесь на линии"
    - "ваш номер в очереди"
    - "соединяю с оператором"

    ASSISTANT:
    - сотрудник компании
    - представляется как сотрудник или оператор
    - говорит: "я оператор", "служба поддержки"
    - задаёт вопросы и помогает решить проблему
    - ведёт диалог

    USER:
    - клиент, который обращается за услугой
    - говорит о своей проблеме
    - использует: "у меня", "мне нужно", "я не могу"
    - задаёт вопросы о тесте, оплате, доставке, результатах
    - не представляет себя сотрудником

    КРИТИЧЕСКОЕ ПРАВИЛО:
    - если человек говорит "я звоню от компании", "я оператор", "служба поддержки" - это ASSISTANT
    - если человек описывает свою проблему - это USER

    РАЗРЕШЕНИЕ КОНФЛИКТОВ:
    - если сначала похоже на автоответчик, но дальше идёт диалог - ASSISTANT

    ПРИМЕРЫ:

    Speaker 0: Алло
    Speaker 1: Меня зовут Денис, я звоню от компании
    Ответ: {"Speaker 0": "USER", "Speaker 1": "ASSISTANT"}

    Speaker 0: Служба поддержки, слушаю
    Speaker 1: У меня проблема
    Ответ: {"Speaker 0": "ASSISTANT", "Speaker 1": "USER"}

    Speaker 0: Вы позвонили в компанию. Ожидайте ответа от оператора
    Speaker 1: Здравствуйте, хочу вернуть деньги
    Ответ: {"Speaker 0": "ROBOT", "Speaker 1": "USER"}

    Теперь определи роли для следующего диалога:

    Ответ должен быть:
    - Только JSON
    - Без пояснений
    - Без markdown
    - Без ```json
"""

OPERATOR_USER_PROMPT = """Ты система контроля качества диалогов колл-центра медицинской лаборатории.

На входе — диалог с уже размеченными ролями:
USER, ASSISTANT, ROBOT.

Задача:
Проверить корректность разметки и определить:
True — диалог корректный
False — есть ошибки

КРИТЕРИИ FALSE:

1. Ошибка ролей:
- USER ведёт себя как оператор (представляется, говорит "я оператор", "служба поддержки", "звоню вам от компании")
- ASSISTANT ведёт себя как клиент (жалобы, "у меня проблема", "мой тест", "верните деньги")

2. Невозможность понять роли:
- роли противоречат друг другу
- диалог выглядит случайно размеченным

3. ASSISTANT не выполняет роль оператора:
- не отвечает на вопросы
- не разъясняет проблему
- не помогает пользователю

КРИТЕРИИ TRUE:

USER:
- задаёт вопросы о тесте, результатах, доставке, оплате
- может обсуждать генетику, родословную, семейную историю
- описывает свою проблему

ASSISTANT:
- сотрудник лаборатории
- отвечает на вопросы
- уточняет данные
- помогает решить проблему
- ведёт диалог

ВАЖНО:
- обсуждение семьи, генетики, родословной — НОРМАЛЬНЫЙ USER сценарий
- не считать ошибкой

ПРАВИЛА:
- не суди по первой фразе
- анализируй весь диалог
- роль определяется поведением, а не приветствием

ФОРМАТ ОТВЕТА:
True или False (одно слово)
"""

QUALITY_PROMPT = """Ты система контроля качества для генетической лаборатории.

На входе — только реплики пациента (USER).

Задача:
решить — оставить диалог (True) или отбросить (False)

FALSE ЕСЛИ:

1. Чужой тест:
- "тест моего сына/дочери/мужа/жены/друга"
- "это не мой анализ"
- "перепутали анализ"
- "результат другого человека"
- "я за другого звоню"

ИСКЛЮЧЕНИЕ:
если это цитата другого человека — не считать ошибкой

2. Смена рода во время разговора:
- "я заказал" -> "я заказала"
- "я сдал" -> "я сдала"
- любая смена рода у одного человека

3. Путаница с личностью:
- "это мой тест?"
- "возможно перепутали"
- "не уверен что мои результаты"

TRUE ВСЕГДА:

4. Семья и генеалогия (разрешено):
- обсуждение родословной
- семейное дерево
- наследственные заболевания
- рассказы про родственников (родителей, детей, бабушек, дедушек)

ВАЖНО:
- семейная информация не является причиной для False
- даже если обсуждаются родственники — это нормальный сценарий
- исключение только смена рода или чужой тест

ПРАВИЛА:
- анализируй весь текст
- только реплики пациента
- если не уверен → True

ФОРМАТ:
True или False (одно слово)
"""

def _clean_json(text: str) -> str:
    """Очистка вывода LLM от markdown и лишних пробелов."""
    if not isinstance(text, str):
        return ""
    text = text.strip()
    text = re.sub(r"^```json\s*", "", text)
    text = re.sub(r"^```\s*", "", text)
    text = re.sub(r"\s*```$", "", text)
    return text.strip()

def validate_operator_user(dialog_text: str, roles_dict: dict) -> bool:
    """Проверка корректности ролей USER и ASSISTANT."""
    labeled_dialog = []
    for line in dialog_text.splitlines():
        line = line.strip()
        if not line:
            continue
        for speaker, role in roles_dict.items():
            if line.startswith(f"{speaker}:"):
                labeled_dialog.append(f"{role}: {line.split(':', 1)[1].strip()}")
                break

    labeled_text = "\n".join(labeled_dialog)
    prompt = OPERATOR_USER_PROMPT + "\n\nДиалог:\n" + labeled_text

    messages = [
        {"role": "system", "content": "Ты проверяешь корректность ролей. Отвечай только True или False."},
        {"role": "user", "content": prompt}
    ]

    response = generate_llm(messages)
    print("DEBUG response:", response)
    cleaned = _clean_json(response).strip().lower()
    return cleaned == "true"

def detect_roles(dialog_text: str):
    """Определение ролей спикеров в диалоге."""
    if len(dialog_text) > MAX_DIALOG_CHARS:
        dialog_text = dialog_text[:MAX_DIALOG_CHARS]

    prompt = ROLE_PROMPT + "\n\nТеперь определи роли для следующего диалога:\n" + dialog_text

    messages = [
        {"role": "system", "content": "Ты строго классифицируешь роли в диалоге. Отвечай только JSON."},
        {"role": "user", "content": prompt}
    ]

    response = generate_llm(messages)
    cleaned = _clean_json(response)

    try:
        data = json.loads(cleaned)
        # Проверяем, что все значения — допустимые роли
        for k, v in data.items():
            if v not in ("USER", "ASSISTANT", "ROBOT"):
                return {}
        return data
    except Exception:
        return {}

def quality_control(user_text: str) -> bool:
    """Проверка качества текста пациента."""
    if len(user_text) > MAX_DIALOG_CHARS:
        user_text = user_text[:MAX_DIALOG_CHARS]

    prompt = QUALITY_PROMPT + "\n\nТекст для проверки:\n" + user_text

    messages = [  # <-- ИСПРАВЛЕНО: убрана лишняя буква t
        {"role": "system", "content": "Ты фильтруешь данные для генетического анализа. Отвечай только True или False."},
        {"role": "user", "content": prompt}
    ]

    response = generate_llm(messages)
    cleaned = _clean_json(response).strip().lower()
    if cleaned == "true":
        return True
    elif cleaned == "false":
        return False
    else:
        # Неожиданный ответ – считаем False, чтобы не пропускать мусор
        print(f"  ВНИМАНИЕ: quality_control вернул '{cleaned}', считаем False")
        return False

def extract_user_text(txt_content: str, user_speaker_label: str) -> str:
    """Извлекает все реплики указанного спикера."""
    pattern = rf"^{re.escape(user_speaker_label)}:\s*(.*?)$"
    lines = txt_content.splitlines()
    user_lines = []
    for line in lines:
        match = re.match(pattern, line.strip())
        if match:
            user_lines.append(match.group(1).strip())
    return "\n".join(user_lines)

def save_roles(output_file: Path, roles_dict: dict):
    output_file.parent.mkdir(parents=True, exist_ok=True)
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(roles_dict, f, ensure_ascii=False, indent=2)
    print(f"Роли сохранены: {output_file}")