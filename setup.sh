#!/bin/bash

# Скрипт установки виртуального окружения и зависимостей для visa_bot

echo "======================================================"
echo "        УСТАНОВКА VISA BOT"
echo "======================================================"

# Проверка наличия Python 3
if ! command -v python3 &> /dev/null; then
    echo "Python 3 не найден. Пожалуйста, установите Python 3"
    exit 1
fi

# Переход в директорию бота
cd "$(dirname "$0")"

# Создание виртуального окружения
echo "Создание виртуального окружения..."
python3 -m venv venv
source venv/bin/activate

# Обновление pip
echo "Обновление pip..."
pip install --upgrade pip

# Установка зависимостей
echo "Установка зависимостей..."
pip install python-telegram-bot==20.0 python-dotenv selenium webdriver-manager

# Установка ChromeDriver (опционально)
if command -v apt-get &> /dev/null; then
    echo "Установка Google Chrome и ChromeDriver..."
    sudo apt-get update
    sudo apt-get install -y wget unzip
    
    # Установка Chrome
    wget -q https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb
    sudo apt-get install -y ./google-chrome-stable_current_amd64.deb
    rm google-chrome-stable_current_amd64.deb
    
    # Установка ChromeDriver
    CHROME_VERSION=$(google-chrome --version | awk '{print $3}' | cut -d '.' -f 1)
    wget -q "https://chromedriver.storage.googleapis.com/LATEST_RELEASE_$CHROME_VERSION" -O chromedriver_version
    CHROMEDRIVER_VERSION=$(cat chromedriver_version)
    rm chromedriver_version
    
    wget -q "https://chromedriver.storage.googleapis.com/$CHROMEDRIVER_VERSION/chromedriver_linux64.zip"
    unzip -q chromedriver_linux64.zip
    chmod +x chromedriver
    sudo mv chromedriver /usr/local/bin/
    rm chromedriver_linux64.zip
fi

# Создание директорий для логов и скриншотов
echo "Создание директорий для логов и скриншотов..."
mkdir -p logs/screenshots

echo ""
echo "======================================================"
echo "        УСТАНОВКА ЗАВЕРШЕНА"
echo "======================================================"
echo ""
echo "Для запуска бота выполните:"
echo "  source venv/bin/activate"
echo "  python main.py"
echo ""
echo "Не забудьте настроить файл .env с токеном вашего бота"
echo "и данными для доступа к VFS Global"
echo "======================================================"