import os
from dotenv import load_dotenv

load_dotenv()

TELEGRAMTOKEN = os.getenv("TELEGRAMTOKEN")

YANDEX_CLOUD_API_KEY = os.getenv("YANDEX_CLOUD_API_KEY") or os.getenv("API_KEY")
FOLDER_ID = os.getenv("FOLDER_ID")