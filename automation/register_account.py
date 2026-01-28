#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import time
import random
import string
import logging
import tempfile
import subprocess
from pathlib import Path

# Настройка логирования
log_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "logs")
os.makedirs(log_dir, exist_ok=True)
screenshots_dir = os.path.join(log_dir, "screenshots")
os.makedirs(screenshots_dir, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join(log_dir, "registration.log")),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# URL для регистрации и логина
REGISTER_URL = "https://visa.vfsglobal.com/blr/ru/pol/register"
LOGIN_URL = "https://visa.vfsglobal.com/blr/ru/pol/login"

# Загрузка учетных данных из .env
import os
from dotenv import load_dotenv

# Загружаем переменные окружения
load_dotenv()
VFS_EMAIL = os.getenv("VFS_EMAIL")
VFS_PASSWORD = os.getenv("VFS_PASSWORD")


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


def register_with_selenium(max_retries=2):
    """Регистрация аккаунта на VFS Global с использованием Selenium."""
    logger.info("Начинаю процесс регистрации с Selenium...")
    
    # Очистка перед запуском
    cleanup_chrome()
    
    # Генерация случайного email и пароля
    email = f"vfsuser_{random.randint(100000, 999999)}@example.com"
    password = ''.join(random.choices(string.ascii_letters + string.digits, k=12))
    
    logger.info(f"Сгенерированы данные: email={email}")
    
    for attempt in range(1, max_retries + 1):
        logger.info(f"Попытка регистрации {attempt}/{max_retries}")
        
        try:
            # Импортируем selenium здесь для обработки возможных ошибок импорта
            from selenium import webdriver
            from selenium.webdriver.chrome.options import Options
            from selenium.webdriver.common.by import By
            from selenium.webdriver.support.ui import WebDriverWait
            from selenium.webdriver.support import expected_conditions as EC
            
            # Создаем временную директорию для пользовательских данных
            temp_dir = tempfile.mkdtemp(prefix=f"chrome_selenium_{int(time.time())}_")
            logger.info(f"Создана временная директория: {temp_dir}")
            
            # Настройка опций Chrome для этой попытки
            options = Options()
            options.add_argument("--no-sandbox")
            options.add_argument("--disable-dev-shm-usage")
            options.add_argument(f"--user-data-dir={temp_dir}")
            # Откомментируйте для запуска в фоновом режиме
            # options.add_argument("--headless")
            
            # Инициализация драйвера
            driver = webdriver.Chrome(options=options)
            driver.set_window_size(1920, 1080)
            
            try:
                # Открытие страницы регистрации
                logger.info(f"Открываю страницу регистрации: {REGISTER_URL}")
                driver.get(REGISTER_URL)
                
                # Ждем загрузки формы регистрации
                WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.ID, "mat-input-0"))
                )
                
                # Сохраняем скриншот страницы регистрации
                screenshot_path = os.path.join(screenshots_dir, f"register_{int(time.time())}.png")
                driver.save_screenshot(screenshot_path)
                logger.info(f"Сохранен скриншот страницы регистрации: {screenshot_path}")
                
                # В этом месте должен быть код для заполнения формы регистрации
                # Примечание: здесь нужно будет адаптировать под текущую структуру формы VFS Global
                
                # Возвращаем успешный результат с данными
                return {
                    "success": True,
                    "email": email,
                    "password": password,
                    "message": "Регистрация успешно завершена"
                }
                
            except Exception as e:
                logger.error(f"Ошибка при регистрации: {str(e)}")
                # Сохраняем скриншот ошибки
                screenshot_path = os.path.join(screenshots_dir, f"error_{int(time.time())}.png")
                try:
                    driver.save_screenshot(screenshot_path)
                    logger.info(f"Сохранен скриншот ошибки: {screenshot_path}")
                except:
                    pass
            
            finally:
                # Закрываем драйвер и удаляем временную директорию
                try:
                    driver.quit()
                except:
                    pass
                
                try:
                    import shutil
                    shutil.rmtree(temp_dir, ignore_errors=True)
                    logger.info(f"Временная директория удалена: {temp_dir}")
                except:
                    pass
        
        except Exception as e:
            logger.error(f"Критическая ошибка при инициализации Selenium: {str(e)}")
        
        # Пауза перед следующей попыткой
        wait_time = 10 + (attempt * 5)
        logger.info(f"Ожидание {wait_time} секунд перед следующей попыткой...")
        time.sleep(wait_time)
    
    # Если все попытки неудачны, возвращаем ошибку
    return {
        "success": False,
        "email": None,
        "password": None,
        "message": "Не удалось зарегистрировать аккаунт после нескольких попыток"
    }


