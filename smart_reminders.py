#!/usr/bin/env python3
"""
Smart Reminder System - Контекстные напоминания на основе типа задачи
"""

import json
import re
from datetime import datetime, timedelta
from pathlib import Path

# Правила напоминаний по типам задач
REMINDER_RULES = {
    # Медицина - за неделю, за день, за час
    "medical": {
        "patterns": [
            r"врач|доктор|больниц|поликлиник|анализ|узи|прием|обследовани|терапевт|стоматолог",
            r"hospital|doctor|clinic|medical|checkup|appointment"
        ],
        "intervals": ["7d", "1d", "1h"],
        "importance": "high",
        "emoji": "🏥"
    },
    
    # Беременность - за 2 недели, за неделю, за день
    "pregnancy": {
        "patterns": [
            r"скрининг|узи.*беременн|консультац.*гинеколог|женск.*консульт",
            r"pregnancy|prenatal|obstetrician"
        ],
        "intervals": ["14d", "7d", "1d", "3h"],
        "importance": "critical",
        "emoji": "🤰"
    },
    
    # Встречи - за день, за час
    "meeting": {
        "patterns": [
            r"встреч|созвон|meeting|звонок|интервью|собрани",
            r"conference|call|zoom"
        ],
        "intervals": ["1d", "1h"],
        "importance": "medium",
        "emoji": "📅"
    },
    
    # Дедлайны - за 3 дня, за день, за 3 часа
    "deadline": {
        "patterns": [
            r"дедлайн|deadline|срок|сдать|отправить|deadline",
            r"due|submit|deliver"
        ],
        "intervals": ["3d", "1d", "3h"],
        "importance": "high",
        "emoji": "⏰"
    },
    
    # Оплата/налоги - за неделю, за 3 дня, за день
    "payment": {
        "patterns": [
            r"оплат|налог|счет|платеж|перевод|кварплат|комуналк",
            r"payment|bill|tax|invoice|rent"
        ],
        "intervals": ["7d", "3d", "1d"],
        "importance": "high",
        "emoji": "💳"
    },
    
    # Покупки - за день
    "shopping": {
        "patterns": [
            r"купить|заказать|забрать|магазин|покупк",
            r"buy|order|purchase|shop|pick.*up"
        ],
        "intervals": ["1d"],
        "importance": "low",
        "emoji": "🛒"
    },
    
    # Путешествия - за месяц, за неделю, за день
    "travel": {
        "patterns": [
            r"билет|рейс|поезд|самолет|вокзал|аэропорт|виз|паспорт",
            r"flight|train|ticket|visa|passport|airport|station"
        ],
        "intervals": ["30d", "7d", "1d", "3h"],
        "importance": "high",
        "emoji": "✈️"
    },
    
    # События - за неделю, за день
    "event": {
        "patterns": [
            r"день.*рожд|праздник|годовщин|свадьб|мероприят",
            r"birthday|anniversary|wedding|event|celebration"
        ],
        "intervals": ["7d", "1d"],
        "importance": "medium",
        "emoji": "🎉"
    },
    
    # По умолчанию - за день
    "default": {
        "patterns": [],
        "intervals": ["1d"],
        "importance": "medium",
        "emoji": "📌"
    }
}


def parse_interval(interval_str):
    """Парсит интервал вида '7d', '1h', '30m' в timedelta"""
    match = re.match(r'(\d+)([dhm])', interval_str)
    if not match:
        return None
    
    value = int(match.group(1))
    unit = match.group(2)
    
    if unit == 'd':
        return timedelta(days=value)
    elif unit == 'h':
        return timedelta(hours=value)
    elif unit == 'm':
        return timedelta(minutes=value)
    return None


def detect_task_type(text):
    """Определяет тип задачи по тексту"""
    text_lower = text.lower()
    
    for task_type, rule in REMINDER_RULES.items():
        if task_type == "default":
            continue
        
        for pattern in rule["patterns"]:
            if re.search(pattern, text_lower):
                return task_type, rule
    
    return "default", REMINDER_RULES["default"]


def format_reminder_message(task_text, deadline, interval_delta):
    """Форматирует текст напоминания"""
    now = datetime.now()
    time_until = deadline - now
    
    if time_until.days > 0:
        time_str = f"через {time_until.days} дн"
    elif time_until.seconds >= 3600:
        hours = time_until.seconds // 3600
        time_str = f"через {hours} ч"
    elif time_until.seconds >= 60:
        mins = time_until.seconds // 60
        time_str = f"через {mins} мин"
    else:
        time_str = "СЕЙЧАС"
    
    deadline_str = deadline.strftime("%d.%m в %H:%M")
    
    return f"⏰ Напоминание: {task_text}\n📅 {deadline_str} ({time_str})"


def create_smart_reminders(promise_text, deadline_dt):
    """
    Создаёт умные напоминания на основе типа задачи
    
    Returns: list of dict with {time, message, importance}
    """
    task_type, rule = detect_task_type(promise_text)
    
    reminders = []
    now = datetime.now()
    
    for interval_str in rule["intervals"]:
        interval_delta = parse_interval(interval_str)
        if not interval_delta:
            continue
        
        reminder_time = deadline_dt - interval_delta
        
        # Пропускаем прошедшие напоминания
        if reminder_time < now:
            continue
        
        message = format_reminder_message(promise_text, deadline_dt, interval_delta)
        
        reminders.append({
            "time": reminder_time.isoformat(),
            "message": message,
            "task_type": task_type,
            "importance": rule["importance"],
            "emoji": rule["emoji"],
            "deadline": deadline_dt.isoformat(),
            "interval": interval_str
        })
    
    return reminders


def generate_cron_schedule(reminder_time):
    """Генерирует cron schedule из datetime"""
    dt = datetime.fromisoformat(reminder_time) if isinstance(reminder_time, str) else reminder_time
    
    return {
        "kind": "at",
        "at": dt.isoformat() + "Z"
    }


# Примеры использования
if __name__ == "__main__":
    # Тест
    examples = [
        ("Сходить к врачу", datetime.now() + timedelta(days=10)),
        ("УЗИ скрининг", datetime.now() + timedelta(days=20)),
        ("Встреча с Лехой", datetime.now() + timedelta(days=2)),
        ("Оплатить квартплату", datetime.now() + timedelta(days=5)),
        ("Купить продукты", datetime.now() + timedelta(hours=6)),
    ]
    
    for text, deadline in examples:
        print(f"\n{'='*60}")
        print(f"Задача: {text}")
        print(f"Дедлайн: {deadline.strftime('%d.%m.%Y %H:%M')}")
        
        reminders = create_smart_reminders(text, deadline)
        
        task_type, rule = detect_task_type(text)
        print(f"Тип: {task_type} ({rule['importance']}) {rule['emoji']}")
        print(f"\nНапоминания ({len(reminders)}):")
        
        for r in reminders:
            reminder_dt = datetime.fromisoformat(r['time'])
            print(f"  - {reminder_dt.strftime('%d.%m %H:%M')} ({r['interval']})")
