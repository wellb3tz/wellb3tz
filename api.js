class LootAPI {
    constructor(botToken) {
        this.botToken = botToken;
    }

    async sendMessage(chatId, text) {
        const url = `https://api.telegram.org/bot${this.botToken}/sendMessage`;
        const response = await fetch(url, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                chat_id: chatId,
                text: text
            })
        });
        return response.json();
    }

    // Добавляем метод для сохранения лута
    async saveLoot(userId, itemName, chance) {
        try {
            const url = 'http://your-server.com/save_loot'; // Замените на ваш URL
            const response = await fetch(url, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    user_id: userId,
                    item_name: itemName,
                    chance: chance,
                    timestamp: new Date().toISOString()
                })
            });
            return response.json();
        } catch (error) {
            console.error('Error saving loot:', error);
            return null;
        }
    }

    // Метод для получения истории лута
    async getLootHistory(userId) {
        try {
            const url = `http://your-server.com/get_loot_history?user_id=${userId}`;
            const response = await fetch(url);
            return response.json();
        } catch (error) {
            console.error('Error getting loot history:', error);
            return [];
        }
    }
}