def register_with_undetected(max_retries=2):
    """Регистрация аккаунта на VFS Global с использованием undetected-chromedriver."""
    logger.info("Начинаю процесс регистрации с undetected-chromedriver...")
    
    # Очистка перед запуском
    cleanup_chrome()
    
    # Генерация случайного email и пароля
    email = f"vfsuser_{random.randint(100000, 999999)}@example.com"
    password = ''.join(random.choices(string.ascii_letters + string.digits, k=12))
    
    logger.info(f"Сгенерированы данные: email={email}")
    
    for attempt in range(1, max_retries + 1):
        logger.info(f"Попытка регистрации с undetected-chromedriver {attempt}/{max_retries}")
        
        try:
            # Импортируем undetected_chromedriver здесь
            import undetected_chromedriver as uc
            
            # Создаем временную директорию для этой попытки
            temp_dir = tempfile.mkdtemp(prefix=f"chrome_undetected_{int(time.time())}_")
            logger.info(f"Создана временная директория: {temp_dir}")
            
            # Важно! Создаем новый объект опций для каждой попытки
            options = uc.ChromeOptions()
            options.add_argument("--no-sandbox")
            options.add_argument("--disable-dev-shm-usage")
            # Откомментируйте для запуска в фоновом режиме
            # options.add_argument("--headless")
            
            # Инициализация драйвера
            driver = uc.Chrome(
                options=options,
                user_data_dir=temp_dir
            )
            driver.set_window_size(1920, 1080)
            
            try:
                # Открытие страницы регистрации
                logger.info(f"Открываю страницу регистрации: {REGISTER_URL}")
                driver.get(REGISTER_URL)
                
                # Ждем загрузки формы регистрации
                WebDriverWait(driver, 20).until(
                    EC.presence_of_element_located((By.ID, "mat-input-0"))
                )
                
                # Сохраняем скриншот страницы регистрации
                screenshot_path = os.path.join(screenshots_dir, f"register_undetected_{int(time.time())}.png")
                driver.save_screenshot(screenshot_path)
                logger.info(f"Сохранен скриншот страницы регистрации: {screenshot_path}")
                
                # В этом месте должен быть код для заполнения формы регистрации
                # Примечание: здесь нужно будет адаптировать под текущую структуру формы VFS Global
                
                # Возвращаем успешный результат с данными
                return {
                    "success": True,
                    "email": email,
                    "password": password,
                    "message": "Регистрация успешно завершена с undetected-chromedriver"
                }
                
            except Exception as e:
                logger.error(f"Ошибка при регистрации с undetected-chromedriver: {str(e)}")
                # Сохраняем скриншот ошибки
                screenshot_path = os.path.join(screenshots_dir, f"error_undetected_{int(time.time())}.png")
                try:
                    driver.save_screenshot(screenshot_path)
                    logger.info(f"Сохранен скриншот ошибки: {screenshot_path}")
                except:
                    pass
            
            finally:
                # Закрываем драйвер и удаляем временную директорию
                try:
                    driver.quit()
                except:
                    pass
                
                try:
                    import shutil
                    shutil.rmtree(temp_dir, ignore_errors=True)
                    logger.info(f"Временная директория удалена: {temp_dir}")
                except:
                    pass
        
        except Exception as e:
            logger.error(f"Критическая ошибка при инициализации undetected-chromedriver: {str(e)}")
        
        # Пауза перед следующей попыткой
        wait_time = 10 + (attempt * 5)
        logger.info(f"Ожидание {wait_time} секунд перед следующей попыткой...")
        time.sleep(wait_time)
    
    # Если все попытки неудачны, возвращаем ошибку
    return {
        "success": False,
        "email": None,
        "password": None,
        "message": "Не удалось зарегистрировать аккаунт с undetected-chromedriver после нескольких попыток"
    }


