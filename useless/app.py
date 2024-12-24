from flask import Flask, request, jsonify
import requests

app = Flask(__name__)

# Ваш Telegram API токен
TELEGRAM_API_TOKEN = '7895202892:AAExf3tcGSTcxa8FYb8114iTZ0b9gCVScvY'
TELEGRAM_API_URL = f'https://api.telegram.org/bot{TELEGRAM_API_TOKEN}/'

response = requests.get(TELEGRAM_API_URL + 'getUpdates', verify=False)
updates = response.json()

@app.route('/')
def home():
    return "Welcome to the Telegram Web App!"

@app.route('/sendMessage', methods=['POST'])
def send_message():
    data = request.json
    chat_id = data.get('chat_id')
    text = data.get('text')

    if not chat_id or not text:
        return jsonify({"error": "chat_id and text are required"}), 400

    response = requests.post(
        TELEGRAM_API_URL + 'sendMessage',
        json={
            'chat_id': chat_id,
            'text': text
        }
    )

    return jsonify(response.json())

if __name__ == '__main__':
    app.run(debug=True)