# dashkavisa — Gitkeep Task 1

## 1. Контекст проекта

**Проект:** dashkavisa  
**Репозиторий:** https://github.com/Solarpaletten/dashkavisa

**Назначение проекта:**  
Автоматизация записи на визу через VFS Global (Poland, Belarus) с использованием:
- Telegram-бота (управление и уведомления),
- браузерной автоматизации (Selenium/Chrome),
- подписок и мониторинга слотов.

Этот файл является контрактом задачи и единственным источником истины для Task1.

---

## 2. Цель Task1

Цель задачи — **НЕ разработка**.

Цель Task1:
- корректно ознакомиться с проектом dashkavisa,
- выровнять понимание архитектуры и границ,
- выявить и зафиксировать логические, структурные и архитектурные ошибки,
- привести текущее состояние проекта к ясной, описанной и непротиворечивой модели.

---

## 3. Область задачи (IN SCOPE)

Разрешено и требуется:
- изучить структуру репозитория;
- изучить документацию проекта: README.md, ARCHITECTURE.md, SETUP.md, CONFIG.md, BROWSER_LIFECYCLE.md, PROJECT_BOUNDARIES.md, ROADMAP.md;
- понять: роль Telegram-бота, роль browser automation, жизненный цикл браузера, как обрабатываются пользователи, подписки, слоты;
- выявить: противоречия между файлами, устаревшие или ошибочные формулировки, архитектурные несоответствия, места потенциальных ошибок или рисков;
- зафиксировать выводы прямо в этом файле в отведённых секциях.

---

## 4. Вне области задачи (NOT IN SCOPE)

Строго запрещено:
- писать или изменять код;
- создавать новые файлы;
- менять структуру проекта;
- предлагать новую архитектуру;
- переписывать проект;
- добавлять новые задачи;
- инициировать рефакторинг;
- решать проблемы Cloudflare, Selenium и т.п. на уровне реализации.

Task1 — аналитическая и выравнивающая, а не инженерная.

---

## 5. Формат работы

Разрешённые действия инженера:
- чтение репозитория через project_knowledge_search;
- обновление ТОЛЬКО этого файла;
- добавление текста только в указанные секции ниже.

---

## 6. Секции для заполнения инженером

### 6.1 Claude Analysis

**Общее понимание проекта:**

dashkavisa — Automation Worker (не веб-приложение, не API, не SaaS). Telegram-бот, управляющий фоновым процессом браузерной автоматизации для мониторинга визовых слотов VFS Global (Беларусь → Польша).

**Архитектура — 3 слоя:**

1. **Telegram Bot Layer** (`main.py`): точка входа. python-telegram-bot v20.0. Обрабатывает команды (/start, /check, /subscribe, /unsubscribe, /help, /register_now). ConversationHandler для пошагового ввода данных. job_queue для периодических проверок.

2. **Automation Layer** (`automation/browser.py`, `automation/register_account.py`, `automation/date_selector.py`): Selenium WebDriver + Chrome. Persistent профиль в `~/.dashkavisa/chrome_profile` (v0.4). Функции: setup_driver(), login_vfs_global(), check_available_dates(), accept_cookies_if_present(). cleanup_chrome() — killall chrome/chromedriver перед каждым запуском.

3. **Configuration Layer** (`config.py`, `.env`): load_dotenv() без явного пути (в текущей версии config.py в project knowledge). Переменные: TELEGRAM_BOT_TOKEN, VFS_EMAIL, VFS_PASSWORD, CITY, VISA_TYPE, CHECK_INTERVAL, MAX_DATES_TO_SHOW. Пользовательские данные (USER_FIRST_NAME, USER_LAST_NAME, USER_BIRTH_DATE, USER_PASSPORT) захардкожены в config.py.

**Хранение данных:**

- Подписчики: JSON (`data/subscribers.json`)
- Данные пользователей: TXT (`users/`)
- Логи: `logs/`
- Скриншоты: `logs/screenshots/`
- Нет БД. Нет персистентности состояния проверок.

**Критичные внешние зависимости:**

- Telegram API (критическая)
- VFS Global (критическая)
- Cloudflare (блокирующая)

**Деплой:**

- PM2 как process manager
- run.sh / start.sh для запуска
- ecosystem.config.js для PM2

---

### 6.2 Detected Issues / Inconsistencies

**I-01. config.py: load_dotenv() без явного пути vs. документация**

Факт: в config.py (project knowledge) вызов `load_dotenv()` без параметра `dotenv_path`. При запуске через PM2 рабочая директория может не совпадать с директорией `config.py`. Файл `.env` находится в `visa_bot/`, а PM2 может запускать из `/var/www/visadash_bot/`. Документация CONFIG.md этот нюанс не описывает. В логах Task2 зафиксирована ошибка: "Отсутствуют обязательные переменные: TOKEN, EMAIL или PASSWORD" — именно из-за этого.

**I-02. Дублирование load_dotenv() в automation/browser.py**

Факт: `automation/browser.py` самостоятельно вызывает `load_dotenv()` и определяет свои переменные (VFS_EMAIL, VFS_PASSWORD, CITY и т.д.), дублируя config.py. Также `automation/register_account.py` делает то же самое. Два источника правды для одних и тех же переменных.

**I-03. Хардкод пользовательских данных в config.py**

Факт: USER_FIRST_NAME, USER_LAST_NAME, USER_BIRTH_DATE, USER_PASSPORT захардкожены непосредственно в config.py как строковые литералы, а не загружаются из .env. Документация CONFIG.md описывает эти переменные как настраиваемые через .env, но фактический код их оттуда не читает.