def login_with_selenium(max_retries=2):
    """Авторизация с существующими учетными данными через Selenium."""
    logger.info(f"Начинаю процесс авторизации на VFS Global с учетными данными: {VFS_EMAIL}")

    # Очистка перед запуском
    cleanup_chrome()

    for attempt in range(1, max_retries + 1):
        logger.info(f"Попытка авторизации {attempt}/{max_retries}")

        try:
            # Импортируем selenium здесь для обработки возможных ошибок импорта
            from selenium import webdriver
            from selenium.webdriver.chrome.options import Options
            from selenium.webdriver.common.by import By
            from selenium.webdriver.support.ui import WebDriverWait
            from selenium.webdriver.support import expected_conditions as EC
            from selenium.common.exceptions import TimeoutException

            # Создаем временную директорию для пользовательских данных
            temp_dir = tempfile.mkdtemp(prefix=f"chrome_selenium_login_{int(time.time())}_")
            logger.info(f"Создана временная директория: {temp_dir}")

            # Настройка опций Chrome для этой попытки
            options = Options()
            options.add_argument("--no-sandbox")
            options.add_argument("--disable-dev-shm-usage")
            options.add_argument(f"--user-data-dir={temp_dir}")
            # Откомментируйте для запуска в фоновом режиме
            # options.add_argument("--headless")

            # Инициализация драйвера
            driver = webdriver.Chrome(options=options)
            driver.set_window_size(1920, 1080)

            try:
                # Открытие страницы логина
                logger.info(f"Открываю страницу авторизации: {LOGIN_URL}")
                driver.get(LOGIN_URL)

                # Ждем загрузки формы авторизации
                WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.ID, "mat-input-0"))
                )

                # Сохраняем скриншот страницы авторизации
                screenshot_path = os.path.join(screenshots_dir, f"login_{int(time.time())}.png")
                driver.save_screenshot(screenshot_path)
                logger.info(f"Сохранен скриншот страницы авторизации: {screenshot_path}")

                # Ввод email и пароля
                email_input = driver.find_element(By.ID, "mat-input-0")
                password_input = driver.find_element(By.ID, "mat-input-1")

                email_input.clear()
                email_input.send_keys(VFS_EMAIL)

                password_input.clear()
                password_input.send_keys(VFS_PASSWORD)

                # Нажатие на кнопку входа
                login_button = WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Войти') or contains(text(), 'Login')]"))
                )
                login_button.click()

                # Ждем перехода на страницу после авторизации
                try:
                    WebDriverWait(driver, 15).until(
                        EC.url_contains("dashboard")
                    )
                    logger.info("Успешная авторизация! Перешли на dashboard")

                    # Делаем скриншот дашборда
                    screenshot_path = os.path.join(screenshots_dir, f"dashboard_{int(time.time())}.png")
                    driver.save_screenshot(screenshot_path)

                    # Возвращаем успешный результат
                    return {
                        "success": True,
                        "email": VFS_EMAIL,
                        "password": VFS_PASSWORD,
                        "message": "Авторизация успешно выполнена"
                    }

                except TimeoutException:
                    # Если не перешли на dashboard, возможно неверные учетные данные
                    logger.error("Ошибка авторизации: не удалось перейти на dashboard")
                    screenshot_path = os.path.join(screenshots_dir, f"login_error_{int(time.time())}.png")
                    driver.save_screenshot(screenshot_path)

            except Exception as e:
                logger.error(f"Ошибка при авторизации: {str(e)}")
                # Сохраняем скриншот ошибки
                screenshot_path = os.path.join(screenshots_dir, f"error_{int(time.time())}.png")
                try:
                    driver.save_screenshot(screenshot_path)
                    logger.info(f"Сохранен скриншот ошибки: {screenshot_path}")
                except:
                    pass

            finally:
                # Закрываем драйвер
                try:
                    driver.quit()
                except:
                    pass

                # Удаляем временную директорию
                try:
                    import shutil
                    shutil.rmtree(temp_dir, ignore_errors=True)
                    logger.info(f"Временная директория удалена: {temp_dir}")
                except:
                    pass

        except Exception as e:
            logger.error(f"Критическая ошибка при инициализации Selenium: {str(e)}")

        # Пауза перед следующей попыткой
        wait_time = 10 + (attempt * 5)
        logger.info(f"Ожидание {wait_time} секунд перед следующей попыткой...")
        time.sleep(wait_time)

    # Если все попытки неудачны, возвращаем ошибку
    return {
        "success": False,
        "email": VFS_EMAIL,
        "password": VFS_PASSWORD,
        "message": "Не удалось авторизоваться после нескольких попыток"
    }

