from flask import Flask, render_template_string
import json
from datetime import datetime, UTC

app = Flask(__name__)

# Константы
INVENTORY_FILE = 'user_collections.json'

# HTML шаблон (такой же как в предыдущем примере)
HTML_TEMPLATE = '''
<!DOCTYPE html>
<html>
<head>
    <title>Unum ad X Bot Dashboard</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            max-width: 800px;
            margin: 0 auto;
            padding: 20px;
            background-color: #f5f5f5;
        }
        .container {
            background-color: white;
            padding: 20px;
            border-radius: 10px;
            box-shadow: 0 0 10px rgba(0,0,0,0.1);
        }
        .item-category {
            margin-bottom: 20px;
        }
        .item {
            display: flex;
            justify-content: space-between;
            padding: 5px 0;
            border-bottom: 1px solid #eee;
        }
        h1, h2 {
            color: #333;
        }
        .stats {
            background-color: #e9ecef;
            padding: 15px;
            border-radius: 5px;
            margin-bottom: 20px;
        }
        .refresh-time {
            color: #666;
            font-size: 0.8em;
            text-align: right;
            margin-top: 20px;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>Unum ad X Bot Dashboard</h1>
        
        <div class="stats">
            <h2>Global Statistics</h2>
            <p>Total Users: {{ total_users }}</p>
            <p>Total Items Collected: {{ total_items }}</p>
        </div>

        <h2>Item Database</h2>
        {% for category, category_items in items_by_category.items() %}
        <div class="item-category">
            <h3>{{ category }} Items</h3>
            {% for item in category_items %}
            <div class="item">
                <span>{{ item.name }}</span>
                <span>{{ "%.4f"|format(item.chance * 100) }}%</span>
            </div>
            {% endfor %}
        </div>
        {% endfor %}
        
        <div class="refresh-time">
            Last updated: {{ current_time }}
        </div>
    </div>
</body>
</html>
'''

# Список предметов (скопируйте из bot.py)
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
def dashboard():
    # Загрузка данных
    user_collections = load_collections()
    
    # Подсчет статистики
    total_users = len(user_collections)
    total_items = sum(
        sum(inventory['inventory'].values())
        for inventory in user_collections.values()
    )
    
    # Текущее время
    current_time = datetime.now(UTC).strftime('%Y-%m-%d %H:%M:%S UTC')
    
    # Категоризация предметов
    items_by_category = categorize_items(items)
    
    return render_template_string(HTML_TEMPLATE,
        items_by_category=items_by_category,
        total_users=total_users,
        total_items=total_items,
        current_time=current_time
    )

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)