# 🚀 Быстрый запуск Show My Food Bot

## 1. Подготовка

### Создайте файл .env
```bash
cp env.example .env
```

Отредактируйте `.env` и добавьте ваши API ключи:
```env
TELEGRAM_BOT_TOKEN=8306187494:AAEuv8eonlfL-wMgrHil66fZCIbNL1SAK3w
PERPLEXITY_API_KEY=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
BOT_MODE=polling
DEBUG=True
```

## 2. Установка зависимостей

```bash
pip install -r requirements.txt
```

## 3. Тестирование компонентов

```bash
python test_bot.py
```

## 4. Запуск бота

```bash
python run_bot.py
```

## 5. Тестирование в Telegram

1. Найдите бота: @show_my_food_bot
2. Отправьте команду `/start`
3. Отправьте фото блюда
4. Следуйте инструкциям бота

## 🐳 Docker (альтернативный способ)

```bash
# Сборка
docker build -t show-my-food-bot .

# Запуск
docker run -d --name bot --env-file .env show-my-food-bot
```

## 🔧 Устранение неполадок

### Ошибка "Module not found"
```bash
pip install -r requirements.txt
```

### Ошибка "API key not found"
Проверьте файл `.env` и убедитесь, что все ключи указаны правильно.

### Ошибка "Permission denied" (Docker)
```bash
sudo docker run -d --name bot --env-file .env show-my-food-bot
```

## 📱 Команды бота

- `/start` - приветствие
- `/help` - помощь
- `/privacy` - политика конфиденциальности
- `/reset` - сброс анализа
- `/fact` - дополнительный факт

## 🎯 Примеры использования

1. **Фото блюда** → анализ → карточка с калориями и фактами
2. **Текст**: "паста карбонара 250г запеченная" → анализ
3. **Уточнения**: изменение веса, способа приготовления

Готово! 🎉