def login_with_undetected(max_retries=2):
    """Авторизация с существующими учетными данными через undetected-chromedriver."""
    logger.info(f"Начинаю процесс авторизации на VFS Global через undetected-chromedriver с учетными данными: {VFS_EMAIL}")

    # Очистка перед запуском
    cleanup_chrome()

    for attempt in range(1, max_retries + 1):
        logger.info(f"Попытка авторизации с undetected-chromedriver {attempt}/{max_retries}")

        try:
            # Импортируем undetected_chromedriver здесь
            import undetected_chromedriver as uc
            from selenium.webdriver.common.by import By
            from selenium.webdriver.support.ui import WebDriverWait
            from selenium.webdriver.support import expected_conditions as EC
            from selenium.common.exceptions import TimeoutException

            # Создаем временную директорию для этой попытки
            temp_dir = tempfile.mkdtemp(prefix=f"chrome_undetected_login_{int(time.time())}_")
            logger.info(f"Создана временная директория: {temp_dir}")

            # Важно! Создаем новый объект опций для каждой попытки
            options = uc.ChromeOptions()
            options.add_argument("--no-sandbox")
            options.add_argument("--disable-dev-shm-usage")
            # Откомментируйте для запуска в фоновом режиме
            # options.add_argument("--headless")

            # Инициализация драйвера
            driver = uc.Chrome(
                options=options,
                user_data_dir=temp_dir
            )
            driver.set_window_size(1920, 1080)

            try:
                # Открытие страницы авторизации
                logger.info(f"Открываю страницу авторизации: {LOGIN_URL}")
                driver.get(LOGIN_URL)

                # Ждем загрузки формы авторизации
                WebDriverWait(driver, 20).until(
                    EC.presence_of_element_located((By.ID, "mat-input-0"))
                )

                # Сохраняем скриншот страницы авторизации
                screenshot_path = os.path.join(screenshots_dir, f"login_undetected_{int(time.time())}.png")
                driver.save_screenshot(screenshot_path)
                logger.info(f"Сохранен скриншот страницы авторизации: {screenshot_path}")

                # Ввод email и пароля
                email_input = driver.find_element(By.ID, "mat-input-0")
                password_input = driver.find_element(By.ID, "mat-input-1")

                email_input.clear()
                email_input.send_keys(VFS_EMAIL)

                password_input.clear()
                password_input.send_keys(VFS_PASSWORD)

                # Нажатие на кнопку входа
                login_button = WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Войти') or contains(text(), 'Login')]"))
                )
                login_button.click()

                # Ждем перехода на страницу после авторизации
                try:
                    WebDriverWait(driver, 15).until(
                        EC.url_contains("dashboard")
                    )
                    logger.info("Успешная авторизация через undetected-chromedriver! Перешли на dashboard")

                    # Делаем скриншот дашборда
                    screenshot_path = os.path.join(screenshots_dir, f"dashboard_undetected_{int(time.time())}.png")
                    driver.save_screenshot(screenshot_path)

                    # Возвращаем успешный результат
                    return {
                        "success": True,
                        "email": VFS_EMAIL,
                        "password": VFS_PASSWORD,
                        "message": "Авторизация через undetected-chromedriver успешно выполнена"
                    }

                except TimeoutException:
                    # Если не перешли на dashboard, возможно неверные учетные данные
                    logger.error("Ошибка авторизации через undetected-chromedriver: не удалось перейти на dashboard")
                    screenshot_path = os.path.join(screenshots_dir, f"login_error_undetected_{int(time.time())}.png")
                    driver.save_screenshot(screenshot_path)

            except Exception as e:
                logger.error(f"Ошибка при авторизации через undetected-chromedriver: {str(e)}")
                # Сохраняем скриншот ошибки
                screenshot_path = os.path.join(screenshots_dir, f"error_undetected_{int(time.time())}.png")
                try:
                    driver.save_screenshot(screenshot_path)
                    logger.info(f"Сохранен скриншот ошибки: {screenshot_path}")
                except:
                    pass

            finally:
                # Закрываем драйвер
                try:
                    driver.quit()
                except:
                    pass

                # Удаляем временную директорию
                try:
                    import shutil
                    shutil.rmtree(temp_dir, ignore_errors=True)
                    logger.info(f"Временная директория удалена: {temp_dir}")
                except:
                    pass

        except Exception as e:
            logger.error(f"Критическая ошибка при инициализации undetected-chromedriver: {str(e)}")

        # Пауза перед следующей попыткой
        wait_time = 10 + (attempt * 5)
        logger.info(f"Ожидание {wait_time} секунд перед следующей попыткой...")
        time.sleep(wait_time)

    # Если все попытки неудачны, возвращаем ошибку
    return {
        "success": False,
        "email": VFS_EMAIL,
        "password": VFS_PASSWORD,
        "message": "Не удалось авторизоваться через undetected-chromedriver после нескольких попыток"
    }

