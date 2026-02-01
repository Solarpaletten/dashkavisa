#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import time
import logging
import tempfile
import subprocess
import shutil
import datetime

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException

# Настройка логирования
log_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "logs")
os.makedirs(log_dir, exist_ok=True)
screenshots_dir = os.path.join(log_dir, "screenshots")
os.makedirs(screenshots_dir, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join(log_dir, "browser.log")),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Загрузка учетных данных из .env
from dotenv import load_dotenv

# Загружаем переменные окружения
load_dotenv()
VFS_EMAIL = os.getenv("VFS_EMAIL")
VFS_PASSWORD = os.getenv("VFS_PASSWORD")
CITY = os.getenv("CITY", "Минск")
VISA_TYPE = os.getenv("VISA_TYPE", "Шенген виза")
CHECK_INTERVAL = int(os.getenv("CHECK_INTERVAL", "60"))
MAX_DATES_TO_SHOW = int(os.getenv("MAX_DATES_TO_SHOW", "5"))

# URL для страниц VFS Global
LOGIN_URL = "https://visa.vfsglobal.com/blr/ru/pol/login"
DASHBOARD_URL = "https://visa.vfsglobal.com/blr/ru/pol/dashboard"
NEW_BOOKING_URL = "https://visa.vfsglobal.com/blr/ru/pol/book-an-appointment"

# v0.4: Persistent Chrome Profile
CHROME_PROFILE_DIR = os.path.join(os.path.expanduser("~"), ".dashkavisa", "chrome_profile")

def cleanup_chrome():
    """Очистка процессов Chrome и временных файлов."""
    try:
        # Завершаем все процессы Chrome и chromedriver
        logger.info("Завершаю все процессы Chrome и chromedriver...")
        try:
            subprocess.run(['killall', '-9', 'chrome'], stderr=subprocess.DEVNULL)
            subprocess.run(['killall', '-9', 'chromedriver'], stderr=subprocess.DEVNULL)
            subprocess.run(['pkill', '-9', '-f', 'chrome'], stderr=subprocess.DEVNULL)
            subprocess.run(['pkill', '-9', '-f', 'chromedriver'], stderr=subprocess.DEVNULL)
        except Exception as e:
            logger.warning(f"Ошибка при завершении процессов: {str(e)}")

        # Очищаем временные файлы
        logger.info("Очищаю временные файлы Chrome...")
        try:
            subprocess.run(['rm', '-rf', '/tmp/chrome_*'], stderr=subprocess.DEVNULL)
            subprocess.run(['rm', '-rf', '/tmp/.com.google.Chrome.*'], stderr=subprocess.DEVNULL)
        except Exception as e:
            logger.warning(f"Ошибка при очистке временных файлов: {str(e)}")

        return True
    except Exception as e:
        logger.error(f"Ошибка при очистке Chrome: {str(e)}")
        return False

def setup_driver():
    """
    Настраивает и возвращает драйвер браузера Chrome.
    v0.4: Persistent Chrome Profile (~/.dashkavisa/chrome_profile)

    Returns:
        webdriver.Chrome: Настроенный драйвер Chrome или None в случае ошибки
    """
    # Очищаем предыдущие процессы Chrome
    cleanup_chrome()

    try:
        # v0.4: Persistent директория (НЕ временная)
        os.makedirs(CHROME_PROFILE_DIR, exist_ok=True)
        logger.info(f"Используется persistent профиль: {CHROME_PROFILE_DIR}")

        # Настраиваем опции Chrome
        options = Options()
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument(f"--user-data-dir={CHROME_PROFILE_DIR}")
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_argument("--window-size=1920,1080")

        # v0.4: --incognito УБРАН — cookies и Cloudflare tokens должны сохраняться

        # Отключаем веб-безопасность для обхода некоторых ограничений
        options.add_argument("--disable-web-security")
        options.add_argument("--allow-running-insecure-content")

        # Устанавливаем user-agent обычного браузера
        options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")

        # Отключаем кеш для получения свежих данных
        options.add_argument("--disable-application-cache")
        options.add_argument("--disable-cache")

        # Отключаем расширения и GPU
        options.add_argument("--disable-extensions")
        options.add_argument("--disable-gpu")

        # Переменные для обхода обнаружения автоматизации
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option("useAutomationExtension", False)

        # Создаем драйвер
        driver = webdriver.Chrome(options=options)

        # Устанавливаем задержку для имитации реального пользователя
        driver.implicitly_wait(5)

        # Удаляем navigator.webdriver флаг для избежания обнаружения
        driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

        # Возвращаем настроенный драйвер
        return driver
    except Exception as e:
        logger.error(f"Ошибка при настройке драйвера: {str(e)}")
        return None

