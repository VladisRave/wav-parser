import re
import json
from pathlib import Path

from llm import generate_llm

MAX_DIALOG_CHARS = 6000

# ПРОМПТЫ
ROLE_PROMPT = """
Задача: Определи роль каждого Speaker в диалоге.

Возможные роли:
- USER — клиент, звонит в компанию, решает свою проблему.
- ASSISTANT — сотрудник компании (оператор), помогает клиенту.
- ROBOT — автоответчик или IVR-система.

Правила определения для каждой роли.

Шаблонные фразы ROBOT: 
- «вы позвонили», «разговор может быть записан»
- «ожидайте», «оставайтесь на линии», «ваш номер в очереди»
- «соединяю с оператором»

Шаблонные фразы ASSISTANT:
- Представляется оператором: «я оператор», «служба поддержки»
- Задаёт вопросы, помогает решить проблему, ведёт диалог
- Отвечает на запросы клиента

Шаблонные фразы USER:
- Описывает проблему: «у меня», «мне нужно», «я не могу»
- Задаёт вопросы о тесте, оплате, доставке, результатах
- **Может просить робота или оператора:** «свяжите с оператором», «переключите на оператора»
- Никогда не представляется сотрудником компании

Критические правила:
- Фразы «я звоню от компании», «я оператор», «служба поддержки» - ASSISTANT
- Описание проблемы клиентом -> USER
- Если в начале диалог похож на ROBOT, но дальше идёт живой диалог -> ASSISTANT

Список примеров:
Пример 1
Speaker 0: Алло  
Speaker 1: Меня зовут Денис, я звоню от компании  
Ответ: {"Speaker 0": "USER", "Speaker 1": "ASSISTANT"}

Пример 2
Speaker 0: Служба поддержки, слушаю  
Speaker 1: У меня проблема  
Ответ: {"Speaker 0": "ASSISTANT", "Speaker 1": "USER"}

Пример 3
Speaker 0: Вы позвонили в компанию. Ожидайте ответа от оператора  
Speaker 1: Здравствуйте, хочу вернуть деньги  
Ответ: {"Speaker 0": "ROBOT", "Speaker 1": "USER"}

Пример 4 (запрос соединить с оператором)
Speaker 0: Повторите, что вы хотите, чтобы я связал вас с оператором.  
Speaker 1: Да  
Ответ: {"Speaker 0": "USER", "Speaker 1": "ROBOT"}

Ответ только в JSON
"""

COMBINED_VALIDATION_PROMPT = """
Ты система контроля качества диалогов колл-центра медицинской лаборатории.

На вход подаются:
1. Диалог с уже размеченными ролями (USER, ASSISTANT, ROBOT)
2. Отдельно — только реплики USER (пациента)

Твоя задача — выполнить две независимые проверки и вернуть JSON-объект с результатами.

ПРОВЕРКА 1: КОРРЕКТНОСТЬ РОЛЕЙ USER/ASSISTANT (результат: roles_valid)

Верни true, если:
- USER задаёт вопросы о тесте, результатах, доставке, оплате, семейную историю, описывает свою проблему.
- ASSISTANT — сотрудник лаборатории, отвечает на вопросы, уточняет данные, помогает решить проблему, ведёт диалог.
- USER может просить соединить с оператором — это норма.

Верни false, если:
- USER ведёт себя как оператор: представляется, говорит "я оператор", "служба поддержки", "звоню вам от компании".
- ASSISTANT ведёт себя как клиент: жалуется, говорит "у меня проблема", "мой тест", "верните деньги".
- Роли противоречат друг другу.

Главное - не суди по первой фразе, анализируй весь диалог.

ПРОВЕРКА 2: КАЧЕСТВО ТЕКСТА USER (результат: quality_ok)

Анализируй только реплики USER.

Верни false, если ЕСТЬ ХОТЯ БЫ ОДНО ИЗ:
1. Чужой тест: "тест моего сына/дочери/мужа/жены/друга", "это не мой анализ", "результат другого человека", "я за другого звоню".
2. Смена рода у одного человека в течение диалога: "я заказал" -> "я заказала", "я сдал" -> "я сдала".
3. Путаница с личностью: "это мой тест?", "возможно перепутали", "не уверен, что мои результаты".

Верни true в остальных случаях, включая:
- Обсуждение родословной, семейного дерева, наследственных заболеваний, рассказы о родственниках.
- Решение проблем с регистрацией пробирки, сбора генетического материала или контактной информации.
- Если не уверен — ставь true.

ФОРМАТ ОТВЕТА

Верни только JSON, строго по схеме:
{"roles_valid": true/false, "quality_ok": true/false}

Примеры:
{"roles_valid": true, "quality_ok": true}
{"roles_valid": false, "quality_ok": true}
{"roles_valid": true, "quality_ok": false}
{"roles_valid": false, "quality_ok": false}
"""


