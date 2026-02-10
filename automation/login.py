#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
STAGE 2: Login - вход в систему
Задача: логин, Cloudflare, кнопка "Войти", SESSION_ACTIVE
"""
import time
from shared_driver import setup_driver, accept_cookies_if_present, screenshots_dir
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

LOGIN_URL = "https://services.vfsglobal.by/blr/ru/pol/login"


def human_behavior(driver):
    """
    Упрощенное человеческое поведение:
    - scroll вниз
    - пауза
    - scroll вверх
    """
    try:
        print("🖱️  Simulating human behavior...")
        driver.execute_script("window.scrollTo(0, 300);")
        time.sleep(0.8)
        driver.execute_script("window.scrollTo(0, 0);")
        time.sleep(0.5)
        print("✅ Human behavior simulated")
    except:
        pass


if __name__ == "__main__":
    print("=" * 60)
    print("🟦 STAGE 2: LOGIN - Вход в систему")
    print("=" * 60)
    
    driver = setup_driver()
    if not driver:
        print("❌ Failed to setup driver")
        exit(1)
    
    try:
        print(f"🌐 Opening: {LOGIN_URL}")
        driver.get(LOGIN_URL)
        time.sleep(3)
        
        # Cookies (из shared_driver)
        accept_cookies_if_present(driver)
        time.sleep(1)
        
        # Check session
        current_url = driver.current_url
        print(f"📍 Current URL: {current_url}")
        
        if "/login" not in current_url:
            print("✅ SESSION_ACTIVE (already logged in)")
            print(f"🎯 Redirected to: {current_url}")
            driver.save_screenshot(f"{screenshots_dir}/stage2_already_logged_in.png")
            print("")
            print("⏸️  PAUSE: Wait 2-5 minutes before Stage 3")
            exit(0)
        
        # ✅ ИСПРАВЛЕНО: Ждем активацию кнопки вместо page_source
        print("⏳ Waiting for page to be ready...")
        time.sleep(5)  # Даем Cloudflare время
        
        # Human behavior
        human_behavior(driver)
        
        # Find button
        print("🔍 Looking for 'Войти' button...")
        button_xpaths = [
            "//button[contains(text(), 'Войти')]",
            "//button[contains(., 'Войти')]",
            "//button[@type='submit']",
        ]
        
        login_button = None
        for xpath in button_xpaths:
            try:
                login_button = WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable((By.XPATH, xpath))
                )
                if login_button and login_button.is_displayed():
                    print(f"✅ Button found and clickable: {xpath}")
                    break
            except:
                continue
        
        if not login_button:
            print("❌ Login button not found")
            driver.save_screenshot(f"{screenshots_dir}/stage2_no_button.png")
            exit(1)
        
        # Scroll to button
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", login_button)
        time.sleep(0.5)
        
        # ✅ ИСПРАВЛЕНО: Hover перед кликом (естественнее)
        try:
            from selenium.webdriver.common.action_chains import ActionChains
            actions = ActionChains(driver)
            actions.move_to_element(login_button).perform()
            time.sleep(0.3)
        except:
            pass
        
        # Click
        print("🖱️  Clicking 'Войти' via JS...")
        driver.execute_script("arguments[0].click();", login_button)
        
        # Wait for redirect
        print("⏳ Waiting for redirect...")
        for i in range(30):
            time.sleep(1)
            current_url = driver.current_url
            if "/login" not in current_url:
                print(f"✅ SESSION_ACTIVE: {current_url}")
                driver.save_screenshot(f"{screenshots_dir}/stage2_logged_in.png")
                print("")
                print("✅ STAGE 2 COMPLETE")
                print("⏸️  PAUSE: Wait 2-5 minutes before Stage 3")
                exit(0)
        
        print("❌ No redirect after 30s")
        driver.save_screenshot(f"{screenshots_dir}/stage2_no_redirect.png")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        driver.save_screenshot(f"{screenshots_dir}/stage2_error.png")
        exit(1)