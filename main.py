# Импорт необходимых библиотек
import telebot
from telebot import types
import sqlite3
import logging
from datetime import datetime
import json  # Для хранения дополнительных данных, если нужно

# Настройка логирования для отслеживания действий бота
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Токен вашего бота от BotFather (замените на реальный)
BOT_TOKEN = '8254638011:AAFo6iwRTITcrJY4p_1CYPzeSkCpH4kX0b0'

# Инициализация бота
bot = telebot.TeleBot(BOT_TOKEN)

# Имя базы данных SQLite для хранения состояний пользователей
DB_NAME = 'bot_states.db'

# Создание подключения к базе данных и таблиц
def init_db():
    """
    Инициализация базы данных.
    Создает таблицу для хранения состояний пользователей в воронке.
    """
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_states (
            user_id INTEGER PRIMARY KEY,
            state TEXT DEFAULT 'start',
            interests TEXT,
            email TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()
    logger.info("База данных инициализирована.")

# Функция для получения текущего состояния пользователя
def get_user_state(user_id):
    """
    Получает текущее состояние пользователя из БД.
    Если пользователь новый, возвращает 'start'.
    """
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('SELECT state FROM user_states WHERE user_id = ?', (user_id,))
    result = cursor.fetchone()
    conn.close()
    if result:
        return result[0]
    else:
        # Новый пользователь, добавляем его в БД
        set_user_state(user_id, 'start')
        return 'start'

# Функция для обновления состояния пользователя
def set_user_state(user_id, state, interests=None, email=None):
    """
    Обновляет состояние пользователя в БД.
    Принимает дополнительные данные, если нужно.
    """
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    if interests or email:
        cursor.execute('''
            INSERT OR REPLACE INTO user_states (user_id, state, interests, email)
            VALUES (?, ?, ?, ?)
        ''', (user_id, state, interests, email))
    else:
        cursor.execute('''
            INSERT OR REPLACE INTO user_states (user_id, state)
            VALUES (?, ?)
        ''', (user_id, state))
    conn.commit()
    conn.close()
    logger.info(f"Состояние пользователя {user_id} обновлено на {state}.")

# Обработчик команды /start
@bot.message_handler(commands=['start'])
def start_message(message):
    """
    Обработчик стартовой команды.
    Показывает приветствие и кнопку для начала воронки.
    """
    user_id = message.from_user.id
    state = get_user_state(user_id)
    
    if state != 'completed':
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        btn_start = types.KeyboardButton('🚀 Начать воронку')
        markup.add(btn_start)
        
        bot.send_message(
            message.chat.id,
            "Привет! 👋 Я бот для демонстрации воронки продаж.\n"
            "Нажмите кнопку ниже, чтобы начать путь от знакомства до покупки.",
            reply_markup=markup
        )
        set_user_state(user_id, 'awaiting_start')
    else:
        bot.send_message(message.chat.id, "Вы уже прошли воронку! /start для сброса.")

# Обработчик текстовых сообщений для этапа ожидания начала
@bot.message_handler(func=lambda message: get_user_state(message.from_user.id) == 'awaiting_start')
def handle_start_request(message):
    """
    Обрабатывает запрос на начало воронки.
    Переходит к первому шагу: сбор интересов.
    """
    if message.text == '🚀 Начать воронку':
        user_id = message.from_user.id
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
        btn1 = types.KeyboardButton('Интересуюсь продуктами')
        btn2 = types.KeyboardButton('Интересуюсь услугами')
        btn3 = types.KeyboardButton('Просто смотрю')
        markup.add(btn1, btn2, btn3)
        
        bot.send_message(
            message.chat.id,
            "Отлично! Первый шаг воронки: Расскажите о своих интересах.\n"
            "Выберите вариант:",
            reply_markup=markup
        )
        set_user_state(user_id, 'awaiting_interests')
    else:
        bot.send_message(message.chat.id, "Пожалуйста, используйте кнопку для начала.")

# Обработчик для сбора интересов
@bot.message_handler(func=lambda message: get_user_state(message.from_user.id) == 'awaiting_interests')
def handle_interests(message):
    """
    Сохраняет интересы пользователя и переходит к следующему шагу: запрос email.
    """
    user_id = message.from_user.id
    interests = message.text
    set_user_state(user_id, 'awaiting_email', interests=interests)
    
    markup = types.ReplyKeyboardRemove()  # Убираем клавиатуру
    bot.send_message(
        message.chat.id,
        f"Спасибо! Вы выбрали: {interests}\n\n"
        "Второй шаг: Для персональных рекомендаций укажите ваш email.",
        reply_markup=markup
    )

# Обработчик для сбора email
@bot.message_handler(func=lambda message: get_user_state(message.from_user.id) == 'awaiting_email')
def handle_email(message):
    """
    Валидирует и сохраняет email, переходит к предложению продукта.
    """
    user_id = message.from_user.id
    email = message.text.strip().lower()
    
    # Простая валидация email
    if '@' not in email or '.' not in email:
        bot.send_message(message.chat.id, "Неверный формат email. Попробуйте снова.")
        return
    
    set_user_state(user_id, 'proposing_product', email=email)
    
    bot.send_message(
        message.chat.id,
        f"Email сохранен: {email}\n\n"
        "Третий шаг: На основе ваших интересов я предлагаю продукт!\n"
        "Например, курс по Python за 999 руб. Хотите узнать детали?"
    )
    
    markup = types.InlineKeyboardMarkup()
    btn_details = types.InlineKeyboardButton('Подробнее о продукте', callback_data='details')
    btn_buy = types.InlineKeyboardButton('Купить сейчас', callback_data='buy')
    btn_skip = types.InlineKeyboardButton('Пока нет', callback_data='skip')
    markup.add(btn_details, btn_buy, btn_skip)
    
    bot.send_message(message.chat.id, "Выберите действие:", reply_markup=markup)

# Обработчик inline-кнопок для предложения продукта
@bot.callback_query_handler(func=lambda call: True)
def handle_callback(call):
    """
    Обрабатывает нажатия на inline-кнопки в шаге предложения.
    """
    user_id = call.from_user.id
    state = get_user_state(user_id)
    
    if state == 'proposing_product':
        if call.data == 'details':
            bot.answer_callback_query(call.id)
            bot.send_message(
                call.message.chat.id,
                "Детали продукта: Курс 'Python для начинающих'.\n"
                "Включает 10 уроков, домашние задания и сертификат.\n"
                "Цена: 999 руб. Скидка 20% для вас!"
            )
            set_user_state(user_id, 'details_shown')
        
        elif call.data == 'buy':
            bot.answer_callback_query(call.id)
            bot.send_message(
                call.message.chat.id,
                "Переходим к оплате! (Интеграция с платежами, например, Yandex.Kassa).\n"
                "Ссылка на оплату: https://example.com/pay (замените на реальную)."
            )
            complete_funnel(call.message.chat.id, user_id)
        
        elif call.data == 'skip':
            bot.answer_callback_query(call.id)
            bot.send_message(
                call.message.chat.id,
                "Хорошо, подумайте. Мы отправим напоминание позже на email.\n"
                "Воронка завершена."
            )
            complete_funnel(call.message.chat.id, user_id)

# Функция завершения воронки
def complete_funnel(chat_id, user_id):
    """
    Завершает воронку, обновляет состояние и отправляет финальное сообщение.
    """
    set_user_state(user_id, 'completed')
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    btn_restart = types.KeyboardButton('/start')
    markup.add(btn_restart)
    
    bot.send_message(
        chat_id,
        "Воронка завершена! Спасибо за участие.\n"
        "Вы успешно прошли все этапы. /start для новой сессии.",
        reply_markup=markup
    )

# Обработчик команды /reset для сброса состояния
@bot.message_handler(commands=['reset'])
def reset_state(message):
    """
    Сбрасывает состояние пользователя для новой воронки.
    """
    user_id = message.from_user.id
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('DELETE FROM user_states WHERE user_id = ?', (user_id,))
    conn.commit()
    conn.close()
    bot.send_message(message.chat.id, "Состояние сброшено. Начните заново с /start.")

# Обработчик неизвестных сообщений
@bot.message_handler(func=lambda message: True)
def handle_unknown(message):
    """
    Обрабатывает неизвестные команды или сообщения.
    """
    state = get_user_state(message.from_user.id)
    if state == 'start' or state == 'completed':
        bot.send_message(message.chat.id, "Используйте /start для начала.")
    else:
        bot.send_message(message.chat.id, "Пожалуйста, следуйте инструкциям воронки.")

# Обработчик ошибок
@bot.message_handler(func=lambda message: message.text == '/error')
def error_handler(message):
    """
    Тестовый обработчик для симуляции ошибки.
    """
    raise ValueError("Тестовая ошибка для демонстрации.")

# Главная функция запуска бота
def main():
    """
    Основная функция: инициализация БД и запуск бота.
    """
    init_db()
    logger.info("Бот запущен.")
    
    # Обработка ошибок polling
    try:
        bot.polling(none_stop=True, interval=0, timeout=20)
    except Exception as e:
        logger.error(f"Ошибка polling: {e}")
    finally:
        logger.info("Бот остановлен.")

# Дополнительные утилиты (для расширения)
def log_user_action(user_id, action):
    """
    Логирует действия пользователя для аналитики воронки.
    """
    timestamp = datetime.now().isoformat()
    with open('user_actions.log', 'a', encoding='utf-8') as f:
        f.write(f"{timestamp} - User {user_id}: {action}\n")

# Если файл запускается напрямую, стартуем бота
if __name__ == '__main__':
    main()

# Дополнительные комментарии для развертывания:
# 1. Замените BOT_TOKEN на токен от @BotFather в Telegram.
# 2. Для production используйте webhook вместо polling (см. docs telebot).
# 3. Интегрируйте реальную платежную систему (например, Telegram Payments).
# 4. Добавьте scheduler (APScheduler) для напоминаний по email.
# 5. Тестируйте на тестовом боте перед деплоем на Heroku/VPS.
# 6. Для масштаба используйте Redis вместо SQLite для состояний.
# 7. Обеспечьте безопасность: не храните чувствительные данные в БД без шифрования.
# 8. Мониторьте логи для оптимизации воронки (конверсия по этапам).
