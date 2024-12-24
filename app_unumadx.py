from flask import Flask, jsonify, send_file
from flask_cors import CORS
import json
from datetime import datetime, UTC

app = Flask(__name__)
CORS(app)  # Включаем CORS для всех роутов

# Константы
INVENTORY_FILE = 'user_collections.json'

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

def load_collections():
    try:
        with open(INVENTORY_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}

def categorize_items(items):
    categories = {
        'Common': [],
        'Uncommon': [],
        'Rare': [],
        'Epic': [],
        'Legendary': [],
        'Mythical': []
    }
    
    for item in items:
        chance = item['chance']
        if chance > 0.07:
            categories['Common'].append(item)
        elif chance > 0.02:
            categories['Uncommon'].append(item)
        elif chance > 0.005:
            categories['Rare'].append(item)
        elif chance > 0.001:
            categories['Epic'].append(item)
        elif chance > 0.0001:
            categories['Legendary'].append(item)
        else:
            categories['Mythical'].append(item)
    
    return categories

@app.route('/')
def index():
    return send_file('index.html')

@app.route('/api/stats')
def get_stats():
    user_collections = load_collections()
    
    total_users = len(user_collections)
    total_items = sum(
        sum(inventory['inventory'].values())
        for inventory in user_collections.values()
    )
    
    return jsonify({
        'total_users': total_users,
        'total_items': total_items,
        'items_by_category': categorize_items(items),
        'updated_at': datetime.now(UTC).isoformat()
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, ssl_context='adhoc')