# JSON SCHEMA ДЛЯ ВАЛИДАЦИИ (строгий режим)
VALIDATION_RESPONSE_FORMAT = {
    "type": "json_schema",
    "json_schema": {
        "name": "validation_result",
        "strict": True,
        "schema": {
            "type": "object",
            "properties": {
                "roles_valid": {"type": "boolean"},
                "quality_ok": {"type": "boolean"}
            },
            "required": ["roles_valid", "quality_ok"],
            "additionalProperties": False
        }
    }
}


async def detect_roles(dialog_text: str) -> dict:
    if len(dialog_text) > MAX_DIALOG_CHARS:
        dialog_text = dialog_text[:MAX_DIALOG_CHARS]
    prompt = ROLE_PROMPT + "\n\n" + dialog_text
    messages = [
        {"role": "system", "content": "Ты классифицируешь роли. Ответь только JSON, без пояснений."},
        {"role": "user", "content": prompt}
    ]
    response = await generate_llm(messages, max_new_tokens=256)
    try:
        data = json.loads(response)
        # фильтруем только спикеров с допустимыми ролями
        filtered = {k: v for k, v in data.items() if v in ("USER", "ASSISTANT", "ROBOT")}
        return filtered
    except:
        return {}

async def validate_combined(dialog_text: str, roles_dict: dict, user_text: str) -> tuple[bool, bool]:
    # строим размеченный диалог
    labeled_lines = []
    for line in dialog_text.splitlines():
        line = line.strip()
        if not line:
            continue
        for speaker, role in roles_dict.items():
            if line.startswith(f"{speaker}:"):
                labeled_lines.append(f"{role}: {line.split(':', 1)[1].strip()}")
                break
    labeled_dialog = "\n".join(labeled_lines)

    if len(labeled_dialog) > MAX_DIALOG_CHARS:
        labeled_dialog = labeled_dialog[:MAX_DIALOG_CHARS]
    if len(user_text) > MAX_DIALOG_CHARS:
        user_text = user_text[:MAX_DIALOG_CHARS]

    prompt = COMBINED_VALIDATION_PROMPT + f"""

Диалог с ролями:
{labeled_dialog}

Реплики USER:
{user_text}
"""
    messages = [
        {"role": "system", "content": "Ты валидатор. Отвечай только JSON."},
        {"role": "user", "content": prompt}
    ]
    response = await generate_llm(messages, max_new_tokens=128, response_format=VALIDATION_RESPONSE_FORMAT)
    try:
        data = json.loads(response)
        return data.get("roles_valid", False), data.get("quality_ok", False)
    except:
        return False, False

def extract_user_text(txt_content: str, user_speaker_label: str) -> str:
    pattern = rf"^{re.escape(user_speaker_label)}:\s*(.*?)$"
    lines = txt_content.splitlines()
    user_lines = []
    for line in lines:
        m = re.match(pattern, line.strip())
        if m:
            user_lines.append(m.group(1).strip())
    return "\n".join(user_lines)

def save_roles(output_file: Path, roles_dict: dict):
    output_file.parent.mkdir(parents=True, exist_ok=True)
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(roles_dict, f, ensure_ascii=False, indent=2)
    print(f"  Роли сохранены: {output_file}")