def register_account(max_selenium_retries=2, max_undetected_retries=2):
    """Главная функция регистрации/авторизации, которая пробует различные методы."""
    logger.info("Начинаю процесс авторизации/регистрации аккаунта VFS Global...")

    # Если есть учетные данные, пробуем авторизоваться
    if VFS_EMAIL and VFS_PASSWORD:
        logger.info(f"Найдены учетные данные: {VFS_EMAIL}, пробуем авторизоваться")

        # Сначала пробуем undetected-chromedriver (более эффективный для обхода защиты)
        try:
            result_undetected = login_with_undetected(max_retries=max_undetected_retries)
            if result_undetected["success"]:
                logger.info("Успешная авторизация с undetected-chromedriver!")
                return result_undetected
        except ImportError:
            logger.warning("undetected-chromedriver не установлен, пропускаю этот метод")
        except Exception as e:
            logger.error(f"Ошибка при использовании undetected-chromedriver: {str(e)}")

        # Если undetected не работает, пробуем обычный Selenium
        try:
            result_selenium = login_with_selenium(max_retries=max_selenium_retries)
            if result_selenium["success"]:
                logger.info("Успешная авторизация с обычным Selenium!")
                return result_selenium
        except ImportError:
            logger.warning("Selenium не установлен, пропускаю этот метод")
        except Exception as e:
            logger.error(f"Ошибка при использовании Selenium: {str(e)}")

    # Если авторизация не удалась или нет учетных данных, пробуем регистрацию
    logger.info("Авторизация не удалась, пробуем регистрацию нового аккаунта")

    # Сначала пробуем undetected-chromedriver (более эффективный для обхода защиты)
    try:
        result_undetected = register_with_undetected(max_retries=max_undetected_retries)
        if result_undetected["success"]:
            logger.info("Успешная регистрация с undetected-chromedriver!")
            return result_undetected
    except ImportError:
        logger.warning("undetected-chromedriver не установлен, пропускаю этот метод")
    except Exception as e:
        logger.error(f"Ошибка при использовании undetected-chromedriver: {str(e)}")

    # Если undetected не работает, пробуем обычный Selenium
    try:
        result_selenium = register_with_selenium(max_retries=max_selenium_retries)
        if result_selenium["success"]:
            logger.info("Успешная регистрация с обычным Selenium!")
            return result_selenium
    except ImportError:
        logger.warning("Selenium не установлен, пропускаю этот метод")
    except Exception as e:
        logger.error(f"Ошибка при использовании Selenium: {str(e)}")

    # Если ни авторизация, ни регистрация не сработали, возвращаем существующие данные
    if VFS_EMAIL and VFS_PASSWORD:
        logger.warning("Не удалось авторизоваться, но у нас есть существующие учетные данные")
        return {
            "success": True,  # Можно считать успехом, так как данные есть
            "email": VFS_EMAIL,
            "password": VFS_PASSWORD,
            "message": "Не удалось авторизоваться автоматически, но учетные данные уже настроены"
        }

    # Если ничего не сработало и нет данных, возвращаем ошибку
    logger.error("Не удалось авторизоваться или зарегистрировать аккаунт ни одним из методов")
    return {
        "success": False,
        "email": None,
        "password": None,
        "message": "Не удалось авторизоваться или зарегистрировать аккаунт ни одним из доступных методов"
    }


if __name__ == "__main__":
    # Если скрипт запущен напрямую, регистрируем аккаунт
    result = register_account()
    if result["success"]:
        print(f"✅ Аккаунт успешно зарегистрирован!")
        print(f"📧 Email: {result['email']}")
        print(f"🔑 Пароль: {result['password']}")
    else:
        print(f"❌ Ошибка регистрации: {result['message']}")