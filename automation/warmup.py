#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
STAGE 1: Warmup - прогрев Cloudflare
Задача: открыть публичную страницу, принять cookies, побыть на сайте
"""
import time
from shared_driver import setup_driver, accept_cookies_if_present, screenshots_dir

PUBLIC_URL = "https://visa.vfsglobal.com/blr/ru/pol"


if __name__ == "__main__":
    print("=" * 60)
    print("🟦 STAGE 1: WARMUP - Прогрев Cloudflare")
    print("=" * 60)
    
    # ❌ УБРАНО: cleanup_chrome() - сохраняем накопленный trust
    
    # Setup
    driver = setup_driver()
    if not driver:
        print("❌ Failed to setup driver")
        exit(1)
    
    try:
        print(f"🌐 Opening: {PUBLIC_URL}")
        driver.get(PUBLIC_URL)
        time.sleep(3)
        
        # Accept cookies (из shared_driver)
        accept_cookies_if_present(driver)
        
        # Human-like delay
        print("⏳ Staying on page (human-like behavior)...")
        time.sleep(5)
        
        # Screenshot
        screenshot_path = f"{screenshots_dir}/stage1_warmup.png"
        driver.save_screenshot(screenshot_path)
        print(f"📸 Screenshot: {screenshot_path}")
        
        print("")
        print("✅ STAGE 1 COMPLETE")
        print("🎯 Cloudflare trust established")
        print("🎯 Cookies saved")
        print("")
        print("⏸️  PAUSE: Wait 3-10 minutes before Stage 2")
        print("   Chrome will stay open (detached)")
        print("")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        driver.quit()
        exit(1)