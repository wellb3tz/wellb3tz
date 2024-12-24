from flask import Flask
import requests
import random
import time
import urllib3
import json
from datetime import datetime, UTC  # Добавляем UTC

# Отключаем предупреждение о незащищенном соединении
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

TELEGRAM_API_TOKEN = '7895202892:AAExf3tcGSTcxa8FYb8114iTZ0b9gCVScvY'
TELEGRAM_API_URL = f'https://api.telegram.org/bot{TELEGRAM_API_TOKEN}/'
INVENTORY_FILE = 'user_collections.json'

response = requests.get(TELEGRAM_API_URL + 'getUpdates', verify=False)
updates = response.json()

# Item database
items = [
    # Common Items (Total: 70%)
    {"name": "🧱 Ordinary Brick", "chance": 0.25},
    {"name": "🪵 Wood Log", "chance": 0.15},
    {"name": "🪨 Stone", "chance": 0.12},
    {"name": "🧶 Thread", "chance": 0.10},
    {"name": "🌾 Wheat", "chance": 0.08},
    
    # Uncommon Items (Total: 20%)
    {"name": "⚒️ Rusty Tools", "chance": 0.06},
    {"name": "🧪 Strange Potion", "chance": 0.05},
    {"name": "📜 Ancient Scroll", "chance": 0.04},
    {"name": "🔑 Bronze Key", "chance": 0.03},
    {"name": "🎭 Mysterious Mask", "chance": 0.02},
    
    # Rare Items (Total: 8%)
    {"name": "⚔️ Steel Sword", "chance": 0.025},
    {"name": "🛡️ Knight's Shield", "chance": 0.02},
    {"name": "💎 Blue Crystal", "chance": 0.015},
    {"name": "🗝️ Silver Key", "chance": 0.01},
    {"name": "🎪 Magic Lamp", "chance": 0.01},
    
    # Epic Items (Total: 1.7%)
    {"name": "🗡️ Dragon Slayer", "chance": 0.005},
    {"name": "👑 Royal Crown", "chance": 0.004},
    {"name": "🌟 Star Fragment", "chance": 0.003},
    {"name": "🔮 Oracle's Orb", "chance": 0.003},
    {"name": "⚜️ Noble's Crest", "chance": 0.002},
    
    # Legendary Items (Total: 0.29%)
    {"name": "🏆 Champion's Trophy", "chance": 0.001},
    {"name": "💫 Cosmic Dust", "chance": 0.001},
    {"name": "🌈 Rainbow Shard", "chance": 0.0005},
    {"name": "⚡ Thunder Crystal", "chance": 0.0004},
    {"name": "🔱 Poseidon's Trident", "chance": 0.0001},
    
    # Mythical Items (Total: 0.01%)
    {"name": "🌌 Galaxy Fragment", "chance": 0.00005},
    {"name": "🎇 Phoenix Feather", "chance": 0.00003},
    {"name": "💠 Eternity Diamond", "chance": 0.00001},
    {"name": "✨ Destiny Star", "chance": 0.00001}
]

