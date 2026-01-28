import os
from dotenv import load_dotenv

print("Текущая директория:", os.getcwd())
print("Проверка наличия файла .env:", os.path.isfile('.env'))

load_dotenv()
token = os.getenv("TELEGRAM_BOT_TOKEN")
print("Загруженный токен:", token)
