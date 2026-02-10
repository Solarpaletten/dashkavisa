#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
STAGE 4: Calendar Watcher - пассивное наблюдение за календарём
Задача: read-only мониторинг доступных дней
❌ НЕ кликать
❌ НЕ навигировать
❌ НЕ менять состояние формы
❌ НЕ вызывать driver.get()
✅ ТОЛЬКО читать DOM
✅ ТОЛЬКО логировать
✅ ТОЛЬКО скриншот при новом слоте
"""
import os
import time
import random
import logging
from datetime import datetime
from shared_driver import setup_driver, screenshots_dir
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException, StaleElementReferenceException

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
POLL_INTERVAL_MIN = 30
POLL_INTERVAL_MAX = 60


def get_available_days(driver):
    """
    Читает DOM календаря, возвращает список доступных дней.
    Доступный день = .mat-calendar-body-cell БЕЗ aria-disabled="true"
    """
    available = []
    try:
        cells = driver.find_elements(By.CSS_SELECTOR, ".mat-calendar-body-cell")
        for cell in cells:
            try:
                aria_disabled = cell.get_attribute("aria-disabled")
                if aria_disabled == "true":
                    continue
                aria_label = cell.get_attribute("aria-label")
                cell_text = cell.text.strip()
                day_info = aria_label if aria_label else cell_text
                if day_info:
                    available.append(day_info)
            except StaleElementReferenceException:
                continue
    except NoSuchElementException:
        watcher_logger.warning("CALENDAR_NOT_FOUND: .mat-calendar-body-cell elements not present")
    except Exception as e:
        watcher_logger.error(f"DOM_READ_ERROR: {e}")
    return available


def check_calendar_present(driver):
    """
    Проверяет наличие календаря в DOM (без навигации).
    """
    try:
        elements = driver.find_elements(By.CSS_SELECTOR, ".mat-calendar-body, mat-calendar, [class*='calendar']")
        return len(elements) > 0
    except Exception:
        return False


if __name__ == "__main__":
    print("=" * 60)
    print("🟦 STAGE 4: CALENDAR WATCHER - Пассивное наблюдение")
    print("=" * 60)
    print("❌ Read-only mode: NO clicks, NO navigation")
    print("=" * 60)

    driver = setup_driver()
    if not driver:
        print("❌ Failed to connect to driver")
        exit(1)

    # Проверка: календарь должен быть на экране
    if not check_calendar_present(driver):
        watcher_logger.error("CALENDAR_NOT_FOUND: Browser is not on calendar page. Run Stage 1-3 first.")
        print("❌ Calendar not found on current page")
        print("   Run Stage 1 → 2 → 3 first, then start watcher")
        exit(1)

    watcher_logger.info("WATCHER_STARTED")
    print("✅ Calendar detected. Watcher active.")
    print(f"🔄 Polling every {POLL_INTERVAL_MIN}-{POLL_INTERVAL_MAX}s")
    print("")

    known_days = set()
    cycle = 0

    try:
        while True:
            cycle += 1

            # Читаем доступные дни
            current_days = get_available_days(driver)
            current_set = set(current_days)

            # Новые дни (которых раньше не было)
            new_days = current_set - known_days

            if new_days:
                for day in sorted(new_days):
                    watcher_logger.info(f"SLOT_DAY_AVAILABLE: {day}")

                # Screenshot при новом слоте
                try:
                    screenshot_name = f"watcher_new_slot_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
                    screenshot_path = os.path.join(screenshots_dir, screenshot_name)
                    driver.save_screenshot(screenshot_path)
                    watcher_logger.info(f"SCREENSHOT_SAVED: {screenshot_path}")
                except Exception as e:
                    watcher_logger.warning(f"SCREENSHOT_FAILED: {e}")

                known_days = current_set
            else:
                if cycle % 10 == 1:
                    watcher_logger.info(f"POLL_CYCLE_{cycle}: no new slots (known: {len(known_days)}, current: {len(current_set)})")

            # Проверка: календарь ещё на экране
            if not check_calendar_present(driver):
                watcher_logger.warning("CALENDAR_LOST: Calendar no longer in DOM. Page may have changed.")
                print("⚠️  Calendar lost. Stopping watcher.")
                break

            # Пауза с jitter
            sleep_time = random.randint(POLL_INTERVAL_MIN, POLL_INTERVAL_MAX)
            time.sleep(sleep_time)

    except KeyboardInterrupt:
        watcher_logger.info("WATCHER_STOPPED: KeyboardInterrupt")
        print("\n⏹️  Watcher stopped by user")
    except Exception as e:
        watcher_logger.error(f"WATCHER_ERROR: {e}")
        print(f"❌ Watcher error: {e}")

    print("")
    print("📊 Summary:")
    print(f"   Cycles: {cycle}")
    print(f"   Known available days: {len(known_days)}")
    for day in sorted(known_days):
        print(f"   ✅ {day}")