# Функция для загрузки инвентаря из файла
def load_collections():
    try:
        with open(INVENTORY_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        return {}
    except json.JSONDecodeError:
        print("Error reading inventory file. Creating backup and starting fresh.")
        # Создаем резервную копию поврежденного файла
        from shutil import copy2
        backup_file = f'user_collections_backup_{int(time.time())}.json'
        copy2(INVENTORY_FILE, backup_file)
        return {}

# Функция для сохранения инвентаря в файл
def save_collections(collections):
    with open(INVENTORY_FILE, 'w', encoding='utf-8') as f:
        json.dump(collections, f, ensure_ascii=False, indent=2)

# Загружаем сохраненные коллекции при запуске
user_collections = load_collections()

def send_message(chat_id, text):
    response = requests.post(
        TELEGRAM_API_URL + 'sendMessage',
        json={
            'chat_id': chat_id,
            'text': text
        },
        verify=False
    )
    return response.json()

def send_welcome(chat_id):
    welcome_message = """
🎮 Welcome to 'Unum ad X'! 🎲

Test your luck and discover rare treasures in this collecting game!

🎯 Available Commands:
/loot - Find new items (60s cooldown)
/collection - View your collection
/help - Show this help message

⚔️ Rarity Levels:
Common - 70%
Uncommon - 20%
Rare - 8%
Epic - 1.7%
Legendary - 0.29%
Mythical - 0.01%

Good luck on your adventure! 🍀
"""
    send_message(chat_id, welcome_message)

def loot_item(chat_id, user_id):
    user_id = str(user_id)  # Конвертируем ID в строку для JSON
    user_collections.setdefault(user_id, {
        'inventory': {},
        'last_loot': None
    })

    # Проверяем время последнего лута (можно настроить задержку)
    current_time = datetime.now(UTC).timestamp()
    last_loot = user_collections[user_id]['last_loot']
    
    if last_loot and current_time - last_loot < 3:  # 60 секунд задержки
        remaining = int(3 - (current_time - last_loot))
        send_message(chat_id, f"⏳ Please wait {remaining} seconds before next loot attempt!")
        return

    # Generate an item
    roll = random.random()
    cumulative_chance = 0

    for item in items:
        cumulative_chance += item["chance"]
        if roll < cumulative_chance:
            user_collections[user_id]['inventory'].setdefault(item["name"], 0)
            user_collections[user_id]['inventory'][item["name"]] += 1
            user_collections[user_id]['last_loot'] = current_time
            
            # Сохраняем изменения
            save_collections(user_collections)
            
            send_message(chat_id, f"🎉 You received: {item['name']}!\nChance: {item['chance']*100:.4f}%")
            return

    send_message(chat_id, "😢 Unfortunately, you found nothing rare. Try again!")

def show_collection(chat_id, user_id):
    user_id = str(user_id)
    if user_id not in user_collections or not user_collections[user_id].get('inventory'):
        send_message(chat_id, "You don't have any items yet. Type /loot to start collecting!")
        return

    inventory = user_collections[user_id]['inventory']
    
    # Сортируем предметы по редкости (используя словарь шансов)
    item_chances = {item['name']: item['chance'] for item in items}
    sorted_items = sorted(inventory.items(), 
                         key=lambda x: item_chances.get(x[0], 0))

    response = "🗂 Your Collection:\n\n"
    for item_name, count in sorted_items:
        response += f"{item_name} — {count} pcs\n"
    
    # Добавляем статистику
    total_items = sum(inventory.values())
    unique_items = len(inventory)
    response += f"\n📊 Statistics:\n"
    response += f"Total items: {total_items}\n"
    response += f"Unique items: {unique_items}/{len(items)}"
    
    send_message(chat_id, response)

def send_help(chat_id):
    send_message(chat_id, """📜 Commands:
/start — Start the game
/loot — Try your luck to find an item (60s cooldown)
/collection — View your collection
/help — Get help and information
""")

def main():
    print("Bot started...")
    offset = None
    
    while True:
        try:
            params = {'timeout': 30}
            if offset:
                params['offset'] = offset

            response = requests.get(TELEGRAM_API_URL + 'getUpdates', params=params, verify=False)
            updates = response.json()['result']

            for update in updates:
                offset = update['update_id'] + 1

                if 'message' not in update:
                    continue

                message = update['message']
                chat_id = message['chat']['id']
                
                if 'text' not in message:
                    continue
                    
                text = message['text']

                # Handle commands
                if text == '/start':
                    send_welcome(chat_id)
                elif text == '/loot':
                    loot_item(chat_id, message['from']['id'])
                elif text == '/collection':
                    show_collection(chat_id, message['from']['id'])
                elif text == '/help':
                    send_help(chat_id)

        except Exception as e:
            print(f"Error occurred: {e}")
            time.sleep(5)
            continue

if __name__ == '__main__':
    main()