from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import random
import time
import urllib3
import json
from datetime import datetime, UTC
from items_database import items
  

app = Flask(__name__)
CORS(app)  # Добавляем поддержку CORS

# Отключаем предупреждение о незащищенном соединении
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

TELEGRAM_API_TOKEN = '7895202892:AAExf3tcGSTcxa8FYb8114iTZ0b9gCVScvY'
TELEGRAM_API_URL = f'https://api.telegram.org/bot{TELEGRAM_API_TOKEN}/'
INVENTORY_FILE = 'user_collections.json'

# Функция для загрузки инвентаря из файла
def load_collections():
    try:
        with open(INVENTORY_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        return {}
    except json.JSONDecodeError:
        print("Error reading inventory file. Creating backup and starting fresh.")
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

def send_message(chat_id, text, reply_markup=None):
    data = {
        'chat_id': chat_id,
        'text': text
    }
    if reply_markup:
        data['reply_markup'] = reply_markup
    
    response = requests.post(
        TELEGRAM_API_URL + 'sendMessage',
        json=data,
        verify=False
    )
    return response.json()

def send_welcome(chat_id):
    welcome_message = """
🎮 Welcome to 'Unum ad X'! 🎲

Test your luck and discover rare treasures in this collecting game!

🎯 Available Commands:
/loot - Find new items
/collection - View your collection
/miniapp - Open Mini App
/help - Show this help message

Good luck on your adventure! 🍀
"""
    keyboard = {
        "inline_keyboard": [[{
            "text": "🎮 Open Mini App",
            "web_app": {"url": "https://wellb3tz.github.io/wellb3tz/"}
        }]]
    }
    send_message(chat_id, welcome_message, keyboard)

def loot_item(chat_id, user_id):
    user_id = str(user_id)
    user_collections.setdefault(user_id, {
        'inventory': {},
        'last_loot': None
    })

    current_time = datetime.now(UTC).timestamp()
    last_loot = user_collections[user_id]['last_loot']
    
    if last_loot and current_time - last_loot < 1:
        remaining = int(1 - (current_time - last_loot))
        send_message(chat_id, f"⏳ Please wait {remaining} seconds before next loot attempt!")
        return False, "Please wait before next loot attempt!"

    roll = random.random()
    cumulative_chance = 0

    for item in items:
        cumulative_chance += item["chance"]
        if roll < cumulative_chance:
            user_collections[user_id]['inventory'].setdefault(item["name"], 0)
            user_collections[user_id]['inventory'][item["name"]] += 1
            user_collections[user_id]['last_loot'] = current_time
            
            save_collections(user_collections)
            
            message = f"🎉 You received: {item['name']}!\nChance: {item['chance']*100:.4f}%"
            send_message(chat_id, message)
            return True, {"item_name": item["name"], "chance": item["chance"]}

    send_message(chat_id, "😢 Unfortunately, you found nothing rare. Try again!")
    return False, "No item found"

def show_collection(chat_id, user_id):
    user_id = str(user_id)
    if user_id not in user_collections or not user_collections[user_id].get('inventory'):
        send_message(chat_id, "You don't have any items yet. Type /loot to start collecting!")
        return

    inventory = user_collections[user_id]['inventory']
    
    item_chances = {item['name']: item['chance'] for item in items}
    sorted_items = sorted(inventory.items(), 
                         key=lambda x: item_chances.get(x[0], 0))

    response = "🗂 Your inventory:\n\n"
    for item_name, count in sorted_items:
        response += f"{item_name} — {count} pcs\n"
    
    total_items = sum(inventory.values())
    unique_items = len(inventory)
    response += f"\n📊 Statistics:\n"
    response += f"Total items: {total_items}\n"
    response += f"Unique items: {unique_items}/{len(items)}"
    
    send_message(chat_id, response)

def send_help(chat_id):
    help_message = """📜 Commands:
/start — Start the game
/loot — Try your luck to find an item
/inventory — View your inventory
/miniapp — Open Mini App interface
/help — Get help and information
"""
    keyboard = {
        "inline_keyboard": [[{
            "text": "🎮 Open Mini App",
            "web_app": {"url": "https://wellb3tz.github.io/wellb3tz/"}
        }]]
    }
    send_message(chat_id, help_message, keyboard)

def setup_mini_app(chat_id):
    keyboard = {
        "inline_keyboard": [[{
            "text": "🎮 Open Mini App",
            "web_app": {"url": "https://wellb3tz.github.io/wellb3tz/"}
        }]]
    }
    send_message(chat_id, "Click the button below to open the Mini App:", keyboard)

@app.route('/loot', methods=['POST'])
def web_loot():
    try:
        data = request.json
        user_id = str(data['user_id'])
        chat_id = data.get('chat_id', user_id)  # Используем user_id как chat_id, если не указан
        
        success, result = loot_item(chat_id, user_id)
        
        if isinstance(result, dict):
            return jsonify(result)
        else:
            return jsonify({'error': result}), 429 if "wait" in result.lower() else 404

    except Exception as e:
        print(f"Error in web_loot: {e}")
        return jsonify({'error': str(e)}), 500

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

                if 'message' in update:
                    message = update['message']
                    chat_id = message['chat']['id']
                    user_id = message['from']['id']

                    # Обработка web_app_data
                    if 'web_app_data' in message:
                        print(f"Received web_app_data: {message['web_app_data']}")
                        data = message['web_app_data']['data']
                        if data == '/loot':
                            print(f"Processing loot command from web_app for user {user_id}")
                            loot_item(chat_id, user_id)
                        continue

                    # Обработка текстовых команд
                    if 'text' in message:
                        text = message['text']
                        if text == '/start':
                            send_welcome(chat_id)
                        elif text == '/loot':
                            loot_item(chat_id, user_id)
                        elif text == '/inventory':
                            show_collection(chat_id, user_id)
                        elif text == '/help':
                            send_help(chat_id)
                        elif text == '/miniapp':
                            setup_mini_app(chat_id)

        except Exception as e:
            print(f"Error in main loop: {e}")
            time.sleep(5)
            continue

if __name__ == '__main__':
    # Запускаем Flask сервер и бота в разных потоках
    from threading import Thread
    from waitress import serve
    
    # Запускаем бота в отдельном потоке
    bot_thread = Thread(target=main)
    bot_thread.daemon = True
    bot_thread.start()
    
    # Запускаем Flask сервер через waitress
    print("Starting Flask server...")
    serve(app, host='0.0.0.0', port=5000)