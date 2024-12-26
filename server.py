from flask import Flask, request, jsonify
from flask_cors import CORS
import json
from datetime import datetime
import pytz

app = Flask(__name__)
CORS(app)

# Путь к файлу с данными
LOOT_DATA_FILE = 'loot_history.json'

def load_loot_data():
    try:
        with open(LOOT_DATA_FILE, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return {}

def save_loot_data(data):
    with open(LOOT_DATA_FILE, 'w') as f:
        json.dump(data, f, indent=2)

@app.route('/save_loot', methods=['POST'])
def save_loot():
    try:
        data = request.json
        user_id = str(data['user_id'])
        item_name = data['item_name']
        chance = data['chance']
        timestamp = data['timestamp']

        loot_data = load_loot_data()
        
        if user_id not in loot_data:
            loot_data[user_id] = {
                'items': [],
                'last_loot': None
            }
        
        # Сохраняем информацию о луте
        loot_data[user_id]['items'].append({
            'item_name': item_name,
            'chance': chance,
            'timestamp': timestamp
        })
        
        # Обновляем время последнего лута
        loot_data[user_id]['last_loot'] = timestamp
        
        save_loot_data(loot_data)
        
        return jsonify({'status': 'success'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/get_loot_history', methods=['GET'])
def get_loot_history():
    try:
        user_id = str(request.args.get('user_id'))
        loot_data = load_loot_data()
        
        if user_id not in loot_data:
            return jsonify([])
            
        return jsonify(loot_data[user_id]['items'])
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/check_cooldown', methods=['GET'])
def check_cooldown():
    try:
        user_id = str(request.args.get('user_id'))
        loot_data = load_loot_data()
        
        if user_id not in loot_data or not loot_data[user_id]['last_loot']:
            return jsonify({'can_loot': True})
            
        last_loot = datetime.fromisoformat(loot_data[user_id]['last_loot'].replace('Z', '+00:00'))
        now = datetime.now(pytz.UTC)
        
        time_passed = (now - last_loot).total_seconds()
        can_loot = time_passed >= 3600  # 1 час кулдаун
        
        return jsonify({
            'can_loot': can_loot,
            'time_remaining': max(0, 3600 - time_passed)
        })
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

if __name__ == '__main__':
    app.run(port=5000)