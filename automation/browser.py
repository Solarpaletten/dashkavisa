#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import time
import random
import logging
import tempfile
import shutil
import subprocess
import datetime
from pathlib import Path
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

    Returns:
        webdriver.Chrome: Настроенный драйвер Chrome или None в случае ошибки
    """
    # Очищаем предыдущие процессы Chrome
    cleanup_chrome()

    try:
        # Создаем временную директорию для профиля
        profile_dir = tempfile.mkdtemp(prefix=f"chrome_profile_{int(time.time())}_")
        logger.info(f"Создана временная директория для профиля: {profile_dir}")

        # Настраиваем опции Chrome
        options = Options()
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument(f"--user-data-dir={profile_dir}")
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_argument("--window-size=1920,1080")

        # Режим инкогнито (помогает обойти ограничения сайта)
        options.add_argument("--incognito")

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
        # Очищаем временную директорию при ошибке
        if 'profile_dir' in locals():
            try:
                shutil.rmtree(profile_dir, ignore_errors=True)
            except:
                pass
        return None

def login_vfs_global(driver):
    """
    Выполняет вход в аккаунт VFS Global.
    
    Args:
        driver (webdriver.Chrome): Драйвер Chrome
        
    Returns:
        bool: True, если вход успешен, иначе False
    """
    try:
        # Проверяем наличие учетных данных
        if not VFS_EMAIL or not VFS_PASSWORD:
            logger.error("Не найдены учетные данные VFS Global в переменных окружения")
            return False
        
        logger.info(f"Открываю страницу авторизации: {LOGIN_URL}")
        driver.get(LOGIN_URL)
        
        # Ждем загрузки формы авторизации
        WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.ID, "mat-input-0"))
        )
        
        # Сохраняем скриншот страницы и исходный код для анализа
        screenshot_path = os.path.join(screenshots_dir, f"login_page_initial_{int(time.time())}.png")
        driver.save_screenshot(screenshot_path)
        
        # Сохраняем исходный код страницы для анализа
        source_path = os.path.join(screenshots_dir, f"login_page_source_{int(time.time())}.html")
        with open(source_path, "w", encoding="utf-8") as f:
            f.write(driver.page_source)
        
        # Проверяем наличие капчи
        if "captcha" in driver.page_source.lower() or "recaptcha" in driver.page_source.lower():
            logger.warning("Обнаружена капча на странице входа!")
            captcha_screenshot = os.path.join(screenshots_dir, f"captcha_detected_{int(time.time())}.png")
            driver.save_screenshot(captcha_screenshot)
            return False
        
        # Ввод email и пароля
        email_input = driver.find_element(By.ID, "mat-input-0")
        password_input = driver.find_element(By.ID, "mat-input-1")
        
        email_input.clear()
        email_input.send_keys(VFS_EMAIL)
        logger.info(f"Введен email: {VFS_EMAIL}")
        
        password_input.clear()
        password_input.send_keys(VFS_PASSWORD)
        logger.info("Введен пароль")
        
        # Ищем и нажимаем кнопку входа
        # Сначала пробуем найти по тексту на русском
        try:
            login_button = WebDriverWait(driver, 5).until(
                EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Войти')]"))
            )
        except:
            # Если не найдена кнопка на русском, ищем на английском
            login_button = WebDriverWait(driver, 5).until(
                EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Login')]"))
            )
        
        login_button.click()
        logger.info("Нажата кнопка входа")
        
        # Ждем перехода на страницу после авторизации
        try:
            WebDriverWait(driver, 20).until(
                EC.url_contains("dashboard")
            )
            logger.info("Успешный вход! Перешли на dashboard")
            
            # Делаем скриншот дашборда
            dashboard_screenshot = os.path.join(screenshots_dir, f"dashboard_{int(time.time())}.png")
            driver.save_screenshot(dashboard_screenshot)
            
            return True
            
        except TimeoutException:
            # Если не перешли на dashboard, проверяем наличие ошибки
            logger.error("Не удалось перейти на dashboard после входа")
            error_screenshot = os.path.join(screenshots_dir, f"login_error_{int(time.time())}.png")
            driver.save_screenshot(error_screenshot)
            return False
            
    except Exception as e:
        logger.error(f"Ошибка при входе в VFS Global: {str(e)}")
        error_screenshot = os.path.join(screenshots_dir, f"login_exception_{int(time.time())}.png")
        try:
            driver.save_screenshot(error_screenshot)
        except:
            pass
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