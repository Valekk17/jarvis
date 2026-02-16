import os

GRAPH_FILE = "/root/.openclaw/workspace/memory/context_graph.md"
TASKS_DIR = "/root/.openclaw/workspace/memory/Tasks"

KILL_LIST = [
    "больничк", "бабуле", "бабулю", "инструкци", "написать, как закончит", "send report", 
    "скинуть код", "перевести 4000", "перевести 2", "сбросить настройки", "проверить две вкладки",
    "временно отключить", "пойти на работу", "войти в Google", "искать ошибку", "запускать приложение",
    "добавить карту", "добавить биллинг", "проверить фоновые", "сделать коллаж", "скачать и скинуть",
    "фотографию с Andrey", "знакомств"
]

def clean_file(filepath):
    if not os.path.exists(filepath): return
    with open(filepath) as f: lines = f.readlines()
    
    new_lines = []
    removed = 0
    for line in lines:
        if any(k.lower() in line.lower() for k in KILL_LIST):
            removed += 1
            continue
        new_lines.append(line)
        
    with open(filepath, "w") as f:
        f.writelines(new_lines)
    print(f"Cleaned {filepath}: -{removed}")

def main():
    clean_file(GRAPH_FILE)
    for f in os.listdir(TASKS_DIR):
        if f.endswith(".md"):
            clean_file(os.path.join(TASKS_DIR, f))

if __name__ == "__main__":
    main()
