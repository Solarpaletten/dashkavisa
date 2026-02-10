#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
STAGE 4: Calendar Watcher - ожидание появления слотов
Рабочая точка: /application-detail с сообщением "нет доступных слотов"

Доктрина: DOM-календарь появляется ТОЛЬКО когда есть слоты.
Пока слотов нет — календаря в DOM нет. Это WAIT, не ошибка.

Логика:
1. Подключиться к Chrome (attach_driver)
2. В цикле:
   - "нет доступных слотов" → WAITING_FOR_SLOTS → refresh → sleep
   - calendar/slot DOM найден → SLOTS_AVAILABLE → screenshot → exit
   - ни то ни другое → UNKNOWN_STATE → screenshot → sleep → refresh

❌ НЕ кликать
❌ НЕ навигировать (только refresh)
❌ НЕ считать "нет слотов" ошибкой
✅ Подключается к существующему Chrome (attach_driver)
"""
import os
import time
import random
import logging
from datetime import datetime
from shared_driver import attach_driver, screenshots_dir
from selenium.webdriver.common.by import By

# Логирование
log_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "logs")
os.makedirs(log_dir, exist_ok=True)

watcher_logger = logging.getLogger("calendar_watcher")
watcher_logger.setLevel(logging.INFO)
watcher_handler = logging.FileHandler(os.path.join(log_dir, "calendar_watcher.log"))
watcher_handler.setFormatter(logging.Formatter('%(asctime)s %(message)s', datefmt='[%Y-%m-%d %H:%M:%S]'))
watcher_logger.addHandler(watcher_handler)

console_handler = logging.StreamHandler()
console_handler.setFormatter(logging.Formatter('%(asctime)s %(message)s', datefmt='[%Y-%m-%d %H:%M:%S]'))
watcher_logger.addHandler(console_handler)

# Интервал опроса (секунды)
CHECK_INTERVAL_MIN = 50
CHECK_INTERVAL_MAX = 80

# Скриншот каждые N итераций в режиме ожидания
SCREENSHOT_EVERY_N = 10

# Селекторы "нет слотов"
NO_SLOTS_KEYWORDS = [
    "нет доступных слотов",
    "no available slots",
    "попробуйте позже",
    "try again later",
]

# Селекторы календаря / слотов (слабые сигналы — несколько)
CALENDAR_CSS_SELECTORS = [
    "mat-calendar",
    "mat-datepicker-content",
    "mat-month-view",
    "[class*='calendar']",
    "[class*='Calendar']",
    ".mat-calendar-body",
    ".mat-calendar-body-cell",
]

SLOT_XPATHS = [
    "//*[contains(@class,'calendar') or contains(@class,'Calendar')]",
    "//button[contains(@class,'available')]",
    "//div[contains(@class,'slot')]",
    "//td[contains(@class,'available')]",
]


def check_no_slots(driver):
    """Проверить: есть ли сообщение 'нет доступных слотов'."""
    try:
        body_text = driver.find_element(By.TAG_NAME, "body").text.lower()
        for keyword in NO_SLOTS_KEYWORDS:
            if keyword.lower() in body_text:
                return True
    except Exception as e:
        watcher_logger.warning(f"CHECK_NO_SLOTS_ERROR: {e}")
    return False


def check_calendar_or_slots(driver):
    """Проверить: появился ли calendar DOM или slot-элементы."""
    # CSS selectors
    for selector in CALENDAR_CSS_SELECTORS:
        try:
            elements = driver.find_elements(By.CSS_SELECTOR, selector)
            if elements:
                return True, f"CSS: {selector} ({len(elements)} elements)"
        except:
            continue

    # XPath selectors
    for xpath in SLOT_XPATHS:
        try:
            elements = driver.find_elements(By.XPATH, xpath)
            if elements:
                return True, f"XPath: {xpath} ({len(elements)} elements)"
        except:
            continue

    return False, None


def soft_refresh(driver):
    """Мягкий refresh через JS."""
    try:
        driver.execute_script("location.reload()")
    except Exception as e:
        watcher_logger.warning(f"REFRESH_ERROR: {e}")


if __name__ == "__main__":
    print("=" * 60)
    print("🟦 STAGE 4: CALENDAR WATCHER - Ожидание слотов")
    print("=" * 60)
    print("❌ Read-only mode: NO clicks, only refresh + read")
    print("=" * 60)

    driver = attach_driver()
    if not driver:
        print("❌ Failed to attach to Chrome")
        print("   Run Stage 1 → 2 → 3 first!")
        exit(1)

    # Проверка контекста
    current_url = driver.current_url
    print(f"📍 Current URL: {current_url}")

    if "vfsglobal" not in current_url:
        watcher_logger.error(f"WRONG_CONTEXT: {current_url}")
        print("❌ WRONG_CONTEXT: not on VFS page")
        exit(1)

    watcher_logger.info(f"WATCHER_STARTED: {current_url}")
    print("✅ Watcher active. Monitoring for slots...")
    print(f"🔄 Check every {CHECK_INTERVAL_MIN}-{CHECK_INTERVAL_MAX}s with page refresh")
    print("")

    cycle = 0

    try:
        while True:
            cycle += 1

            # 1. Проверяем: "нет слотов"?
            no_slots = check_no_slots(driver)

            if no_slots:
                # WAITING — нормальный режим
                if cycle % SCREENSHOT_EVERY_N == 1:
                    watcher_logger.info(f"WAITING_FOR_SLOTS (cycle {cycle})")
                    # Периодический скриншот
                    try:
                        ss_name = f"watcher_waiting_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
                        ss_path = os.path.join(screenshots_dir, ss_name)
                        driver.save_screenshot(ss_path)
                        watcher_logger.info(f"SCREENSHOT: {ss_path}")
                    except:
                        pass
                elif cycle % 5 == 0:
                    watcher_logger.info(f"WAITING_FOR_SLOTS (cycle {cycle})")

            else:
                # Нет сообщения "нет слотов" — проверяем: появился ли календарь?
                found, detail = check_calendar_or_slots(driver)

                if found:
                    # 🎯 СЛОТЫ ПОЯВИЛИСЬ!
                    watcher_logger.info(f"SLOTS_AVAILABLE: {detail}")
                    print("")
                    print("=" * 60)
                    print("🎯🎯🎯 SLOTS_AVAILABLE! 🎯🎯🎯")
                    print(f"   Detected: {detail}")
                    print(f"   URL: {driver.current_url}")
                    print("=" * 60)

                    # Скриншот
                    try:
                        ss_name = f"watcher_SLOTS_FOUND_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
                        ss_path = os.path.join(screenshots_dir, ss_name)
                        driver.save_screenshot(ss_path)
                        watcher_logger.info(f"SCREENSHOT_SLOTS: {ss_path}")
                        print(f"📸 Screenshot: {ss_path}")
                    except:
                        pass

                    # Выход — человек берёт управление
                    print("")
                    print("🛑 Watcher stopped. Manual action required!")
                    print("   Go to browser and book the slot!")
                    exit(0)

                else:
                    # Ни "нет слотов", ни календарь — неизвестное состояние
                    watcher_logger.warning(f"UNKNOWN_STATE (cycle {cycle}): URL={driver.current_url}")
                    try:
                        ss_name = f"watcher_unknown_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
                        ss_path = os.path.join(screenshots_dir, ss_name)
                        driver.save_screenshot(ss_path)
                        watcher_logger.info(f"SCREENSHOT_UNKNOWN: {ss_path}")
                    except:
                        pass

            # 2. Sleep с jitter
            sleep_time = random.randint(CHECK_INTERVAL_MIN, CHECK_INTERVAL_MAX)
            time.sleep(sleep_time)

            # 3. Soft refresh
            soft_refresh(driver)
            time.sleep(5)  # Дать странице загрузиться после refresh

    except KeyboardInterrupt:
        watcher_logger.info(f"WATCHER_STOPPED: KeyboardInterrupt (cycle {cycle})")
        print(f"\n⏹️  Watcher stopped by user after {cycle} cycles")
    except Exception as e:
        watcher_logger.error(f"WATCHER_ERROR: {e}")
        print(f"❌ Watcher error: {e}")

    print("")
    print(f"📊 Total cycles: {cycle}")
