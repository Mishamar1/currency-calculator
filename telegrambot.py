import logging
import os
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import (
    Application, CommandHandler, MessageHandler, 
    filters, ContextTypes, ConversationHandler
)
from dotenv import load_dotenv
from currency_client import CurrencyClient

load_dotenv()

# Включаем логирование
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", 
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Токен бота
TOKEN = os.getenv("TELEGRAM_API_KEY")

# Состояния для ConversationHandler
AMOUNT, FROM_CURRENCY, TO_CURRENCY = range(3)

# Создаем клиент валют (один на всё приложение)
currency_client = CurrencyClient()

# Кэш для выбранных валют пользователя
user_data_cache = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /start"""
    welcome_name = update.message.from_user.first_name
    
    # Клавиатура с основными действиями
    keyboard = [
        ["💰 Конвертировать валюту"],
        ["📋 Список валют"]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    
    await update.message.reply_text(
        f"👋 Привет, {welcome_name}!\n\n"
        f"Я бот для конвертации валют. Я помогу тебе узнать, сколько денег "
        f"в одной валюте соответствует другой валюте по актуальному курсу.\n\n"
        f"Выбери действие:",
        reply_markup=reply_markup
    )

async def list_currencies(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показать список доступных валют"""
    currencies = currency_client.check_supported_currency()
    
    # Разбиваем на части по 20 валют, чтобы не превысить лимит Telegram
    message_parts = []
    current_part = "📊 *Доступные валюты:*\n\n"
    
    i = 1
    for code, name in currencies.items():
        line = f"`{code}` - {name}\n"
        
        if len(current_part + line) > 4000:  # Лимит Telegram ~4096
            message_parts.append(current_part)
            current_part = ""
        
        current_part += line
        
        # Добавляем пустую строку после каждых 10 валют для читаемости
        if i % 10 == 0:
            current_part += "\n"
        i += 1
    
    if current_part:
        message_parts.append(current_part)
    
    # Отправляем по частям
    for part in message_parts:
        await update.message.reply_text(part, parse_mode="Markdown")
    
    # Возвращаемся в главное меню
    keyboard = [["💰 Конвертировать валюту"]]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await update.message.reply_text(
        "Чтобы начать конвертацию, нажми кнопку ниже:",
        reply_markup=reply_markup
    )

async def convert_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Начать процесс конвертации - запросить сумму"""
    await update.message.reply_text(
        "💵 Введите сумму, которую хотите конвертировать (например: 100):",
        reply_markup=ReplyKeyboardRemove()
    )
    return AMOUNT

async def convert_amount(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Получить сумму и запросить исходную валюту"""
    try:
        amount = float(update.message.text.replace(',', '.'))
        if amount <= 0:
            await update.message.reply_text("❌ Сумма должна быть положительным числом. Попробуйте снова:")
            return AMOUNT
        
        # Сохраняем сумму в контексте
        context.user_data['amount'] = amount
        
        # Создаем клавиатуру с популярными валютами
        popular = ["USD", "EUR", "RUB", "GBP", "JPY", "CNY"]
        keyboard = [[p] for p in popular]
        keyboard.append(["🔍 Другая валюта"])
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        
        await update.message.reply_text(
            f"Сумма: {amount}\n\n"
            f"Выберите исходную валюту (из какой конвертируем):",
            reply_markup=reply_markup
        )
        return FROM_CURRENCY
        
    except ValueError:
        await update.message.reply_text(
            "❌ Пожалуйста, введите число (например: 100 или 100.50):"
        )
        return AMOUNT

