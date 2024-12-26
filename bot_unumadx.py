from flask import Flask, request, jsonify
from flask_cors import CORS
import telebot
import random
import time
import json
from datetime import datetime, UTC
from threading import Thread
from waitress import serve
from items_database import items
import hashlib
import hmac
import base64


# Инициализация Flask и Telegram бота
app = Flask(__name__)
CORS(app, resources={
    r"/*": {
        "origins": ["https://wellb3tz.github.io"],
        "methods": ["GET", "POST", "OPTIONS"],
        "allow_headers": ["Content-Type", "Accept", "Origin"],
    }
})

BOT_TOKEN = '7895202892:AAExf3tcGSTcxa8FYb8114iTZ0b9gCVScvY'
bot = telebot.TeleBot(BOT_TOKEN)

# Загрузка коллекций пользователей
def load_collections():
    try:
        with open('user_collections.json', 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return {}

# Сохранение коллекций пользователей
def save_collections(collections):
    with open('user_collections.json', 'w') as f:
        json.dump(collections, f, indent=4)

def verify_telegram_data(init_data, bot_token):
    try:
        # Разбираем init_data
        data_check_string = '\n'.join([
            f"{key}={value}"
            for key, value in sorted(parse_init_data(init_data).items())
            if key != 'hash'
        ])
        
        # Создаем secret key из токена бота
        secret_key = hmac.new(
            'WebAppData'.encode(),
            bot_token.encode(),
            hashlib.sha256
        ).digest()
        
        # Вычисляем хеш
        data_hash = hmac.new(
            secret_key,
            data_check_string.encode(),
            hashlib.sha256
        ).hexdigest()
        
        return data_hash == parse_init_data(init_data).get('hash', '')
    except Exception as e:
        print(f"Error verifying Telegram data: {e}")
        return False

def parse_init_data(init_data):
    try:
        return dict(param.split('=') for param in init_data.split('&'))
    except:
        return {}
    
# Словарь для хранения времени последнего лута
last_loot_time = {}
COOLDOWN_SECONDS = 1

def get_random_item():
    """Выбирает случайный предмет на основе шансов"""
    rand = random.random()
    current_prob = 0
    
    for item in items:
        current_prob += item["chance"]
        if rand <= current_prob:
            return {
                "item_name": item["name"],
                "chance": item["chance"]
            }
    
    # Если почему-то ничего не выбрано, вернуть первый предмет (с наибольшим шансом)
    return {
        "item_name": items[0]["name"],
        "chance": items[0]["chance"]
    }

def can_loot(user_id):
    """Проверяет, может ли пользователь получить лут"""
    if user_id not in last_loot_time:
        return True
    
    time_passed = (datetime.now(UTC) - last_loot_time[user_id]).total_seconds()
    return time_passed >= COOLDOWN_SECONDS

def get_remaining_time(user_id):
    """Возвращает оставшееся время до следующего лута"""
    if user_id not in last_loot_time:
        return 0
    
    time_passed = (datetime.now(UTC) - last_loot_time[user_id]).total_seconds()
    remaining = COOLDOWN_SECONDS - time_passed
    return max(0, remaining)

def format_time(seconds):
    """Форматирует время в читаемый формат"""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    return f"{hours}h {minutes}m"

def add_to_collection(user_id, item):
    """Добавляет предмет в коллекцию пользователя"""
    collections = load_collections()
    
    if user_id not in collections:
        collections[user_id] = []
    
    item_data = {
        "name": item["item_name"],
        "rarity": item["rarity"],
        "obtained_at": datetime.now(UTC).isoformat()
    }
    
    collections[user_id].append(item_data)
    save_collections(collections)

def get_rarity(chance):
    """Определяет редкость предмета по шансу"""
    if chance >= 0.08:  # 8% и выше
        return "Common"
    elif chance >= 0.02:  # 2-8%
        return "Uncommon"
    elif chance >= 0.01:  # 1-2%
        return "Rare"
    elif chance >= 0.002:  # 0.2-1%
        return "Epic"
    elif chance >= 0.0001:  # 0.01-0.2%
        return "Legendary"
    else:  # менее 0.01%
        return "Mythical"
    
def loot_item(chat_id, user_id):
    """Обрабатывает получение лута"""
    try:
        user_id = str(user_id)
        
        if not can_loot(user_id):
            remaining = get_remaining_time(user_id)
            return False, f"You need to wait {format_time(remaining)} before looting again!"
        
        result = get_random_item()
        rarity = get_rarity(result["chance"])
        result["rarity"] = rarity
        last_loot_time[user_id] = datetime.now(UTC)
        
        # Отправляем сообщение в Telegram, если это вызов из бота
        if chat_id:
            emoji_map = {
                "Common": "⚪",
                "Uncommon": "🟢",
                "Rare": "🔵",
                "Epic": "🟣",
                "Legendary": "🟡",
                "Mythical": "🌈"
            }
            emoji = emoji_map.get(rarity, "⚪")
            message = (
                f"{result['item_name']}\n"
                f"Rarity: {rarity} {emoji}\n"
                f"Chance: {result['chance']*100:.4f}%"
            )
            bot.send_message(chat_id, message)
        
        return True, result
        
    except Exception as e:
        print(f"Error in loot_item: {e}")
        return False, str(e)

@app.route('/loot', methods=['POST', 'OPTIONS'])
def web_loot():
    if request.method == 'OPTIONS':
        return jsonify({"status": "ok"}), 200
        
    try:
        print(f"Received request: {request.method}")
        data = request.json
        
        if not data:
            return jsonify({"error": "No data received"}), 400
            
        user_id = str(data.get('user_id'))
        init_data = data.get('initData')
        
        # Проверяем данные от Telegram
        if init_data and not verify_telegram_data(init_data, BOT_TOKEN):
            print("Failed to verify Telegram data")
            # Для разработки можно закомментировать следующую строку
            # return jsonify({"error": "Invalid Telegram data"}), 403
        
        if not user_id:
            return jsonify({"error": "No user_id provided"}), 400
            
        chat_id = data.get('chat_id', user_id)
        
        success, result = loot_item(chat_id, user_id)
        
        print(f"Loot result: {result}")
        
        if isinstance(result, dict):
            return jsonify(result)
        else:
            return jsonify({'error': result}), 429 if "wait" in str(result).lower() else 404

    except Exception as e:
        print(f"Error in web_loot: {e}")
        return jsonify({'error': str(e)}), 500

@bot.message_handler(commands=['start'])
def send_welcome(message):
    """Обработчик команды /start"""
    bot.reply_to(message, 
        "Welcome to Unum ad X Bot! 🎮\n"
        "Use /loot to get random items every hour.\n"
        "Visit our Mini App for a better experience!"
    )

@bot.message_handler(commands=['loot'])
def handle_loot(message):
    """Обработчик команды /loot"""
    success, result = loot_item(message.chat.id, message.from_user.id)
    if not success and isinstance(result, str):
        bot.reply_to(message, result)

def main():
    """Основная функция для запуска бота"""
    while True:
        try:
            print("Starting bot polling...")
            bot.polling(none_stop=True)
        except Exception as e:
            print(f"Bot polling error: {e}")
            time.sleep(15)

if __name__ == '__main__':
    # Загружаем последние данные при запуске
    user_collections = load_collections()
    
    # Запускаем бота в отдельном потоке
    bot_thread = Thread(target=main)
    bot_thread.daemon = True
    bot_thread.start()
    
    # Запускаем Flask сервер через waitress
    print("Starting server on port 5000...")
    serve(app, host='0.0.0.0', port=5000)