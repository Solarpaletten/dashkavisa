# Установка и настройка visa_bot

**Версия документа:** v0.1

---

## Требования к системе

### Операционная система

- Ubuntu 22.04 / 24.04 LTS (рекомендуется)
- Debian 11/12
- Другие Linux-дистрибутивы (с адаптацией команд)

### Python

- Python 3.10 или выше
- pip (менеджер пакетов)
- venv (виртуальное окружение)

### Браузер

- Google Chrome или Chromium
- ChromeDriver (совместимый с версией браузера)

### Дополнительно

- Git
- PM2 (для production-деплоя)
- Доступ к интернету

---

## Пошаговая установка

### Шаг 1. Подготовка системы

Обновление пакетов:

```bash
sudo apt update && sudo apt upgrade -y
```

Установка базовых зависимостей:

```bash
sudo apt install -y python3 python3-pip python3-venv git curl wget
```

### Шаг 2. Установка Chrome

```bash
wget https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb
sudo dpkg -i google-chrome-stable_current_amd64.deb
sudo apt --fix-broken install -y
```

Проверка установки:

```bash
google-chrome --version
```

### Шаг 3. Установка ChromeDriver

ChromeDriver должен соответствовать версии Chrome.

```bash
# Проверить версию Chrome
google-chrome --version

# Скачать соответствующий ChromeDriver с:
# https://chromedriver.chromium.org/downloads
# или https://googlechromelabs.github.io/chrome-for-testing/
```

Установка:

```bash
sudo mv chromedriver /usr/local/bin/
sudo chmod +x /usr/local/bin/chromedriver
```

Проверка:

```bash
chromedriver --version
```

### Шаг 4. Клонирование репозитория

```bash
cd /var/www
git clone <repository-url> visa_bot
cd visa_bot
```

### Шаг 5. Создание виртуального окружения

```bash
python3 -m venv venv
source venv/bin/activate
```

### Шаг 6. Установка Python-зависимостей

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### Шаг 7. Настройка конфигурации

Создание файла `.env`:

```bash
cp .env.example .env
nano .env
```

Заполнить все обязательные переменные (см. [CONFIG.md](CONFIG.md)).

### Шаг 8. Создание директорий

```bash
mkdir -p logs/screenshots
mkdir -p users
mkdir -p data
```

### Шаг 9. Проверка установки

```bash
python test_env.py
```

Ожидаемый результат: все проверки пройдены.

---

## Первый запуск

### Режим разработки

```bash
source venv/bin/activate
python main.py
```

### Проверка работы бота

1. Открыть Telegram
2. Найти бота по имени
3. Отправить команду `/start`
4. Должен прийти ответ с приветствием

---

## Ручной первичный вход (ВАЖНО)

При первом запуске автоматизации VFS Global может потребовать ручного прохождения проверки Cloudflare.

### Процедура:

1. Запустить браузер вручную на сервере (через VNC или X11 forwarding)
2. Перейти на `https://visa.vfsglobal.com/blr/ru/pol/login`
3. Ввести учётные данные
4. Пройти проверку Cloudflare (если появится)
5. Дождаться успешного входа
6. Закрыть браузер

После этого автоматический вход должен работать корректно.

---

## Production-деплой (PM2)

### Установка PM2

```bash
sudo npm install -g pm2
```

### Создание скрипта запуска

Файл `run.sh` уже присутствует в проекте:

```bash
#!/bin/bash
cd /var/www/visa_bot
source venv/bin/activate
python main.py
```

### Запуск через PM2

```bash
pm2 start run.sh --name visabot
pm2 save
pm2 startup
```

### Управление процессом

```bash
pm2 status          # Статус
pm2 logs visabot    # Логи
pm2 restart visabot # Перезапуск
pm2 stop visabot    # Остановка
```

---

## Проверка работоспособности

### Чек-лист

- [ ] Бот отвечает на `/start`
- [ ] Команда `/check` запускает проверку
- [ ] В логах нет критических ошибок
- [ ] Скриншоты создаются в `logs/screenshots/`

### Просмотр логов

```bash
tail -f logs/browser.log
```

---

## Типичные проблемы

### Chrome не запускается

Проверить наличие зависимостей:

```bash
sudo apt install -y libxss1 libappindicator1 libindicator7 libnss3
```

### ChromeDriver не совместим

Убедиться, что версии Chrome и ChromeDriver совпадают.

### Ошибки прав доступа

```bash
sudo chown -R $USER:$USER /var/www/visa_bot
chmod +x run.sh
```

### Cloudflare блокирует

См. документ [BROWSER_LIFECYCLE.md](BROWSER_LIFECYCLE.md).

---

*Документ актуален для версии v0.1*
