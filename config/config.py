from dataclasses import dataclass
import os
from dotenv import load_dotenv  # загрузка переменных окружения из файла .env

load_dotenv()  # вызов переменных окружения, файл ".env"


@dataclass
class TgBot:
    token: str  # Токен телеграм бота
    admin_pass: str  # admins: list[int]  # Список id админов бота


@dataclass
class Config:
    tg_bot: TgBot


def load_config(path: str) -> Config:
    return Config(
        tg_bot=TgBot(token=os.getenv('BOT_TOKEN'),
                     admin_pass=os.getenv('BOT_PASS')))
