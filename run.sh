#!/bin/bash

# Скрипт запуска visa_bot

# Переход в директорию бота
cd "$(dirname "$0")"

# Активация виртуального окружения
source venv/bin/activate

# Запуск бота
echo "Запуск Visa Bot..."
python main.py