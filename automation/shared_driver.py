#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Общая конфигурация драйвера для всех этапов

setup_driver()  — STAGE 1, 2 (создаёт новый Chrome)
attach_driver() — STAGE 3, 4 (подключается к существующему Chrome)
"""
import os
import time
import logging
import subprocess
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException

# Настройка логирования
log_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "logs")
os.makedirs(log_dir, exist_ok=True)
screenshots_dir = os.path.join(log_dir, "screenshots")
os.makedirs(screenshots_dir, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join(log_dir, "stages.log")),
        logging.StreamHandler()
    ]
)

# Persistent профиль
CHROME_PROFILE_DIR = os.path.join(os.path.expanduser("~"), ".dashkavisa", "chrome_profile")


def cleanup_chrome():
    """
    ⚠️ АВАРИЙНЫЙ ИНСТРУМЕНТ - использовать только вручную!
    НЕ вызывать в stage-файлах автоматически!
    """
    try:
        print("🧹 Аварийная очистка Chrome...")
        
        subprocess.run(['pkill', '-9', '-f', 'Google Chrome'], stderr=subprocess.DEVNULL)
        subprocess.run(['pkill', '-9', '-f', 'chromedriver'], stderr=subprocess.DEVNULL)
        
        singleton_files = [
            f"{CHROME_PROFILE_DIR}/SingletonLock",
            f"{CHROME_PROFILE_DIR}/SingletonCookie",
            f"{CHROME_PROFILE_DIR}/SingletonSocket"
        ]
        for f in singleton_files:
            try:
                os.remove(f)
            except:
                pass
        
        time.sleep(2)
        print("✅ Chrome очищен")
        return True
    except Exception as e:
        print(f"❌ Ошибка очистки: {e}")
        return False


def accept_cookies_if_present(driver, timeout=5):
    """
    Единая функция принятия cookies для всех stage
    """
    xpaths = [
        "//button[contains(., 'Согласиться с использованием всех файлов cookie')]",
        "//button[contains(., 'Согласиться')]",
        "//button[contains(., 'Accept all')]",
    ]
    for xp in xpaths:
        try:
            btn = WebDriverWait(driver, timeout).until(
                EC.element_to_be_clickable((By.XPATH, xp))
            )
            btn.click()
            print("✅ Cookies accepted")
            return True
        except TimeoutException:
            continue
    print("ℹ️  Cookie banner not found")
    return False


def setup_driver():
    """
    Создание НОВОГО Chrome с persistent профилем.
    Использовать ТОЛЬКО в STAGE 1 и STAGE 2.
    """
    try:
        os.makedirs(CHROME_PROFILE_DIR, exist_ok=True)
        
        options = Options()
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument(f"--user-data-dir={CHROME_PROFILE_DIR}")
        options.add_argument("--profile-directory=Default")
        options.add_argument("--no-first-run")
        options.add_argument("--no-default-browser-check")
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_argument("--window-size=1920,1080")
        options.add_argument("--remote-debugging-port=9222")
        
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option("useAutomationExtension", False)
        options.add_experimental_option("detach", True)
        
        driver = webdriver.Chrome(options=options)
        driver.implicitly_wait(5)
        
        return driver
    except Exception as e:
        print(f"❌ Ошибка setup: {e}")
        return None


def attach_driver():
    """
    Подключение к УЖЕ ОТКРЫТОМУ Chrome через remote debugging port 9222.
    Использовать ТОЛЬКО в STAGE 3 и STAGE 4.
    НЕ создаёт новое окно.
    Автоматически переключается на вкладку с VFS.
    """
    try:
        print("🔌 Attaching to existing Chrome (port 9222)...")
        
        options = Options()
        options.add_experimental_option("debuggerAddress", "127.0.0.1:9222")
        
        driver = webdriver.Chrome(options=options)
        
        # Перебираем все вкладки, ищем VFS
        handles = driver.window_handles
        print(f"📑 Found {len(handles)} tab(s)")
        
        vfs_handle = None
        for handle in handles:
            driver.switch_to.window(handle)
            url = driver.current_url
            print(f"   Tab: {url}")
            if "vfsglobal" in url:
                vfs_handle = handle
                break
        
        if vfs_handle:
            driver.switch_to.window(vfs_handle)
            print(f"✅ Attached to VFS tab: {driver.current_url}")
        else:
            print(f"⚠️  No VFS tab found. Current: {driver.current_url}")
        
        return driver
    except Exception as e:
        print(f"❌ Failed to attach to Chrome: {e}")
        print("   Make sure Stage 1-2 have been run and Chrome is open")
        return None
