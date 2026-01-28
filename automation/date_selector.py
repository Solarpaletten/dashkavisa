#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import time
import logging
import tempfile
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
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
        logging.FileHandler(os.path.join(log_dir, "date_selector.log")),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def select_available_date(driver, selected_date=None):
    """
    Выбирает доступную дату из календаря VFS Global.
    
    Args:
        driver: Экземпляр Selenium WebDriver
        selected_date: Предпочтительная дата для выбора (если None, выбирается первая доступная)
        
    Returns:
        tuple: (bool, str) - (успех, выбранная дата или сообщение об ошибке)
    """
    try:
        logger.info("Начинаю поиск и выбор доступной даты")
        
        # Сначала проверяем, есть ли сообщение об отсутствии слотов
        try:
            no_slots_message = driver.find_element(By.XPATH, 
                "//div[contains(text(), 'нет доступных слотов') or contains(text(), 'Приносим извинения') or contains(text(), 'Места для регистрации')]")
            message_text = no_slots_message.text
            logger.info(f"Найдено сообщение об отсутствии слотов: {message_text}")
            
            # Делаем скриншот страницы с сообщением
            screenshot_path = os.path.join(screenshots_dir, f"no_slots_for_selection_{int(time.time())}.png")
            driver.save_screenshot(screenshot_path)
            
            # Возвращаем сообщение об ошибке
            return False, "Нет доступных слотов для записи"
        except:
            logger.info("Сообщение об отсутствии слотов не найдено, ищем доступные даты для выбора")
        
        # Делаем скриншот перед попыткой найти календарь
        screenshot_path = os.path.join(screenshots_dir, f"calendar_search_{int(time.time())}.png")
        driver.save_screenshot(screenshot_path)
        
        # Проверяем, есть ли календарь с датами
        try:
            # Ищем элементы календаря (матрицу дат)
            calendar = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, ".mat-calendar-body, .calendar-container, mat-calendar, .date-selection"))
            )
            logger.info("Календарь найден")
            
            # Ищем все доступные (не заблокированные) ячейки в календаре
            available_cells = []
            
            # Проверяем доступные даты различными способами (под разные версии UI)
            
            # Способ 1: Ищем стандартные ячейки календаря
            try:
                cells = driver.find_elements(By.CSS_SELECTOR, 
                    ".mat-calendar-body-cell:not(.mat-calendar-body-disabled), .date-available, td.selectable:not(.disabled)")
                
                if cells:
                    available_cells.extend(cells)
                    logger.info(f"Найдено {len(cells)} доступных ячеек календаря (способ 1)")
            except Exception as e:
                logger.warning(f"Ошибка при поиске ячеек календаря (способ 1): {str(e)}")
            
            # Способ 2: Ищем любые элементы, которые могут быть кликабельными датами
            if not available_cells:
                try:
                    date_elements = driver.find_elements(By.CSS_SELECTOR, 
                        "[class*='date']:not([class*='disabled']), [class*='calendar-cell']:not([class*='disabled'])")
                    
                    clickable_elements = []
                    for elem in date_elements:
                        try:
                            if elem.is_displayed() and elem.is_enabled() and elem.text.strip() and any(c.isdigit() for c in elem.text):
                                clickable_elements.append(elem)
                        except:
                            continue
                    
                    if clickable_elements:
                        available_cells.extend(clickable_elements)
                        logger.info(f"Найдено {len(clickable_elements)} кликабельных элементов с датами (способ 2)")
                except Exception as e:
                    logger.warning(f"Ошибка при поиске элементов дат (способ 2): {str(e)}")
            
            # Если нашли доступные ячейки, выбираем одну из них
            if available_cells:
                # Если есть предпочтительная дата, пытаемся найти ее
                selected_cell = None
                
                if selected_date:
                    for cell in available_cells:
                        try:
                            cell_text = cell.text.strip()
                            if selected_date in cell_text:
                                selected_cell = cell
                                logger.info(f"Найдена предпочтительная дата: {cell_text}")
                                break
                        except:
                            continue
                
                # Если предпочтительная дата не найдена или не указана, берем первую доступную
                if not selected_cell and available_cells:
                    selected_cell = available_cells[0]
                    logger.info(f"Выбрана первая доступная дата: {selected_cell.text}")
                
                # Прокручиваем страницу к выбранной ячейке
                driver.execute_script("arguments[0].scrollIntoView(true);", selected_cell)
                time.sleep(1)
                
                # Делаем скриншот перед кликом
                screenshot_path = os.path.join(screenshots_dir, f"before_date_click_{int(time.time())}.png")
                driver.save_screenshot(screenshot_path)
                
                # Сохраняем текст выбранной даты
                selected_date_text = "Не удалось получить текст даты"
                try:
                    selected_date_text = selected_cell.text.strip()
                except:
                    pass
                
                # Кликаем на выбранную дату
                try:
                    WebDriverWait(driver, 5).until(EC.element_to_be_clickable(selected_cell))
                    selected_cell.click()
                    logger.info(f"Выполнен клик по дате: {selected_date_text}")
                    time.sleep(2)
                except Exception as e:
                    logger.error(f"Ошибка при клике на дату: {str(e)}")
                    # Альтернативный способ клика
                    try:
                        driver.execute_script("arguments[0].click();", selected_cell)
                        logger.info(f"Выполнен JavaScript-клик по дате: {selected_date_text}")
                        time.sleep(2)
                    except Exception as js_error:
                        logger.error(f"Ошибка при JavaScript-клике: {str(js_error)}")
                        return False, f"Не удалось выбрать дату: {selected_date_text}"
                
                # Делаем скриншот после клика
                screenshot_path = os.path.join(screenshots_dir, f"after_date_click_{int(time.time())}.png")
                driver.save_screenshot(screenshot_path)
                
                # Проверяем, появилось ли меню выбора времени
                try:
                    time_selection = WebDriverWait(driver, 5).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, ".time-slot, .time-selection, [class*='time-slot']"))
                    )
                    logger.info("Найдено меню выбора времени")
                    
                    # Выбираем первый доступный временной слот
                    try:
                        time_slots = driver.find_elements(By.CSS_SELECTOR, 
                            ".time-slot:not(.disabled), [class*='time-slot']:not([class*='disabled']), button[class*='time']")
                        
                        if time_slots:
                            first_slot = time_slots[0]
                            slot_text = first_slot.text.strip()
                            
                            # Прокручиваем к временному слоту
                            driver.execute_script("arguments[0].scrollIntoView(true);", first_slot)
                            time.sleep(1)
                            
                            # Делаем скриншот перед выбором времени
                            screenshot_path = os.path.join(screenshots_dir, f"before_time_click_{int(time.time())}.png")
                            driver.save_screenshot(screenshot_path)
                            
                            # Кликаем на временной слот
                            try:
                                WebDriverWait(driver, 5).until(EC.element_to_be_clickable(first_slot))
                                first_slot.click()
                                logger.info(f"Выбран временной слот: {slot_text}")
                                time.sleep(2)
                            except:
                                # Альтернативный клик
                                driver.execute_script("arguments[0].click();", first_slot)
                                logger.info(f"Выполнен JavaScript-клик по временному слоту: {slot_text}")
                                time.sleep(2)
                            
                            # Делаем скриншот после выбора времени
                            screenshot_path = os.path.join(screenshots_dir, f"after_time_click_{int(time.time())}.png")
                            driver.save_screenshot(screenshot_path)
                            
                            # Проверяем наличие кнопки подтверждения
                            try:
                                confirm_button = WebDriverWait(driver, 5).until(
                                    EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Подтвердить') or contains(text(), 'Продолжить')]"))
                                )
                                confirm_button.click()
                                logger.info("Нажата кнопка подтверждения времени")
                                time.sleep(2)
                                
                                # Делаем финальный скриншот после подтверждения
                                screenshot_path = os.path.join(screenshots_dir, f"after_confirmation_{int(time.time())}.png")
                                driver.save_screenshot(screenshot_path)
                                
                                return True, f"Успешно выбрана дата {selected_date_text} и время {slot_text}"
                            except:
                                logger.warning("Кнопка подтверждения не найдена, но дата и время были выбраны")
                                return True, f"Выбрана дата {selected_date_text} и время {slot_text}, подтверждение невозможно"
                        else:
                            logger.warning("Меню выбора времени найдено, но нет доступных временных слотов")
                            return False, "Нет доступных временных слотов для выбранной даты"
                    except Exception as e:
                        logger.error(f"Ошибка при выборе временного слота: {str(e)}")
                        return False, f"Ошибка при выборе времени: {str(e)}"
                except:
                    logger.info("Меню выбора времени не найдено, возможно, выбор времени не требуется")
                    # В некоторых случаях выбор времени может не потребоваться
                    # Проверяем наличие кнопки подтверждения или продолжения
                    try:
                        next_button = WebDriverWait(driver, 5).until(
                            EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Подтвердить') or contains(text(), 'Продолжить') or contains(text(), 'Далее')]"))
                        )
                        next_button.click()
                        logger.info("Нажата кнопка подтверждения даты")
                        time.sleep(2)
                        
                        # Делаем финальный скриншот после подтверждения
                        screenshot_path = os.path.join(screenshots_dir, f"after_date_confirm_{int(time.time())}.png")
                        driver.save_screenshot(screenshot_path)
                        
                        return True, f"Успешно выбрана дата {selected_date_text}"
                    except:
                        logger.warning("Кнопка подтверждения не найдена, но дата была выбрана")
                        return True, f"Выбрана дата {selected_date_text}, подтверждение невозможно"
                
            else:
                logger.warning("Календарь найден, но нет доступных дат для выбора")
                screenshot_path = os.path.join(screenshots_dir, f"no_available_dates_{int(time.time())}.png")
                driver.save_screenshot(screenshot_path)
                return False, "В календаре нет доступных дат для выбора"
                
        except Exception as e:
            logger.error(f"Ошибка при поиске и работе с календарем: {str(e)}")
            screenshot_path = os.path.join(screenshots_dir, f"calendar_error_{int(time.time())}.png")
            driver.save_screenshot(screenshot_path)
            return False, f"Ошибка при работе с календарем: {str(e)}"
        
    except Exception as e:
        logger.error(f"Критическая ошибка при выборе даты: {str(e)}")
        error_screenshot = os.path.join(screenshots_dir, f"date_selection_critical_error_{int(time.time())}.png")
        try:
            driver.save_screenshot(error_screenshot)
        except:
            pass
        return False, f"Критическая ошибка при выборе даты: {str(e)}"


