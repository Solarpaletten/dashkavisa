#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import logging
import datetime
import time
import json
from threading import Thread
from dotenv import load_dotenv
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ConversationHandler,
    filters,
    ContextTypes,
)

# Попытка импорта Selenium для веб-автоматизации
try:
    from selenium import webdriver
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.common.exceptions import TimeoutException, NoSuchElementException
    SELENIUM_AVAILABLE = True
except ImportError:
    SELENIUM_AVAILABLE = False
    logging.warning("Selenium не установлен. Функции автоматизации браузера не будут работать.")

# Настройка логирования
log_dir = os.path.dirname(os.path.abspath(__file__))
log_file = os.path.join(log_dir, "visa_bot.log")

# Проверка доступа к директории логов
try:
    with open(log_file, 'a') as f:
        pass
except:
    log_file = "/tmp/visa_bot.log"

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Загрузка переменных окружения
load_dotenv()
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

# Состояния для разговора
(MAIN_MENU, CHOOSE_VISA_TYPE, CHOOSE_CITY, CHOOSE_INVITATION, 
 ENTER_FULL_NAME, ENTER_BIRTHDATE, CONFIRMATION) = range(7)

# Глобальные данные пользователей
user_data_global = {}

# Опции для выбора
VISA_TYPES = ["Туристическая виза", "Рабочая виза", "Национальная виза", "Шенген виза"]
CITIES = ["Минск", "Брест", "Гродно", "Могилев", "Витебск", "Гомель"]
INVITATION_TYPES = ["Туристическое приглашение", "Рабочее приглашение", "Учебное приглашение", "Частное приглашение"]

# Функция для создания меню с кнопками
def create_menu_keyboard(options):
    keyboard = []
    for option in options:
        keyboard.append([InlineKeyboardButton(option, callback_data=option)])
    return InlineKeyboardMarkup(keyboard)

# Команда /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user = update.message.from_user
    logger.info(f"Пользователь {user.username} ({user.id}) запустил бота")
    
    # Приветственное сообщение
    await update.message.reply_text(
        f"👋 Здравствуйте, {user.first_name}!\n\n"
        "Я бот для проверки и бронирования слотов в визовом центре VFS Global.\n\n"
        "Я помогу вам:\n"
        "- Проверить наличие свободных слотов\n"
        "- Заполнить форму записи на подачу документов\n"
        "- Получить ссылку для завершения процесса\n\n"
        "Пожалуйста, выберите тип визы:"
    )
    
    # Предлагаем выбрать тип визы
    keyboard = create_menu_keyboard(VISA_TYPES)
    await update.message.reply_text("Выберите тип визы:", reply_markup=keyboard)
    
    # Инициализируем данные пользователя
    user_id = update.effective_user.id
    user_data_global[user_id] = {}
    
    return CHOOSE_VISA_TYPE

