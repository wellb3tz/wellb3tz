import requests

TELEGRAM_API_TOKEN = '7895202892:AAExf3tcGSTcxa8FYb8114iTZ0b9gCVScvY'
TELEGRAM_API_URL = f'https://api.telegram.org/bot{TELEGRAM_API_TOKEN}/'

response = requests.get(TELEGRAM_API_URL + 'getUpdates', verify=False)
updates = response.json()

if updates['ok']:
    for update in updates['result']:
        if 'message' in update:
            chat_id = update['message']['chat']['id']
            print(f"Chat ID: {chat_id}")
else:
    print("Failed to get updates")