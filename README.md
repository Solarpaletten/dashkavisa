# VFS Global Visa Bot

**Версия:** v0.1 — Initial Internal Release  
**Статус:** Зафиксирован, режим сопровождения  
**Тип:** Automation Worker / Internal Tool

---

## Назначение

Telegram-бот для мониторинга доступных слотов записи на визу в Польшу через VFS Global (Беларусь, Минск).

Проект предназначен для **внутреннего использования** одним пользователем. Это не публичный сервис и не SaaS-продукт.

---

## Возможности

- Авторизация в системе VFS Global
- Проверка доступных слотов для записи
- Уведомления в Telegram при появлении слотов
- Система подписки на уведомления
- Ручная проверка по команде

---

## Команды бота

| Команда | Описание |
|---------|----------|
| `/start` | Начало работы с ботом |
| `/check` | Ручная проверка доступных слотов |
| `/subscribe` | Подписаться на уведомления |
| `/unsubscribe` | Отписаться от уведомлений |
| `/help` | Справка по командам |

---

## Ограничения текущей версии

- **Cloudflare защита** — сайт VFS Global использует Cloudflare, что требует особого подхода к автоматизации
- **Ручной первичный вход** — первая авторизация может потребовать ручного прохождения проверки
- **Single-user** — рассчитан на одного пользователя
- **Зависимость от UI** — изменения на сайте VFS могут потребовать адаптации селекторов

---

## Структура проекта

```
visa_bot/
├── main.py              # Точка входа, Telegram-бот
├── config.py            # Конфигурация
├── automation/
│   ├── browser.py       # Работа с браузером
│   ├── date_selector.py # Выбор дат
│   └── register_account.py
├── logs/                # Логи и скриншоты
├── users/               # Данные пользователей
└── docs/                # Документация
```

---

## Быстрый старт

1. Клонировать репозиторий
2. Настроить `.env` по образцу `.env.example`
3. Установить зависимости: `pip install -r requirements.txt`
4. Запустить: `python main.py`

Подробная инструкция: [docs/SETUP.md](docs/SETUP.md)

---

## Документация

- [Архитектура](docs/ARCHITECTURE.md)
- [Установка и настройка](docs/SETUP.md)
- [Конфигурация](docs/CONFIG.md)
- [Жизненный цикл браузера](docs/BROWSER_LIFECYCLE.md)
- [Границы проекта](docs/PROJECT_BOUNDARIES.md)
- [Roadmap](docs/ROADMAP.md)

---

## Команда

- **Архитектор:** Leanid (YPL Group / IT SOLAR)
- **Координатор:** Dashka (Super Assistant)
- **Инженер:** Claude (Chief Engineer)

---

## Лицензия

Проприетарный код © 2025 YPL Group Inc. / IT SOLAR

Использование, копирование и распространение без разрешения запрещено.

git add main.py
git commit -m "fix: make slot search dates dynamic for 2026

- Remove hardcoded dates 25.05.2025, 27.05.2025, 02.06.2025
- Use datetime.today() + timedelta(14/21/35) for dynamic dates
- Format DD.MM.YYYY preserved
- Tested 01.02.2026: bot returns 15.02/22.02/08.03.2026
- Full flow confirmed: /start → slots → booking → link"

# Тег релиза
git tag -a v0.2-dynamic-dates -m "v0.2: Dynamic slot dates (2026)

Fixed: hardcoded May 2025 dates replaced with dynamic calculation
Tested: 01.02.2026 - bot correctly shows Feb-Mar 2026 slots
Files changed: main.py (2 replacements)
Audited clean: browser.py, date_selector.py"

# Пуш
git push origin main
git push origin v0.2-dynamic-dates
