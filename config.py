#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
from dotenv import load_dotenv

# Загружаем переменные окружения
load_dotenv()

# Настройки Telegram бота
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

# Настройки для VFS Global
VFS_EMAIL = os.getenv("VFS_EMAIL")
VFS_PASSWORD = os.getenv("VFS_PASSWORD")
CITY = os.getenv("CITY", "Минск")
VISA_TYPE = os.getenv("VISA_TYPE", "Шенген виза")

# Настройки для проверки слотов
CHECK_INTERVAL = int(os.getenv("CHECK_INTERVAL", "60"))  # Интервал между проверками в минутах
MAX_DATES_TO_SHOW = int(os.getenv("MAX_DATES_TO_SHOW", "5"))  # Максимальное количество дат для отображения

# Данные пользователя KANOPLICH NADZEYA
USER_FIRST_NAME = "NADZEYA"
USER_LAST_NAME = "KANOPLICH"
USER_BIRTH_DATE = "06.09.1957"
USER_PASSPORT = "4060957H053PB2"

# Пути к директориям
BOT_DIR = os.path.dirname(os.path.abspath(__file__))
AUTOMATION_DIR = os.path.join(BOT_DIR, "automation")
USERS_DIR = os.path.join(BOT_DIR, "users")
LOGS_DIR = os.path.join(BOT_DIR, "logs")
SCREENSHOTS_DIR = os.path.join(LOGS_DIR, "screenshots")

# Создаем необходимые директории
os.makedirs(AUTOMATION_DIR, exist_ok=True)
os.makedirs(USERS_DIR, exist_ok=True)
os.makedirs(LOGS_DIR, exist_ok=True)
os.makedirs(SCREENSHOTS_DIR, exist_ok=True)