def complete_booking(driver):
    """
    Завершает процесс бронирования после выбора даты и времени.
    
    Args:
        driver: Экземпляр Selenium WebDriver
        
    Returns:
        tuple: (bool, str) - (успех, сообщение с результатом или ошибкой)
    """
    try:
        logger.info("Начинаю процесс завершения бронирования")
        
        # Сохраняем скриншот текущего состояния
        screenshot_path = os.path.join(screenshots_dir, f"booking_completion_start_{int(time.time())}.png")
        driver.save_screenshot(screenshot_path)
        
        # Проверяем, находимся ли мы на странице завершения бронирования
        # Ищем элементы, характерные для финальной страницы
        confirmation_elements = [
            "//h1[contains(text(), 'Подтверждение')]",
            "//div[contains(text(), 'Ваше бронирование')]",
            "//div[contains(text(), 'Записи на прием')]",
            "//button[contains(text(), 'Завершить') or contains(text(), 'Подтвердить бронирование')]"
        ]
        
        found_confirmation_page = False
        for selector in confirmation_elements:
            try:
                element = driver.find_element(By.XPATH, selector)
                found_confirmation_page = True
                logger.info(f"Найден элемент подтверждения бронирования: {selector}")
                break
            except:
                continue
        
        if not found_confirmation_page:
            logger.warning("Не найдены элементы страницы подтверждения бронирования")
            
            # Пробуем нажать любую кнопку продолжения, которая может быть на странице
            try:
                continue_buttons = driver.find_elements(By.XPATH, 
                    "//button[contains(text(), 'Продолжить') or contains(text(), 'Далее') or contains(text(), 'Подтвердить')]")
                
                if continue_buttons:
                    # Берем первую найденную кнопку
                    button = continue_buttons[0]
                    button_text = button.text.strip()
                    
                    # Скролл к кнопке
                    driver.execute_script("arguments[0].scrollIntoView(true);", button)
                    time.sleep(1)
                    
                    # Делаем скриншот перед нажатием
                    screenshot_path = os.path.join(screenshots_dir, f"before_continue_click_{int(time.time())}.png")
                    driver.save_screenshot(screenshot_path)
                    
                    # Нажимаем кнопку
                    button.click()
                    logger.info(f"Нажата кнопка: {button_text}")
                    time.sleep(2)
                    
                    # Делаем скриншот после нажатия
                    screenshot_path = os.path.join(screenshots_dir, f"after_continue_click_{int(time.time())}.png")
                    driver.save_screenshot(screenshot_path)
                else:
                    logger.warning("Не найдено кнопок для продолжения")
            except Exception as e:
                logger.error(f"Ошибка при поиске и нажатии кнопки продолжения: {str(e)}")
        
        # Ищем финальную кнопку подтверждения/завершения бронирования
        final_button_found = False
        try:
            final_buttons = driver.find_elements(By.XPATH, 
                "//button[contains(text(), 'Завершить') or contains(text(), 'Подтвердить бронирование') or contains(text(), 'Финализировать')]")
            
            if final_buttons:
                final_button = final_buttons[0]
                final_button_text = final_button.text.strip()
                
                # Скролл к кнопке
                driver.execute_script("arguments[0].scrollIntoView(true);", final_button)
                time.sleep(1)
                
                # Делаем скриншот перед финальным нажатием
                screenshot_path = os.path.join(screenshots_dir, f"before_final_button_{int(time.time())}.png")
                driver.save_screenshot(screenshot_path)
                
                # Нажимаем финальную кнопку
                final_button.click()
                logger.info(f"Нажата финальная кнопка: {final_button_text}")
                time.sleep(3)
                
                # Делаем скриншот после финального нажатия
                screenshot_path = os.path.join(screenshots_dir, f"after_final_button_{int(time.time())}.png")
                driver.save_screenshot(screenshot_path)
                
                final_button_found = True
            else:
                logger.warning("Не найдена финальная кнопка подтверждения бронирования")
        except Exception as e:
            logger.error(f"Ошибка при поиске и нажатии финальной кнопки: {str(e)}")
        
        # Проверяем наличие подтверждения успешного бронирования
        success_elements = [
            "//div[contains(text(), 'успешно забронирован') or contains(text(), 'Ваша запись подтверждена')]",
            "//div[contains(text(), 'Спасибо') and contains(text(), 'бронирование')]",
            "//h1[contains(text(), 'Подтверждение')]"
        ]
        
        success_found = False
        success_message = ""
        for selector in success_elements:
            try:
                element = driver.find_element(By.XPATH, selector)
                success_message = element.text.strip()
                success_found = True
                logger.info(f"Найдено подтверждение успешного бронирования: {success_message}")
                break
            except:
                continue
        
        # Делаем финальный скриншот результата
        screenshot_path = os.path.join(screenshots_dir, f"booking_completion_final_{int(time.time())}.png")
        driver.save_screenshot(screenshot_path)
        
        if success_found:
            return True, f"Бронирование успешно завершено: {success_message}"
        elif final_button_found:
            return True, "Процесс бронирования выполнен, но подтверждение не найдено"
        else:
            return False, "Не удалось завершить процесс бронирования, финальная кнопка не найдена"
        
    except Exception as e:
        logger.error(f"Критическая ошибка при завершении бронирования: {str(e)}")
        error_screenshot = os.path.join(screenshots_dir, f"booking_completion_error_{int(time.time())}.png")
        try:
            driver.save_screenshot(error_screenshot)
        except:
            pass
        return False, f"Критическая ошибка при завершении бронирования: {str(e)}"