**I-04. Расхождение main.py и main_updated.py**

Факт: в репозитории присутствуют два файла — `main.py` и `main_updated.py`. main.py импортирует `import config` и использует `config.BOT_TOKEN`, а также содержит импорты automation-модулей. main_updated.py использует `load_dotenv()` напрямую и `os.getenv("TELEGRAM_BOT_TOKEN")`. Неясно, какой из них актуален. Наличие двух точек входа — источник путаницы.

**I-05. config.py не экспортирует BOT_TOKEN, но main.py его импортирует**

Факт: main.py содержит `from config import BOT_TOKEN, CHECK_INTERVAL`. Однако в config.py переменная называется `TELEGRAM_BOT_TOKEN`, а не `BOT_TOKEN`. Это приведёт к ImportError при запуске.

**I-06. setup.sh использует устаревшую схему установки ChromeDriver**

Факт: setup.sh использует `chromedriver.storage.googleapis.com` для загрузки ChromeDriver. Начиная с Chrome 115, Google перешёл на Chrome for Testing (новый endpoint). Для Chrome 120+ (указанного в user-agent в browser.py) этот метод не работает.

**I-07. requirements.txt: фиксированные старые версии**

Факт: python-telegram-bot==20.0, python-dotenv==0.21.0, selenium==4.9.0, webdriver-manager==3.8.6. Это конкретные старые версии. setup.sh при этом устанавливает зависимости без указания версий (`pip install python-telegram-bot==20.0 python-dotenv selenium webdriver-manager`), что создаёт расхождение с requirements.txt.

**I-08. Противоречие: ARCHITECTURE.md заявляет "нет персистентности сессий", но browser.py использует persistent профиль**

Факт: ARCHITECTURE.md: "Нет персистентности сессий — каждая проверка создаёт новую сессию браузера". Однако browser.py (v0.4) использует `CHROME_PROFILE_DIR = ~/.dashkavisa/chrome_profile` как persistent профиль. Документация не обновлена после изменения в v0.4.

**I-09. Противоречие между browser.py: кеш отключён, но профиль persistent**

Факт: browser.py одновременно использует persistent профиль (для сохранения cookies/Cloudflare tokens) и отключает кеш (`--disable-application-cache`, `--disable-cache`). Это логический конфликт: persistent профиль имеет смысл именно для кеширования cookies/tokens.

**I-10. README.md: структура проекта неполная**

Факт: README.md показывает `automation/register_account.py`, но не упоминает `automation/undetected_register.py`, `account_manager.py`, `main_updated.py`, `test_env.py`, `setup.sh`, `handlers/register_now.py`. Фактическая структура репозитория шире документированной.

**I-11. ROADMAP.md: "Переход на undetected-chromedriver" в v0.2, но уже используется**

Факт: ROADMAP.md указывает "Переход на undetected-chromedriver" как задачу v0.2 (Backlog, не начато). Однако файл `automation/undetected_register.py` уже существует и использует undetected-chromedriver. Roadmap не отражает фактическое состояние.

**I-12. PROJECT_BOUNDARIES.md: "Нет сохранения истории проверок", но subscribers.json существует**

Факт: PROJECT_BOUNDARIES заявляет "Сохранение истории проверок — Нет базы данных". Фактически `data/subscribers.json` хранит данные подписчиков, а `users/` хранит данные пользователей. Это форма персистентности, хотя и не "история проверок" как таковая. Формулировка неточна.

**I-13. Двойной import os в register_account.py**

Факт: `automation/register_account.py` содержит `import os` в строке 3 и повторно `import os` перед `from dotenv import load_dotenv`. Дублирование импорта.

---

### 6.3 Clarifications Needed

**Q-01.** Какой файл является актуальной точкой входа: `main.py` или `main_updated.py`? Нужно ли удалить неактуальный файл?

**Q-02.** Переменная `BOT_TOKEN` в main.py vs `TELEGRAM_BOT_TOKEN` в config.py — какое имя канонично? Это сломанный импорт или config.py был обновлён позже (с добавлением алиаса `BOT_TOKEN`)?

**Q-03.** Пользовательские данные (USER_FIRST_NAME и т.д.) — должны загружаться из .env (как описано в CONFIG.md) или оставаться захардкоженными (как в текущем config.py)?

**Q-04.** Файлы `automation/undetected_register.py`, `account_manager.py`, `handlers/register_now.py` — это часть v0.1 или экспериментальные артефакты Task2? Должны ли они быть в scope документации?

**Q-05.** Persistent Chrome Profile (v0.4 в browser.py) — это принятое архитектурное решение? Если да, ARCHITECTURE.md и BROWSER_LIFECYCLE.md нуждаются в обновлении.

**Q-06.** setup.sh — актуален ли он? ChromeDriver endpoint устарел для Chrome 115+.

---

### 6.4 Task1 Status

**READY FOR REVIEW**

---

## 7. Критерий завершения (DONE)

Task1 считается выполненной, если:
- [x] файл gitkeep1task1.md обновлён;
- [x] все секции из пункта 6 заполнены;
- [x] код проекта не изменялся;
- [x] новые файлы не создавались;
- [x] выводы сформулированы чётко и проверяемо.

---

## 8. Формат отчёта в чат

> C=>D
> Task1 complete.
> gitkeep1task1.md updated.
> Ready for review.