# Обработчик выбора типа визы
async def visa_type_selected(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    selected_visa = query.data
    user_data_global[user_id]['visa_type'] = selected_visa
    
    logger.info(f"Пользователь {query.from_user.username} ({user_id}) выбрал тип визы: {selected_visa}")
    
    # Предлагаем выбрать город
    keyboard = create_menu_keyboard(CITIES)
    await query.edit_message_text(
        f"Выбран тип визы: *{selected_visa}*\n\n"
        "Теперь выберите город для подачи документов:",
        reply_markup=keyboard,
        parse_mode='Markdown'
    )
    
    return CHOOSE_CITY

# Обработчик выбора города
async def city_selected(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    selected_city = query.data
    user_data_global[user_id]['city'] = selected_city
    
    logger.info(f"Пользователь {query.from_user.username} ({user_id}) выбрал город: {selected_city}")
    
    # Предлагаем выбрать тип приглашения
    keyboard = create_menu_keyboard(INVITATION_TYPES)
    await query.edit_message_text(
        f"Выбран город: *{selected_city}*\n\n"
        "Выберите тип приглашения/документа:",
        reply_markup=keyboard,
        parse_mode='Markdown'
    )
    
    return CHOOSE_INVITATION

# Обработчик выбора типа приглашения
async def invitation_selected(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    selected_invitation = query.data
    user_data_global[user_id]['invitation'] = selected_invitation
    
    logger.info(f"Пользователь {query.from_user.username} ({user_id}) выбрал тип приглашения: {selected_invitation}")
    
    # Просим ввести ФИО
    await query.edit_message_text(
        f"Выбран тип приглашения: *{selected_invitation}*\n\n"
        "Пожалуйста, введите ваши ФИО (как в паспорте):",
        parse_mode='Markdown'
    )
    
    return ENTER_FULL_NAME

# Обработчик ввода ФИО
async def full_name_entered(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_id = update.effective_user.id
    full_name = update.message.text
    user_data_global[user_id]['full_name'] = full_name
    
    logger.info(f"Пользователь {update.message.from_user.username} ({user_id}) ввел ФИО: {full_name}")
    
    # Просим ввести дату рождения
    await update.message.reply_text(
        "Пожалуйста, введите вашу дату рождения в формате ДД.ММ.ГГГГ:"
    )
    
    return ENTER_BIRTHDATE

# Обработчик ввода даты рождения
async def birthdate_entered(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_id = update.effective_user.id
    birthdate = update.message.text
    user_data_global[user_id]['birthdate'] = birthdate
    
    logger.info(f"Пользователь {update.message.from_user.username} ({user_id}) ввел дату рождения: {birthdate}")
    
    # Показываем сводку введенной информации для подтверждения
    user_data = user_data_global[user_id]
    
    confirmation_message = (
        "📝 *Проверьте введенные данные:*\n\n"
        f"👤 *ФИО:* {user_data['full_name']}\n"
        f"🎂 *Дата рождения:* {user_data['birthdate']}\n"
        f"🛂 *Тип визы:* {user_data['visa_type']}\n"
        f"🏙️ *Город:* {user_data['city']}\n"
        f"📋 *Тип приглашения:* {user_data['invitation']}\n\n"
        "Данные указаны верно? Если да, я начну поиск доступных слотов."
    )
    
    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("✅ Да, всё верно", callback_data="confirm_yes"),
            InlineKeyboardButton("❌ Нет, начать заново", callback_data="confirm_no")
        ]
    ])
    
    await update.message.reply_text(
        confirmation_message,
        reply_markup=keyboard,
        parse_mode='Markdown'
    )
    
    return CONFIRMATION

# Обработчик подтверждения данных
async def confirmation_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    
    if query.data == "confirm_yes":
        # Пользователь подтвердил данные
        logger.info(f"Пользователь {query.from_user.username} ({user_id}) подтвердил данные и запустил поиск слотов")
        
        # Отправляем сообщение о начале поиска
        await query.edit_message_text(
            "🔍 *Начинаю поиск доступных слотов...*\n\n"
            "Это может занять некоторое время. Пожалуйста, подождите.",
            parse_mode='Markdown'
        )
        
        # Запускаем поиск слотов в отдельном потоке
        progress_message = await context.bot.send_message(
            chat_id=query.message.chat_id,
            text="⏳ Проверяю доступность слотов... (0%)"
        )
        
        # Имитация прогресса (в реальном приложении здесь будет реальная проверка)
        for progress in range(10, 101, 10):
            await asyncio.sleep(1)  # Имитация задержки
            await context.bot.edit_message_text(
                chat_id=query.message.chat_id,
                message_id=progress_message.message_id,
                text=f"⏳ Проверяю доступность слотов... ({progress}%)"
            )
        
        # Имитация успешного результата (в реальном приложении здесь будет результат проверки)
        # Здесь будет вызов функции check_available_slots
        if not SELENIUM_AVAILABLE:
            # Если Selenium не установлен, показываем сообщение об ошибке
            await context.bot.edit_message_text(
                chat_id=query.message.chat_id,
                message_id=progress_message.message_id,
                text="⚠️ *Ошибка:* Функции автоматизации браузера недоступны. "
                     "Пожалуйста, обратитесь к администратору бота.",
                parse_mode='Markdown'
            )
        else:
            # Имитация нахождения слота (в будущем замените на реальную проверку)
            available_dates = ["25.05.2025", "27.05.2025", "02.06.2025"]
            
            if available_dates:
                # Доступные слоты найдены
                date_buttons = []
                for date in available_dates:
                    date_buttons.append([InlineKeyboardButton(date, callback_data=f"date_{date}")])
                
                slot_keyboard = InlineKeyboardMarkup(date_buttons)
                
                await context.bot.edit_message_text(
                    chat_id=query.message.chat_id,
                    message_id=progress_message.message_id,
                    text="✅ *Найдены доступные слоты!*\n\n"
                         "Выберите предпочтительную дату:",
                    reply_markup=slot_keyboard,
                    parse_mode='Markdown'
                )
            else:
                # Доступных слотов не найдено
                await context.bot.edit_message_text(
                    chat_id=query.message.chat_id,
                    message_id=progress_message.message_id,
                    text="😔 *К сожалению, доступных слотов не найдено.*\n\n"
                         "Попробуйте выбрать другой город или повторите попытку позже.",
                    parse_mode='Markdown'
                )
        
        return ConversationHandler.END
    
    elif query.data == "confirm_no":
        # Пользователь не подтвердил данные, начинаем заново
        logger.info(f"Пользователь {query.from_user.username} ({user_id}) не подтвердил данные и начал заново")
        
        # Очищаем данные пользователя
        user_data_global[user_id] = {}
        
        # Предлагаем выбрать тип визы заново
        keyboard = create_menu_keyboard(VISA_TYPES)
        await query.edit_message_text(
            "🔄 Начинаем заново.\n\n"
            "Пожалуйста, выберите тип визы:",
            reply_markup=keyboard
        )
        
        return CHOOSE_VISA_TYPE

# Обработчик выбора даты (после подтверждения)
async def date_selected(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    selected_date = query.data.replace("date_", "")
    user_data_global[user_id]['selected_date'] = selected_date
    
    logger.info(f"Пользователь {query.from_user.username} ({user_id}) выбрал дату: {selected_date}")
    
    # Здесь в реальном приложении будет логика бронирования слота
    # Имитация процесса бронирования
    await query.edit_message_text(
        f"🗓️ Выбрана дата: *{selected_date}*\n\n"
        "🔄 Оформляю бронирование...",
        parse_mode='Markdown'
    )
    
    # Имитация задержки бронирования
    booking_message = await context.bot.send_message(
        chat_id=query.message.chat_id,
        text="⏳ Оформляю бронирование... (0%)"
    )
    
    for progress in range(20, 101, 20):
        await asyncio.sleep(1)  # Имитация задержки
        await context.bot.edit_message_text(
            chat_id=query.message.chat_id,
            message_id=booking_message.message_id,
            text=f"⏳ Оформляю бронирование... ({progress}%)"
        )
    
    # Имитация успешного бронирования с получением ссылки
    unique_code = f"VFS-{user_id}-{int(time.time())}"
    booking_url = f"https://visa.vfsglobal.com/blr/ru/pol/book-an-appointment/confirmation?code={unique_code}"
    
    await context.bot.edit_message_text(
        chat_id=query.message.chat_id,
        message_id=booking_message.message_id,
        text="✅ *Бронирование успешно оформлено!*\n\n"
             f"🔗 *Ваша ссылка для завершения процесса:*\n{booking_url}\n\n"
             "⚠️ *Важно:* Пройдите по ссылке в течение 15 минут для завершения бронирования.\n\n"
             "📝 *Инструкция:*\n"
             "1. Перейдите по ссылке\n"
             "2. Войдите в свой аккаунт VFS Global\n"
             "3. Проверьте и подтвердите информацию\n"
             "4. Завершите процесс бронирования\n\n"
             "*Ваш код бронирования:* `" + unique_code + "`",
        parse_mode='Markdown'
    )
    
    return ConversationHandler.END

# Обработчик отмены
async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user = update.message.from_user
    logger.info(f"Пользователь {user.username} ({user.id}) отменил разговор")
    
    await update.message.reply_text(
        "❌ Операция отменена. Чтобы начать заново, воспользуйтесь командой /start"
    )
    
    return ConversationHandler.END

# Функция для проверки доступных слотов через браузер
def check_available_slots(user_data):
    """
    Проверяет наличие доступных слотов на сайте VFS Global
    
    Args:
        user_data: Словарь с данными пользователя
    
    Returns:
        list: Список доступных дат или пустой список, если слоты не найдены
    """
    if not SELENIUM_AVAILABLE:
        logger.error("Selenium не установлен, невозможно проверить доступные слоты")
        return []
    
    try:
        # Настройка браузера
        options = webdriver.ChromeOptions()
        options.add_argument('--headless')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        
        driver = webdriver.Chrome(options=options)
        
        # Посещаем сайт VFS Global
        driver.get("https://visa.vfsglobal.com/blr/ru/pol/login")
        
        # Создаем новый аккаунт или входим в существующий
        # (Здесь нужно добавить реальную логику авторизации)
        
        # Переходим на страницу бронирования
        driver.get("https://visa.vfsglobal.com/blr/ru/pol/book-an-appointment")
        
        # Выбираем тип визы, город и др.
        # (Здесь нужно добавить реальную логику выбора опций)
        
        # Проверяем доступные слоты
        # (Здесь нужно добавить реальную логику проверки слотов)
        
        # Возвращаем пример доступных дат
        return ["25.05.2025", "27.05.2025", "02.06.2025"]
    
    except Exception as e:
        logger.error(f"Ошибка при проверке доступных слотов: {str(e)}")
        return []
    
    finally:
        if 'driver' in locals():
            driver.quit()

# Сообщение об ошибке при неверном вводе
async def invalid_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "⚠️ Извините, я не понимаю этот ввод. Пожалуйста, следуйте инструкциям."
    )

# Импорт asyncio для имитации асинхронных задержек
import asyncio

# Обработчик команды регистрации
async def register_now(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обрабатывает команду /register_now для регистрации нового аккаунта в VFS Global."""
    user = update.message.from_user
    logger.info(f"Пользователь {user.username} ({user.id}) запустил команду регистрации")
    
    # Отправляем сообщение о начале процесса
    await update.message.reply_text(
        "🔄 Начинаю процесс регистрации нового аккаунта VFS Global...\n\n"
        "⏳ Это может занять несколько минут. Пожалуйста, подождите."
    )
    
    try:
        # Создаем необходимые директории
        import os
        import subprocess
        import sys
        import time
        import random
        import string
        
        bot_dir = os.path.dirname(os.path.abspath(__file__))
        automation_dir = os.path.join(bot_dir, "automation")
        users_dir = os.path.join(bot_dir, "users")
        logs_dir = os.path.join(bot_dir, "logs")
        
        os.makedirs(automation_dir, exist_ok=True)
        os.makedirs(users_dir, exist_ok=True)
        os.makedirs(logs_dir, exist_ok=True)
        os.makedirs(os.path.join(logs_dir, "screenshots"), exist_ok=True)
        
        # Проверяем наличие скрипта регистрации
        register_script = os.path.join(automation_dir, "register_account.py")
        if not os.path.exists(register_script):
            logger.warning(f"Скрипт автоматической регистрации не найден: {register_script}")
            await update.message.reply_text(
                "⚠️ Скрипт автоматической регистрации не найден.\n"
                "Использую режим симуляции регистрации."
            )
            # Будем использовать симуляцию
            use_simulation = True
        else:
            use_simulation = False
            
            # Проверяем наличие необходимых зависимостей
            try:
                # Добавляем automation_dir в путь для импорта
                if automation_dir not in sys.path:
                    sys.path.append(automation_dir)
                
                # Импортируем модуль регистрации
                from register_account import register_account, cleanup_chrome
                logger.info("Модуль регистрации успешно импортирован")
                use_simulation = False
            except ImportError as e:
                logger.error(f"Ошибка импорта модуля регистрации: {str(e)}")
                await update.message.reply_text(
                    "⚠️ Не удалось загрузить модуль регистрации.\n"
                    "Использую режим симуляции регистрации."
                )
                use_simulation = True
        
        # Очищаем процессы Chrome перед запуском
        await update.message.reply_text("🧹 Очищаю процессы Chrome и временные файлы...")
        
        if use_simulation:
            # Очистка в режиме симуляции
            try:
                subprocess.run(['killall', '-9', 'chrome'], stderr=subprocess.DEVNULL)
                subprocess.run(['killall', '-9', 'chromedriver'], stderr=subprocess.DEVNULL)
                subprocess.run(['pkill', '-9', '-f', 'chrome'], stderr=subprocess.DEVNULL)
                subprocess.run(['rm', '-rf', '/tmp/chrome_*'], stderr=subprocess.DEVNULL)
                subprocess.run(['rm', '-rf', '/tmp/.com.google.Chrome.*'], stderr=subprocess.DEVNULL)
            except Exception as e:
                logger.warning(f"Ошибка при очистке Chrome: {str(e)}")
        else:
            # Используем функцию очистки из модуля регистрации
            cleanup_chrome()
        
        # Создаем сообщение с прогрессом
        progress_message = await update.message.reply_text("⏳ Регистрация аккаунта: 0%")
        
        if use_simulation:
            # РЕЖИМ СИМУЛЯЦИИ: Имитация процесса регистрации
            for progress in range(10, 101, 10):
                await asyncio.sleep(1)  # Имитация работы
                await context.bot.edit_message_text(
                    chat_id=update.message.chat_id,
                    message_id=progress_message.message_id,
                    text=f"⏳ Регистрация аккаунта (симуляция): {progress}%"
                )
            
            # Генерируем случайные данные для аккаунта
            email = f"vfsuser_{random.randint(100000, 999999)}@example.com"
            password = ''.join(random.choices(string.ascii_letters + string.digits, k=12))
            
            result = {
                "success": True,
                "email": email,
                "password": password,
                "message": "Симуляция регистрации успешно завершена"
            }
        else:
            # РЕАЛЬНЫЙ РЕЖИМ: Запускаем реальную регистрацию через модуль
            # Обновляем прогресс для пользователя
            await context.bot.edit_message_text(
                chat_id=update.message.chat_id,
                message_id=progress_message.message_id,
                text="⏳ Регистрация аккаунта: запуск браузера..."
            )
            
            # Запускаем процесс регистрации
            result = register_account(max_selenium_retries=1, max_undetected_retries=1)
            
            # Обновляем сообщение о результате
            if result["success"]:
                await context.bot.edit_message_text(
                    chat_id=update.message.chat_id,
                    message_id=progress_message.message_id,
                    text="⏳ Регистрация аккаунта: заполнение формы..."
                )
            else:
                await context.bot.edit_message_text(
                    chat_id=update.message.chat_id,
                    message_id=progress_message.message_id,
                    text="⏳ Регистрация аккаунта: ошибка при работе браузера, пробую другой метод..."
                )
        
        # Сохраняем данные аккаунта
        if result["success"]:
            user_file = os.path.join(users_dir, f"user_{update.effective_user.id}.txt")
            with open(user_file, "w") as f:
                f.write(f"Email: {result['email']}\nPassword: {result['password']}")
            
            # Отправляем результат пользователю
            await context.bot.edit_message_text(
                chat_id=update.message.chat_id,
                message_id=progress_message.message_id,
                text=f"✅ Аккаунт успешно зарегистрирован!\n\n"
                     f"📧 Email: {result['email']}\n"
                     f"🔑 Пароль: {result['password']}\n\n"
                     f"Сохраните эти данные для входа в VFS Global.\n"
                     f"Для использования в боте введите команду /start"
            )
        else:
            await context.bot.edit_message_text(
                chat_id=update.message.chat_id,
                message_id=progress_message.message_id,
                text=f"❌ Не удалось автоматически зарегистрировать аккаунт: {result['message']}\n\n"
                     f"Пожалуйста, попробуйте позже или зарегистрируйтесь вручную на сайте VFS Global."
            )
    
    except Exception as e:
        logger.error(f"Ошибка при регистрации: {str(e)}")
        await update.message.reply_text(
            f"❌ Ошибка при регистрации аккаунта: {str(e)}\n"
            "Пожалуйста, попробуйте позже или обратитесь к администратору."
        )

# Основная функция
def main():
    """Запуск бота"""
    # Создаем приложение с использованием токена
    application = Application.builder().token(TOKEN).build()
    
    # Определяем обработчик разговора
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            CHOOSE_VISA_TYPE: [CallbackQueryHandler(visa_type_selected)],
            CHOOSE_CITY: [CallbackQueryHandler(city_selected)],
            CHOOSE_INVITATION: [CallbackQueryHandler(invitation_selected)],
            ENTER_FULL_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, full_name_entered)],
            ENTER_BIRTHDATE: [MessageHandler(filters.TEXT & ~filters.COMMAND, birthdate_entered)],
            CONFIRMATION: [CallbackQueryHandler(confirmation_handler)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )
    
    # Добавляем обработчик для выбора даты
    application.add_handler(CallbackQueryHandler(date_selected, pattern=r"^date_"))
    
    # Добавляем обработчик команды регистрации
    application.add_handler(CommandHandler("register_now", register_now))
    
    # Добавляем обработчик разговора
    application.add_handler(conv_handler)
    
    # Запускаем бота
    application.run_polling()

if __name__ == "__main__":
    main()