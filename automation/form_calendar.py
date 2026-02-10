#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
STAGE 3: Form & Calendar - заполнение формы и открытие календаря
Задача: через кнопки дойти до календаря и остановиться
❌ НЕ анализировать даты
❌ НЕ переходить по URL напрямую
✅ ТОЛЬКО UI как человек
"""
import os
import time
from shared_driver import setup_driver, accept_cookies_if_present, screenshots_dir
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException


def human_scroll(driver):
    """Естественный скролл"""
    try:
        driver.execute_script("window.scrollTo(0, 200);")
        time.sleep(0.5)
        driver.execute_script("window.scrollTo(0, 0);")
        time.sleep(0.3)
    except:
        pass


if __name__ == "__main__":
    print("=" * 60)
    print("🟦 STAGE 3: FORM & CALENDAR")
    print("=" * 60)
    
    driver = setup_driver()
    if not driver:
        print("❌ Failed to setup driver")
        exit(1)
    
    try:
        print("🚀 STAGE 3 START")
        
        # 1. Проверка: НЕ на login
        current_url = driver.current_url
        print(f"📍 Current URL: {current_url}")
        
        if "/login" in current_url:
            print("❌ Still on login page - run Stage 2 first!")
            exit(1)
        
        # 2. Принять cookies если есть
        accept_cookies_if_present(driver)
        time.sleep(1)
        
        # 3. Найти кнопку "Записаться на приём"
        print("🔍 Looking for 'Записаться на приём' button...")
        
        appointment_button_xpaths = [
            "//button[contains(text(), 'Записаться на приём')]",
            "//button[contains(text(), 'Записаться на прием')]",
            "//button[contains(., 'Start New Booking')]",
            "//a[contains(@href, 'book-an-appointment')]",
        ]
        
        appointment_button = None
        for xpath in appointment_button_xpaths:
            try:
                appointment_button = WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable((By.XPATH, xpath))
                )
                if appointment_button and appointment_button.is_displayed():
                    print(f"✅ Button found: {xpath}")
                    break
            except TimeoutException:
                continue
        
        if not appointment_button:
            print("⚠️  Button not found, might already be on form page")
        else:
            # Human behavior before click
            human_scroll(driver)
            
            # Scroll to button
            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", appointment_button)
            time.sleep(0.5)
            
            # Click
            print("🖱️  BOOK_APPOINTMENT_CLICKED")
            driver.execute_script("arguments[0].click();", appointment_button)
            time.sleep(3)
        
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
        
        # 5. Минимальное заполнение формы (если требуется)
        print("📝 Checking if form needs filling...")
        
        # Попытка выбрать центр (если dropdown есть)
        try:
            center_dropdown = WebDriverWait(driver, 5).until(
                EC.element_to_be_clickable((By.XPATH, "//mat-select[contains(@formcontrolname, 'center')]"))
            )
            print("🔽 Center dropdown found, selecting...")
            center_dropdown.click()
            time.sleep(1)
            
            # Выбрать первый доступный центр
            first_center = WebDriverWait(driver, 5).until(
                EC.element_to_be_clickable((By.XPATH, "//mat-option[1]"))
            )
            first_center.click()
            print("✅ Center selected")
            time.sleep(1)
        except TimeoutException:
            print("ℹ️  Center already selected or not required")
        
        # Попытка выбрать категорию (если dropdown есть)
        try:
            category_dropdown = WebDriverWait(driver, 5).until(
                EC.element_to_be_clickable((By.XPATH, "//mat-select[contains(@formcontrolname, 'category')]"))
            )
            print("🔽 Category dropdown found, selecting...")
            category_dropdown.click()
            time.sleep(1)
            
            # Выбрать первую доступную категорию
            first_category = WebDriverWait(driver, 5).until(
                EC.element_to_be_clickable((By.XPATH, "//mat-option[1]"))
            )
            first_category.click()
            print("✅ Category selected")
            time.sleep(1)
        except TimeoutException:
            print("ℹ️  Category already selected or not required")
        
        # Ввод даты рождения (если требуется)
        try:
            birth_date_input = WebDriverWait(driver, 3).until(
                EC.presence_of_element_located((By.XPATH, "//input[@formcontrolname='dateOfBirth']"))
            )
            if not birth_date_input.get_attribute('value'):
                birth_date_input.clear()
                birth_date_input.send_keys(os.getenv("USER_BIRTH_DATE", "06/09/1957"))
                print("✅ Birth date entered")
                time.sleep(0.5)
        except TimeoutException:
            print("ℹ️  Birth date not required or already filled")
        
        # 6. Найти кнопку "Продолжить" / "Continue"
        print("🔍 Looking for 'Продолжить' button...")
        
        continue_button_xpaths = [
            "//button[contains(text(), 'Продолжить')]",
            "//button[contains(text(), 'Continue')]",
            "//button[contains(text(), 'Submit')]",
            "//button[@type='submit']",
        ]
        
        continue_button = None
        for xpath in continue_button_xpaths:
            try:
                continue_button = WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable((By.XPATH, xpath))
                )
                if continue_button and continue_button.is_displayed():
                    print(f"✅ Continue button found: {xpath}")
                    break
            except TimeoutException:
                continue
        
        if not continue_button:
            print("❌ Continue button not found")
            driver.save_screenshot(f"{screenshots_dir}/stage3_no_continue.png")
            exit(1)
        
        # Scroll to button
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", continue_button)
        time.sleep(0.5)
        
        # Click
        print("🖱️  CALENDAR_BUTTON_CLICKED")
        driver.execute_script("arguments[0].click();", continue_button)
        time.sleep(5)
        
        # 7. Дождаться появления календаря
        print("⏳ Waiting for calendar...")
        
        calendar_selectors = [
            ".mat-calendar-body",
            "mat-calendar",
            "[class*='calendar']",
            ".mat-datepicker-content",
        ]
        
        calendar_found = False
        for selector in calendar_selectors:
            try:
                WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, selector))
                )
                print(f"✅ Calendar found: {selector}")
                calendar_found = True
                break
            except TimeoutException:
                continue
        
        if not calendar_found:
            # Проверяем сообщение "нет слотов"
            try:
                no_slots = driver.find_element(By.XPATH, "//div[contains(text(), 'нет доступных слотов') or contains(text(), 'No slots')]")
                if no_slots:
                    print("ℹ️  Calendar area loaded but no slots available")
                    calendar_found = True
            except:
                pass
        
        if not calendar_found:
            print("❌ Calendar not found")
            driver.save_screenshot(f"{screenshots_dir}/stage3_no_calendar.png")
            exit(1)
        
        # 8. Скриншот
        print("📸 Taking screenshot...")
        screenshot_path = f"{screenshots_dir}/stage3_calendar_ready.png"
        driver.save_screenshot(screenshot_path)
        print(f"✅ Screenshot: {screenshot_path}")
        
        # 9. Финальный лог
        print("")
        print("✅ CALENDAR_READY")
        print("✅ STAGE 3 COMPLETE")
        print("")
        print("🎯 Calendar is open and ready")
        print("🎯 Browser parked at calendar page")
        print("")
        print("⏸️  NEXT: Run main.py for date analysis")
        print("   (separate process, read-only bot)")
        print("")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        driver.save_screenshot(f"{screenshots_dir}/stage3_error.png")
        exit(1)