def accept_cookies_if_present(driver, logger, timeout=5):
    """
    v0.4.1: Автоматическое принятие cookie-баннера VFS Global.
    Вызывается ДО проверки логина, чтобы разблокировать DOM.
    Пробует несколько XPath с fallback.
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
            logger.info("Cookie consent accepted automatically")
            return True
        except TimeoutException:
            continue
    logger.info("Cookie banner not found — skipping")
    return False

def login_vfs_global(driver):
    """
    v0.4.1: Hybrid Human-Assisted Login (Cloudflare-safe)

    Функция НЕ логинится сама. Проверяет состояние сохранённой сессии.
    Человек логинится один раз вручную. Бот использует сохранённые cookies.

    Состояния:
        SUCCESS          → сессия жива, URL не /login → return True
        WAIT             → Waiting Room до 120с → потом повторная проверка
        CAPTCHA_REQUIRED → обнаружена капча → лог, return False, браузер НЕ закрывать
        MANUAL_LOGIN     → форма email/password → лог, return False, браузер НЕ закрывать

    Returns:
        bool: True если сессия активна и доступен booking flow, иначе False
    """
    try:
        LOGIN_URL = "https://services.vfsglobal.by/blr/ru/pol/login"

        logger.info(f"Opening VFS Global: {LOGIN_URL}")
        driver.get(LOGIN_URL)

        # Даём странице начать загрузку
        time.sleep(3)

        # v0.4.1: Принять cookie-баннер (если есть) ДО проверки логина
        accept_cookies_if_present(driver, logger)
        time.sleep(1)  # дать DOM обновиться после закрытия баннера

        # ============================================================
        # v0.4.2: SESSION CHECK — пробуем dashboard напрямую
        # URL > DOM. Если сессия жива — dashboard откроется.
        # Login form в DOM не является признаком отсутствия сессии.
        # ============================================================
        DASHBOARD_CHECK_URL = "https://services.vfsglobal.by/blr/ru/pol/dashboard"
        logger.info(f"Checking active session via dashboard: {DASHBOARD_CHECK_URL}")
        driver.get(DASHBOARD_CHECK_URL)
        time.sleep(3)

        if "/dashboard" in driver.current_url:
            logger.info(f"SUCCESS: Active session detected (dashboard)")
            return True

        # Если dashboard не открылся — вернёмся на login для дальнейших проверок
        logger.info("Dashboard not accessible, checking login page state...")
        driver.get(LOGIN_URL)
        time.sleep(3)

        # ============================================================
        # КРИТЕРИЙ УСПЕХА №1: URL уже не /login (сессия жива)
        # ============================================================
        current_url = driver.current_url
        if "login" not in current_url:
            logger.info(f"SUCCESS: Session active, redirected to {current_url}")
            return True

        # ============================================================
        # WAITING ROOM: ждём до 120 секунд (БЕЗ взаимодействия)
        # ============================================================
        waiting_room_timeout = 120
        waiting_room_start = time.time()
        waiting_room_detected = False

        while time.time() - waiting_room_start < waiting_room_timeout:
            page_source = driver.page_source.lower()

            waiting_room_keywords = [
                "вы находитесь в очереди",
                "waiting room",
                "ожидаемое время ожидания",
                "expected wait time",
                "queue-it",
            ]

            is_waiting_room = any(kw in page_source for kw in waiting_room_keywords)

            if is_waiting_room:
                if not waiting_room_detected:
                    waiting_room_detected = True
                    logger.info("WAIT: Cloudflare Waiting Room detected, waiting up to 120s...")

                time.sleep(5)

                # Проверяем — может уже ушли с /login
                current_url = driver.current_url
                if "login" not in current_url:
                    logger.info(f"SUCCESS: Passed Waiting Room, redirected to {current_url}")
                    return True

                continue
            else:
                # Waiting Room пройден или его не было
                break

        if waiting_room_detected:
            elapsed = int(time.time() - waiting_room_start)
            logger.info(f"Waiting Room phase ended after {elapsed}s")

        # ============================================================
        # После Waiting Room — проверяем URL ещё раз
        # ============================================================
        current_url = driver.current_url
        if "login" not in current_url:
            logger.info(f"SUCCESS: Redirected to {current_url}")
            return True

        # ============================================================
        # CAPTCHA DETECT (только обнаружение, 0 кликов)
        # ============================================================
        page_source = driver.page_source.lower()

        captcha_keywords = [
            "подтвердите, что вы человек",
            "verify you are human",
            "cf-challenge",
            "cf-turnstile",
            "captcha",
            "challenge-platform",
            "challenge-form",
        ]

        # Проверяем iframe Cloudflare
        captcha_iframes = driver.find_elements(By.CSS_SELECTOR,
            "iframe[src*='challenges'], iframe[src*='captcha'], iframe[src*='cf-'], iframe[src*='turnstile']")

        is_captcha = any(kw in page_source for kw in captcha_keywords) or len(captcha_iframes) > 0

        if is_captcha:
            logger.warning("=" * 60)
            logger.warning("CAPTCHA_REQUIRED")
            logger.warning("Cloudflare CAPTCHA detected.")
            logger.warning("Please solve CAPTCHA manually in the browser window.")
            logger.warning("Then restart: python automation/browser.py")
            logger.warning("Browser left open intentionally.")
            logger.warning("=" * 60)
            # Скриншот
            screenshot_path = os.path.join(screenshots_dir, f"captcha_detected_{int(time.time())}.png")
            try:
                driver.save_screenshot(screenshot_path)
                logger.info(f"Screenshot: {screenshot_path}")
            except:
                pass
            return False

        # ============================================================
        # LOGIN FORM DETECT (сессия истекла → ручной логин)
        # ============================================================
        login_form_selectors = [
            "input[type='email']",
            "input[type='password']",
            "#mat-input-0",
        ]

        login_form_found = False
        for selector in login_form_selectors:
            try:
                driver.find_element(By.CSS_SELECTOR, selector)
                login_form_found = True
                break
            except:
                continue

        if login_form_found:
            logger.warning("=" * 60)
            logger.warning("MANUAL_LOGIN_REQUIRED")
            logger.warning("Login form detected — session expired or first run.")
            logger.warning("Please login manually in the browser window:")
            logger.warning(f"  URL: {LOGIN_URL}")
            logger.warning(f"  Profile: {CHROME_PROFILE_DIR}")
            logger.warning("After login, close browser and restart bot.")
            logger.warning("=" * 60)
            # Скриншот
            screenshot_path = os.path.join(screenshots_dir, f"login_form_detected_{int(time.time())}.png")
            try:
                driver.save_screenshot(screenshot_path)
                logger.info(f"Screenshot: {screenshot_path}")
            except:
                pass
            return False

        # ============================================================
        # UNKNOWN STATE — ничего не распознано
        # ============================================================
        logger.warning(f"UNKNOWN_STATE: URL={current_url}")
        logger.warning("Could not determine page state. Check screenshot.")
        screenshot_path = os.path.join(screenshots_dir, f"unknown_state_{int(time.time())}.png")
        try:
            driver.save_screenshot(screenshot_path)
            logger.info(f"Screenshot: {screenshot_path}")
        except:
            pass
        return False

    except Exception as e:
        logger.exception(f"Login check error: {e}")
        return False

def start_new_appointment(driver):
    """
    Начинает новую запись на прием и заполняет все необходимые поля.

    Args:
        driver (webdriver.Chrome): Драйвер Chrome

    Returns:
        bool: True, если запись успешно начата, иначе False
    """
    try:
        # Сначала проверяем, находимся ли мы уже на странице dashboard
        if not "dashboard" in driver.current_url:
            # Переходим на dashboard
            logger.info("Переходим на dashboard")
            driver.get(DASHBOARD_URL)
            time.sleep(2)

        # Ищем кнопку "Записаться на прием" и нажимаем на нее
        try:
            book_button = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Записаться на прием')]"))
            )
            book_button.click()
            logger.info("Нажата кнопка 'Записаться на прием'")
        except:
            # Возможно, мы уже перешли на страницу заполнения формы
            logger.warning("Не найдена кнопка 'Записаться на прием', пробуем перейти напрямую")
            driver.get(NEW_BOOKING_URL)

        # Ждем загрузки формы записи
        WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.XPATH, "//*[contains(text(), 'Выберите свой Центр приложений')]"))
        )

        # Сохраняем скриншот страницы записи
        screenshot_path = os.path.join(screenshots_dir, f"booking_page_{int(time.time())}.png")
        driver.save_screenshot(screenshot_path)
        logger.info("Загружена страница записи")

        # Выбираем центр в Минске
        try:
            # Находим dropdown для выбора центра
            center_dropdown = WebDriverWait(driver, 5).until(
                EC.element_to_be_clickable((By.XPATH, "//mat-select[contains(@aria-labelledby, 'mat-form-field') and contains(@formcontrolname, 'center')]"))
            )
            center_dropdown.click()
            time.sleep(1)

            # Выбираем Poland Visa Application Center-Minsk
            center_option = WebDriverWait(driver, 5).until(
                EC.element_to_be_clickable((By.XPATH, "//mat-option//span[contains(text(), 'Poland Visa Application Center-Minsk')]"))
            )
            center_option.click()
            logger.info("Выбран центр: Poland Visa Application Center-Minsk")
            time.sleep(1)
        except Exception as e:
            logger.warning(f"Ошибка при выборе центра: {str(e)}")
            # Возможно, центр уже выбран, продолжаем

        # Выбираем категорию визы (National Visa D)
        try:
            # Находим dropdown для выбора категории
            category_dropdown = WebDriverWait(driver, 5).until(
                EC.element_to_be_clickable((By.XPATH, "//mat-select[contains(@aria-labelledby, 'mat-form-field') and contains(@formcontrolname, 'category')]"))
            )
            category_dropdown.click()
            time.sleep(1)

            # Выбираем National Visa D
            category_option = WebDriverWait(driver, 5).until(
                EC.element_to_be_clickable((By.XPATH, "//mat-option//span[contains(text(), 'National Visa D')]"))
            )
            category_option.click()
            logger.info("Выбрана категория: National Visa D")
            time.sleep(1)
        except Exception as e:
            logger.warning(f"Ошибка при выборе категории визы: {str(e)}")
            # Возможно, категория уже выбрана, продолжаем

        # Выбираем подкатегорию (на скриншоте видно Praca - Oswiadczenie)
        try:
            # Находим dropdown для выбора подкатегории
            subcategory_dropdown = WebDriverWait(driver, 5).until(
                EC.element_to_be_clickable((By.XPATH, "//mat-select[contains(@aria-labelledby, 'mat-form-field') and contains(@formcontrolname, 'subCategory')]"))
            )
            subcategory_dropdown.click()
            time.sleep(1)

            # Выбираем Praca - Oswiadczenie
            subcategory_options = driver.find_elements(By.XPATH, "//mat-option//span")
            for option in subcategory_options:
                if "Praca - Oswiadczenie" in option.text:
                    option.click()
                    logger.info("Выбрана подкатегория: Praca - Oswiadczenie")
                    time.sleep(1)
                    break
            # Если не нашли конкретную опцию, выбираем первую доступную
            if not "Praca - Oswiadczenie" in [option.text for option in subcategory_options]:
                # Выбираем первую подкатегорию в списке
                first_option = WebDriverWait(driver, 5).until(
                    EC.element_to_be_clickable((By.XPATH, "//mat-option[1]"))
                )
                first_option.click()
                logger.info(f"Выбрана подкатегория: {first_option.text}")
                time.sleep(1)
        except Exception as e:
            logger.warning(f"Ошибка при выборе подкатегории: {str(e)}")
            # Возможно, подкатегория уже выбрана, продолжаем

        # Вводим дату рождения
        try:
            birth_date_input = WebDriverWait(driver, 5).until(
                EC.presence_of_element_located((By.XPATH, "//input[@formcontrolname='dateOfBirth']"))
            )
            birth_date_input.clear()
            birth_date_input.send_keys(os.getenv("USER_BIRTH_DATE", "06/09/1957"))
            logger.info(f"Введена дата рождения: {os.getenv('USER_BIRTH_DATE', '06/09/1957')}")
            time.sleep(1)
        except Exception as e:
            logger.warning(f"Ошибка при вводе даты рождения: {str(e)}")
            # Возможно, дата уже введена или поле не требуется на этом этапе

        # Проверяем наличие сообщения о доступности слотов
        try:
            # Ищем сообщение о недоступности слотов
            no_slots_message = driver.find_element(By.XPATH,
                "//div[contains(text(), 'нет доступных слотов') or contains(text(), 'Приносим извинения')]")
            logger.info(f"Найдено сообщение об отсутствии слотов: {no_slots_message.text}")
            # Сохраняем скриншот страницы с сообщением
            screenshot_path = os.path.join(screenshots_dir, f"no_slots_message_{int(time.time())}.png")
            driver.save_screenshot(screenshot_path)
        except:
            # Если сообщение не найдено, возможно, есть доступные слоты
            logger.info("Сообщение об отсутствии слотов не найдено, возможно, есть доступные даты")

        # Нажимаем на кнопку "Продолжить", если она есть
        try:
            continue_button = WebDriverWait(driver, 5).until(
                EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Продолжить')]"))
            )
            continue_button.click()
            logger.info("Нажата кнопка 'Продолжить'")
            time.sleep(2)
        except:
            logger.warning("Кнопка 'Продолжить' не найдена или недоступна")

        # Если мы дошли до этого места, считаем, что начало записи успешно
        logger.info("Процесс поиска слотов запущен успешно")
        return True

    except Exception as e:
        logger.error(f"Ошибка при начале записи: {str(e)}")
        error_screenshot = os.path.join(screenshots_dir, f"booking_error_{int(time.time())}.png")
        try:
            driver.save_screenshot(error_screenshot)
        except:
            pass
        return False

def check_available_dates(driver):
    """
    Проверяет доступные даты для записи на прием.

    Args:
        driver (webdriver.Chrome): Драйвер Chrome

    Returns:
        tuple: (bool, list|str) - (успех, список дат или сообщение об ошибке)
    """
    try:
        # Проверяем наличие сообщения об отсутствии слотов на текущей странице
        try:
            no_slots_message = driver.find_element(By.XPATH,
                "//div[contains(text(), 'нет доступных слотов') or contains(text(), 'Приносим извинения') or contains(text(), 'Места для регистрации')]")
            message_text = no_slots_message.text
            logger.info(f"Найдено сообщение об отсутствии слотов: {message_text}")

            # Делаем скриншот страницы с сообщением
            screenshot_path = os.path.join(screenshots_dir, f"no_slots_available_{int(time.time())}.png")
            driver.save_screenshot(screenshot_path)

            # Возвращаем пустой список дат, но с успешным статусом
            return True, []
        except:
            logger.info("Сообщение об отсутствии слотов не найдено, ищем доступные даты")

        # Проверяем, есть ли календарь с датами
        try:
            # Ищем элементы календаря
            WebDriverWait(driver, 5).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, ".mat-calendar-body, .calendar-container, mat-calendar, .date-selection"))
            )

            # Делаем скриншот календаря
            calendar_screenshot = os.path.join(screenshots_dir, f"calendar_{int(time.time())}.png")
            driver.save_screenshot(calendar_screenshot)
            logger.info("Найден календарь с датами")

            # Ищем все доступные дни (не заблокированные)
            available_dates = []

            # Проверяем доступные даты различными способами (под разные версии UI)

            # Способ 1: Ищем стандартные ячейки календаря
            try:
                calendar_cells = driver.find_elements(By.CSS_SELECTOR,
                    ".mat-calendar-body-cell:not(.mat-calendar-body-disabled), .date-available, td.selectable:not(.disabled)")

                month_name = ""
                try:
                    month_element = driver.find_element(By.CSS_SELECTOR, ".mat-calendar-period-button, .current-month")
                    month_name = month_element.text.strip()
                except:
                    month_name = datetime.datetime.now().strftime("%B %Y")

                for cell in calendar_cells:
                    try:
                        date_text = cell.find_element(By.CSS_SELECTOR,
                            ".mat-calendar-body-cell-content, .date-text").text
                        full_date = f"{date_text} {month_name}"
                        available_dates.append(full_date)
                        logger.info(f"Найдена доступная дата: {full_date}")

                        # Сохраняем атрибуты для возможного клика в будущем
                        cell.location_once_scrolled_into_view

                    except:
                        continue
            except Exception as e:
                logger.warning(f"Ошибка при проверке ячеек календаря (способ 1): {str(e)}")

            # Способ 2: Ищем любые элементы, которые могут содержать даты и быть кликабельными
            if not available_dates:
                try:
                    date_elements = driver.find_elements(By.CSS_SELECTOR,
                        "[class*='date']:not([class*='disabled']), [class*='calendar']:not([class*='disabled'])")

                    for elem in date_elements:
                        try:
                            if elem.is_displayed() and elem.is_enabled():
                                date_text = elem.text.strip()
                                if date_text and any(c.isdigit() for c in date_text):
                                    available_dates.append(date_text)
                                    logger.info(f"Найдена доступная дата (способ 2): {date_text}")
                        except:
                            continue
                except Exception as e:
                    logger.warning(f"Ошибка при проверке элементов дат (способ 2): {str(e)}")

            # Если нашли доступные даты, возвращаем их
            if available_dates:
                logger.info(f"Найдено {len(available_dates)} доступных дат")

                # Сохраняем доп. скриншот страницы с календарем для проверки
                bonus_screenshot = os.path.join(screenshots_dir, f"available_dates_{int(time.time())}.png")
                driver.save_screenshot(bonus_screenshot)

                return True, available_dates
            else:
                logger.info("Календарь найден, но доступных дат нет")
                return True, []

        except Exception as e:
            logger.warning(f"Ошибка при поиске календаря: {str(e)}")

            # Если календарь не найден, это может означать, что доступных дат нет
            # или что сайт показал сообщение об отсутствии слотов
            screenshot_path = os.path.join(screenshots_dir, f"no_calendar_{int(time.time())}.png")
            driver.save_screenshot(screenshot_path)

            return True, []

    except Exception as e:
        logger.error(f"Ошибка при проверке доступных дат: {str(e)}")
        error_screenshot = os.path.join(screenshots_dir, f"calendar_error_{int(time.time())}.png")
        try:
            driver.save_screenshot(error_screenshot)
        except:
            pass
        return False, str(e)

def fill_personal_data(driver, first_name, last_name, birth_date):
    """
    Заполняет личные данные в форме записи.
    
    Args:
        driver (webdriver.Chrome): Драйвер Chrome
        first_name (str): Имя
        last_name (str): Фамилия
        birth_date (str): Дата рождения в формате DD.MM.YYYY
        
    Returns:
        bool: True, если данные успешно заполнены, иначе False
    """
    try:
        # Ожидаем загрузки формы с личными данными
        WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "input[formcontrolname='firstName']"))
        )
        
        # Заполняем поля формы
        first_name_input = driver.find_element(By.CSS_SELECTOR, "input[formcontrolname='firstName']")
        last_name_input = driver.find_element(By.CSS_SELECTOR, "input[formcontrolname='lastName']")
        
        # Очищаем поля и заполняем новыми данными
        first_name_input.clear()
        first_name_input.send_keys(first_name)
        logger.info(f"Введено имя: {first_name}")
        
        last_name_input.clear()
        last_name_input.send_keys(last_name)
        logger.info(f"Введена фамилия: {last_name}")
        
        # Ищем поле для даты рождения (может иметь разный формат ввода)
        try:
            # Вариант 1: Если это обычное текстовое поле
            birth_date_input = driver.find_element(By.CSS_SELECTOR, "input[formcontrolname='dateOfBirth']")
            birth_date_input.clear()
            birth_date_input.send_keys(birth_date)
        except:
            # Вариант 2: Если это поле с датапикером
            birth_date_input = driver.find_element(By.CSS_SELECTOR, "input.mat-datepicker-input")
            birth_date_input.clear()
            birth_date_input.send_keys(birth_date)
        
        logger.info(f"Введена дата рождения: {birth_date}")
        
        # Сохраняем скриншот заполненной формы
        screenshot_path = os.path.join(screenshots_dir, f"personal_data_form_{int(time.time())}.png")
        driver.save_screenshot(screenshot_path)
        
        # Нажимаем кнопку продолжения
        continue_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Продолжить') or contains(text(), 'Continue')]"))
        )
        continue_button.click()
        logger.info("Нажата кнопка продолжения после заполнения личных данных")
        
        return True
        
    except Exception as e:
        logger.error(f"Ошибка при заполнении личных данных: {str(e)}")
        error_screenshot = os.path.join(screenshots_dir, f"personal_data_error_{int(time.time())}.png")
        try:
            driver.save_screenshot(error_screenshot)
        except:
            pass
        return False

# Тест функций, если скрипт запущен напрямую
if __name__ == "__main__":
    try:
        # Тестируем функции
        print("Тестирование функций для работы с браузером...")
        
        # Настраиваем драйвер
        driver = setup_driver()
        if driver:
            print("✅ Драйвер успешно настроен")
            
            # Выполняем вход
            if login_vfs_global(driver):
                print("✅ Вход в VFS Global выполнен успешно")
                
                # Начинаем новую запись
                if start_new_appointment(driver):
                    print("✅ Новая запись успешно начата")
                    
                    # Проверяем доступные даты
                    success, result = check_available_dates(driver)
                    if success:
                        if isinstance(result, list) and result:
                            print(f"✅ Найдены доступные даты: {', '.join(result[:5])}")
                            if len(result) > 5:
                                print(f"...и еще {len(result) - 5} дат")
                        else:
                            print("❌ Доступных дат не найдено")
                    else:
                        print(f"❌ Ошибка при проверке дат: {result}")
                else:
                    print("❌ Не удалось начать новую запись")
            else:
                print("❌ Не удалось войти в VFS Global")
                
            # Освобождаем ресурсы
            driver.quit()
            print("✅ Драйвер закрыт")
        else:
            print("❌ Не удалось настроить драйвер")
            
    except Exception as e:
        print(f"❌ Критическая ошибка при тестировании: {str(e)}")
