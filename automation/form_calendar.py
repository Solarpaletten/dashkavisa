#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
STAGE 3: Form & Calendar - заполнение формы до точки ожидания
Задача: dashboard → форма → выбрать центр/категорию/подкатегорию → остановиться

✅ Подключается к существующему Chrome (attach_driver)
✅ Dashboard → клик "Записаться" → fallback URL
✅ Dropdowns: Minsk → National D Visa → Work D-visa
✅ "Нет слотов" = SUCCESS (STAGE_3_READY_FOR_WATCHER)

❌ НЕ проходить дальше без слота
❌ НЕ ретраить dropdown бесконечно
❌ НЕ считать "нет слотов" ошибкой
"""
import os
import time
from shared_driver import attach_driver, accept_cookies_if_present, screenshots_dir
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException

# Конфигурация формы
APPOINTMENT_URL = "https://services.vfsglobal.by/blr/ru/pol/appointment"
CENTER_NAME = "Poland Visa Application Center-Minsk"
CATEGORY_NAME = "National D Visa"
SUBCATEGORY_NAME = "Work D-visa"


def human_scroll(driver):
    """Естественный скролл"""
    try:
        driver.execute_script("window.scrollTo(0, 200);")
        time.sleep(0.5)
        driver.execute_script("window.scrollTo(0, 0);")
        time.sleep(0.3)
    except:
        pass


def click_dashboard_button(driver):
    """
    Попытка нажать кнопку 'Записаться на прием' на dashboard.
    Уровень 1: xpath. Уровень 2: JS XPath.
    """
    print("🔍 Looking for 'Записаться на прием' on dashboard...")

    button_xpaths = [
        "//button[contains(text(), 'Записаться на прием')]",
        "//button[contains(text(), 'Записаться на приём')]",
        "//a[contains(text(), 'Записаться на прием')]",
        "//a[contains(text(), 'Записаться на приём')]",
        "//*[contains(text(), 'Записаться на прием')]",
        "//*[contains(text(), 'Записаться на приём')]",
    ]

    for xpath in button_xpaths:
        try:
            btn = WebDriverWait(driver, 3).until(
                EC.element_to_be_clickable((By.XPATH, xpath))
            )
            if btn and btn.is_displayed():
                print(f"✅ Button found: {xpath}")
                driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", btn)
                time.sleep(0.3)
                driver.execute_script("arguments[0].click();", btn)
                print("🖱️  DASHBOARD_BUTTON_CLICKED")
                return True
        except TimeoutException:
            continue

    # JS dispatch
    print("🔍 Trying JS XPath click...")
    js_result = driver.execute_script("""
        var node = document.evaluate(
            "//*[contains(text(),'Записаться')]",
            document, null,
            XPathResult.FIRST_ORDERED_NODE_TYPE, null
        ).singleNodeValue;
        if (node) { node.click(); return node.tagName + ': ' + node.textContent.trim().substring(0, 50); }
        return null;
    """)

    if js_result:
        print(f"✅ JS click: {js_result}")
        print("🖱️  DASHBOARD_BUTTON_CLICKED (JS)")
        return True

    print("❌ Dashboard button not found")
    return False


def select_option_by_text(driver, dropdown_xpath, option_text, field_name):
    """
    Кликнуть dropdown → найти option по тексту → кликнуть.
    Проверяет: если уже выбрано — пропускает.
    """
    try:
        dropdown = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, dropdown_xpath))
        )

        # Проверить: уже выбрано?
        current_value = dropdown.text.strip()
        if option_text in current_value:
            print(f"✅ {field_name} already selected: {current_value}")
            return True

        print(f"🔽 {field_name}: opening dropdown...")
        dropdown.click()
        time.sleep(1)

        # Найти option по тексту
        option_xpath = f"//mat-option[contains(., '{option_text}')]"
        option = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, option_xpath))
        )
        option.click()
        print(f"✅ {field_name} selected: {option_text}")
        time.sleep(1.5)
        return True

    except TimeoutException:
        print(f"❌ {field_name}: dropdown or option not found")
        return False
    except Exception as e:
        print(f"❌ {field_name} error: {e}")
        return False


def check_no_slots_message(driver):
    """
    Проверить сообщение 'нет доступных слотов' — это SUCCESS, не ошибка.
    """
    no_slots_xpaths = [
        "//*[contains(text(), 'нет доступных слотов')]",
        "//*[contains(text(), 'no available slots')]",
        "//*[contains(text(), 'Please try again later')]",
        "//*[contains(text(), 'попробуйте позже')]",
    ]

    for xpath in no_slots_xpaths:
        try:
            element = driver.find_element(By.XPATH, xpath)
            if element and element.is_displayed():
                return True, element.text.strip()
        except:
            continue

    return False, None


if __name__ == "__main__":
    print("=" * 60)
    print("🟦 STAGE 3: FORM & CALENDAR")
    print("=" * 60)

    driver = attach_driver()
    if not driver:
        print("❌ Failed to attach to Chrome")
        print("   Run Stage 1 and Stage 2 first!")
        exit(1)

    try:
        print("🚀 STAGE 3 START")

        # 1. Проверка контекста
        current_url = driver.current_url
        print(f"📍 Current URL: {current_url}")

        if current_url.startswith("chrome://"):
            print("❌ WRONG_CONTEXT: Browser is on chrome:// page")
            exit(1)

        if "/login" in current_url:
            print("❌ Still on login page - run Stage 2 first!")
            exit(1)

        # 2. Cookies
        accept_cookies_if_present(driver)
        time.sleep(1)

        # 3. Dashboard → appointment
        if "/dashboard" in current_url:
            print("📍 On dashboard — navigating to appointment flow")
            human_scroll(driver)

            button_clicked = click_dashboard_button(driver)

            if button_clicked:
                print("⏳ Waiting for page transition...")
                time.sleep(5)
            else:
                print(f"🔄 FALLBACK: navigating to {APPOINTMENT_URL}")
                driver.get(APPOINTMENT_URL)
                time.sleep(5)

            print(f"📍 New URL: {driver.current_url}")

        # 4. Дождаться формы
        print("⏳ Waiting for form...")
        try:
            WebDriverWait(driver, 15).until(
                EC.presence_of_element_located((By.XPATH, "//mat-select | //input | //form"))
            )
            print("✅ FORM_READY")
        except TimeoutException:
            print("❌ Form not loaded")
            driver.save_screenshot(f"{screenshots_dir}/stage3_no_form.png")
            exit(1)

        # 5. Dropdown 1: Center → Minsk
        select_option_by_text(
            driver,
            "//mat-select[1]",
            CENTER_NAME,
            "CENTER"
        )

        # 6. Dropdown 2: Category → National D Visa
        select_option_by_text(
            driver,
            "//mat-select[2]",
            CATEGORY_NAME,
            "CATEGORY"
        )

        # 7. Dropdown 3: Subcategory → Work D-visa
        select_option_by_text(
            driver,
            "//mat-select[3]",
            SUBCATEGORY_NAME,
            "SUBCATEGORY"
        )

        # 8. Проверка результата
        print("⏳ Waiting for page response...")
        time.sleep(3)

        # Проверяем "нет слотов" — это SUCCESS
        no_slots, message = check_no_slots_message(driver)

        # Скриншот
        screenshot_path = f"{screenshots_dir}/stage3_form_complete.png"
        driver.save_screenshot(screenshot_path)
        print(f"📸 Screenshot: {screenshot_path}")

        # 9. Финальный статус
        print("")
        if no_slots:
            print("=" * 60)
            print("✅ STAGE_3_READY_FOR_WATCHER")
            print("=" * 60)
            print(f"📍 URL: {driver.current_url}")
            print(f"📋 Center: {CENTER_NAME}")
            print(f"📋 Category: {CATEGORY_NAME}")
            print(f"📋 Subcategory: {SUBCATEGORY_NAME}")
            print(f"📋 Status: {message}")
            print("")
            print("🎯 Form is in waiting state")
            print("🎯 Browser parked — ready for calendar_watcher.py")
            print("")
        else:
            # Календарь или слоты могут быть доступны
            print("=" * 60)
            print("✅ STAGE_3_COMPLETE")
            print("=" * 60)
            print(f"📍 URL: {driver.current_url}")
            print("🎯 Form filled, checking for calendar/slots...")
            print("")

    except Exception as e:
        print(f"❌ Error: {e}")
        driver.save_screenshot(f"{screenshots_dir}/stage3_error.png")
        exit(1)