async def convert_from_currency(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Получить исходную валюту и запросить целевую"""
    text = update.message.text
    
    if text == "🔍 Другая валюта":
        await update.message.reply_text(
            "Введите код валюты (например: USD, EUR, RUB):",
            reply_markup=ReplyKeyboardRemove()
        )
        return FROM_CURRENCY
    
    from_curr = text.upper()
    
    # Проверяем, поддерживается ли валюта
    if from_curr not in currency_client.supported_currencies:
        await update.message.reply_text(
            f"❌ Валюта {from_curr} не поддерживается.\n"
            f"Проверьте список доступных валют через команду /start или введите другой код:"
        )
        return FROM_CURRENCY
    
    context.user_data['from_currency'] = from_curr
    
    # Клавиатура с популярными валютами для целевой валюты
    popular = ["USD", "EUR", "RUB", "GBP", "JPY", "CNY"]
    keyboard = [[p] for p in popular]
    keyboard.append(["🔍 Другая валюта"])
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    
    await update.message.reply_text(
        f"Исходная валюта: {from_curr}\n\n"
        f"Теперь выберите валюту, в которую конвертируем:",
        reply_markup=reply_markup
    )
    return TO_CURRENCY

async def convert_to_currency(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Получить целевую валюту и выполнить конвертацию"""
    text = update.message.text
    
    if text == "🔍 Другая валюта":
        await update.message.reply_text(
            "Введите код валюты (например: USD, EUR, RUB):",
            reply_markup=ReplyKeyboardRemove()
        )
        return TO_CURRENCY
    
    to_curr = text.upper()
    
    # Проверяем, поддерживается ли валюта
    if to_curr not in currency_client.supported_currencies:
        await update.message.reply_text(
            f"❌ Валюта {to_curr} не поддерживается.\n"
            f"Проверьте список доступных валют или введите другой код:"
        )
        return TO_CURRENCY
    
    # Получаем данные из контекста
    amount = context.user_data.get('amount')
    from_curr = context.user_data.get('from_currency')
    
    if not amount or not from_curr:
        await update.message.reply_text(
            "❌ Произошла ошибка. Начните конвертацию заново:",
            reply_markup=ReplyKeyboardRemove()
        )
        return ConversationHandler.END
    
    # Выполняем конвертацию
    result = currency_client.convert(amount, from_curr, to_curr)
    
    if result is None:
        await update.message.reply_text(
            f"❌ Не удалось получить курс для {from_curr} → {to_curr}. Попробуйте позже.",
            reply_markup=ReplyKeyboardRemove()
        )
    else:
        # Получаем названия валют
        from_name = currency_client.get_supported_currencies(from_curr)
        to_name = currency_client.get_supported_currencies(to_curr)
        
        await update.message.reply_text(
            f"✅ *Результат конвертации:*\n\n"
            f"{amount:,.2f} {from_curr} ({from_name})\n"
            f"= {result:,.2f} {to_curr} ({to_name})",
            parse_mode="Markdown",
            reply_markup=ReplyKeyboardRemove()
        )
    
    # Возвращаемся в главное меню
    keyboard = [["💰 Конвертировать валюту", "📋 Список валют"]]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await update.message.reply_text(
        "Что хотите сделать дальше?",
        reply_markup=reply_markup
    )
    
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Отмена операции"""
    keyboard = [["💰 Конвертировать валюту", "📋 Список валют"]]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    
    await update.message.reply_text(
        "❌ Конвертация отменена. Выберите действие:",
        reply_markup=reply_markup
    )
    return ConversationHandler.END

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик текстовых сообщений (вне диалога)"""
    text = update.message.text
    
    if text == "💰 Конвертировать валюту":
        return await convert_start(update, context)
    elif text == "📋 Список валют":
        await list_currencies(update, context)
    else:
        keyboard = [["💰 Конвертировать валюту", "📋 Список валют"]]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        await update.message.reply_text(
            "Я вас не понимаю. Используйте кнопки меню или команду /start",
            reply_markup=reply_markup
        )

def main():
    """Основная функция для запуска бота"""
    if not TOKEN:
        logger.error("TELEGRAM_API_KEY не найден в .env файле")
        return
    
    # Создаем приложение
    app = Application.builder().token(TOKEN).build()
    
    # Диалог конвертации
    conv_handler = ConversationHandler(
        entry_points=[
            CommandHandler("convert", convert_start),
            MessageHandler(filters.Text("💰 Конвертировать валюту"), convert_start)
        ],
        states={
            AMOUNT: [MessageHandler(filters.TEXT & ~filters.COMMAND, convert_amount)],
            FROM_CURRENCY: [MessageHandler(filters.TEXT & ~filters.COMMAND, convert_from_currency)],
            TO_CURRENCY: [MessageHandler(filters.TEXT & ~filters.COMMAND, convert_to_currency)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )
    
    # Регистрируем обработчики
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("list", list_currencies))
    app.add_handler(conv_handler)
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    # Запускаем бота
    logger.info("Бот запущен...")
    app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()