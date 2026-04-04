import os
from dotenv import load_dotenv
import asyncio
import json
from typing import Dict, List, Optional, Any
from httpx import AsyncClient, Response
from datetime import datetime, timedelta

from remnawave import RemnawaveSDK



load_dotenv()  # вызов переменных окружения, файл ".env"

BASE_URL = os.getenv('PANEL_URL')
TOKEN = os.getenv('REMNAWAVE_TOKEN')
SECRET_NAME = os.getenv('SECRET_NAME') #необходим для доступа к API,лежит в ramnawave/nginx
SECRET_VALUE = os.getenv('SECRET_VALUE')#необходим для доступа к API,лежит в ramnawave/nginx




async def main():


    http_client = AsyncClient(
        base_url=BASE_URL,
        cookies={SECRET_NAME: SECRET_VALUE},
        headers={
            "Authorization": f"Bearer {TOKEN}",
            "Host": BASE_URL.replace("https://", "").replace("http://", ""),
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Accept": "application/json, text/plain, */*",
            "X-Forwarded-Host": BASE_URL.replace("https://", "").replace("http://", ""),
            "X-Forwarded-Proto": "https",
            "Referer": f"{BASE_URL}/auth/login?{SECRET_NAME}={SECRET_VALUE}"
        },
        timeout=60.0,
        follow_redirects=True
    )

    client = RemnawaveSDK(client=http_client)

    try:
        users = client.users.get_users_by_telegram_id("758504107")
        print(users)
        # # 2. Тестовый запрос к статусу (полезно для диагностики)
        # status_resp = await http_client.get("/api/auth/status")
        # print(f"Auth status code: {status_resp.status_code}")
        # print(f"Auth status body: {status_resp.text[:300]}")  # покажем, что пришло
        #
        # # 2. Прямой запрос к пользователям (самый надёжный тест)
        # print("Делаем прямой запрос /api/users ...")
        # raw_resp = await http_client.get("/api/users")
        # print(f"Raw /api/users status: {raw_resp.status_code}")
        # print(f"Raw body (первые 400 символов): {repr(raw_resp.text[:400])}")
        # # Сохранение users.json с панели remnawave_client
        # with open('../cache/users.json', 'w', encoding='utf-8') as file:
        #     json.dump(raw_resp.json(),file, indent=4, ensure_ascii=False)
    except Exception as e:
        print(f"❌ Ошибка: {type(e).__name__} — {e}")


if __name__ == "__main__":
    asyncio.run(main())