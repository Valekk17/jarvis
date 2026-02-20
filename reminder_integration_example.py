#!/usr/bin/env python3
"""
Пример интеграции smart_reminders в entity_collector.py
"""

from smart_reminders import create_smart_reminders, generate_cron_schedule
from datetime import datetime
import subprocess
import json


def create_cron_reminder(reminder_data):
    """Создаёт cron job для напоминания через OpenClaw"""
    
    cron_job = {
        "name": f"reminder-{reminder_data['task_type']}-{reminder_data['time'][:10]}",
        "schedule": generate_cron_schedule(reminder_data['time']),
        "sessionTarget": "main",
        "payload": {
            "kind": "systemEvent",
            "text": reminder_data['message']
        }
    }
    
    # Создание через openclaw cron add
    cmd = [
        "openclaw", "cron", "add",
        "--job", json.dumps(cron_job)
    ]
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    return result.returncode == 0


def process_promise_with_smart_reminders(promise):
    """
    Обработка promise из entity_collector с созданием умных напоминаний
    
    promise = {
        "promise": "Сходить к врачу",
        "deadline": "2026-03-15T10:00:00",
        "promiser": "Valek",
        "promisee": "Arisha"
    }
    """
    
    # Парсим дедлайн
    deadline_dt = datetime.fromisoformat(promise['deadline'].replace('Z', '+00:00'))
    
    # Генерируем умные напоминания
    reminders = create_smart_reminders(promise['promise'], deadline_dt)
    
    print(f"📋 Задача: {promise['promise']}")
    print(f"📅 Дедлайн: {deadline_dt.strftime('%d.%m.%Y %H:%M')}")
    print(f"⏰ Создано напоминаний: {len(reminders)}")
    
    # Создаём cron jobs
    created = 0
    for reminder in reminders:
        if create_cron_reminder(reminder):
            created += 1
            reminder_time = datetime.fromisoformat(reminder['time'])
            print(f"  ✓ {reminder['emoji']} {reminder_time.strftime('%d.%m %H:%M')} ({reminder['interval']})")
        else:
            print(f"  ✗ Ошибка создания: {reminder['time']}")
    
    return created


# Пример использования в entity_collector.py
if __name__ == "__main__":
    # Симуляция promise из Gemini response
    example_promise = {
        "promise": "Сходить на УЗИ скрининг",
        "deadline": "2026-03-15T10:00:00",
        "promiser": "Valek",
        "promisee": "Arisha",
        "status": "pending"
    }
    
    process_promise_with_smart_reminders(example_promise)
