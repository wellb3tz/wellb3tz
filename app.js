const BOT_TOKEN = '7895202892:AAExf3tcGSTcxa8FYb8114iTZ0b9gCVScvY';
const api = new LootAPI(BOT_TOKEN);

let lastLootTime = {};
const COOLDOWN_SECONDS = 3600; // 1 час
let isButtonEnabled = true;

function showMessage(text, duration = 3000, isSuccess = false) {
    const messageElement = document.getElementById('message');
    messageElement.textContent = text;
    messageElement.style.backgroundColor = isSuccess ? 
        'var(--tg-theme-button-color, #2481cc)' : 
        'var(--tg-theme-secondary-bg-color, #f1f1f1)';
    
    if (duration > 0) {
        setTimeout(() => {
            messageElement.textContent = '';
            messageElement.style.backgroundColor = 'transparent';
        }, duration);
    }
}

function getRandomItem() {
    const rand = Math.random();
    let currentProb = 0;
    
    for (const item of items) {
        currentProb += item.chance;
        if (rand <= currentProb) {
            return item;
        }
    }
    
    return items[0];
}

function canLoot(userId) {
    if (!(userId in lastLootTime)) return true;
    const timePassedMs = Date.now() - lastLootTime[userId];
    return timePassedMs >= COOLDOWN_SECONDS * 1000;
}

function getFormattedTimeRemaining(userId) {
    if (!(userId in lastLootTime)) return "0h 0m";
    const timePassedMs = Date.now() - lastLootTime[userId];
    const remainingSeconds = Math.max(0, COOLDOWN_SECONDS - timePassedMs / 1000);
    const hours = Math.floor(remainingSeconds / 3600);
    const minutes = Math.floor((remainingSeconds % 3600) / 60);
    return `${hours}h ${minutes}m`;
}

async function handleLootClick() {
    if (!isButtonEnabled) return;

    const button = document.querySelector('.loot-button');
    button.disabled = true;
    isButtonEnabled = false;
    showMessage('🎲 Rolling for loot...', 0);

    try {
        const user = window.Telegram.WebApp.initDataUnsafe?.user;
        const userId = user?.id || `test_user_${Math.random().toString(36).substr(2, 9)}`;

        // Проверяем кулдаун на сервере
        const cooldownCheck = await api.checkCooldown(userId);
        if (!cooldownCheck.can_loot) {
            const timeRemaining = Math.ceil(cooldownCheck.time_remaining);
            const hours = Math.floor(timeRemaining / 3600);
            const minutes = Math.floor((timeRemaining % 3600) / 60);
            throw new Error(`You need to wait ${hours}h ${minutes}m before looting again!`);
        }

        const result = getRandomItem();
        
        // Сохраняем лут на сервере
        await api.saveLoot(userId, result.name, result.chance);

        const message = `${result.name}\nChance: ${(result.chance * 100).toFixed(4)}%`;
        
        if (user?.id) {
            await api.sendMessage(user.id, message);
        }

        showMessage(message, 3000, true);

    } catch (error) {
        console.error('Error:', error);
        showMessage(`❌ Error: ${error.message}`);
    }
}

// Инициализация при загрузке страницы
document.addEventListener('DOMContentLoaded', function() {
    try {
        const savedLootTime = localStorage.getItem('lastLootTime');
        if (savedLootTime) {
            lastLootTime = JSON.parse(savedLootTime);
        }

        window.Telegram.WebApp.ready();
        window.Telegram.WebApp.expand();
    } catch (e) {
        console.error('Error initializing:', e);
    }
});