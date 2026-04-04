import os
from dotenv import load_dotenv
import asyncio
import json
from typing import Dict, List, Optional, Any
from httpx import AsyncClient, Response
from datetime import datetime, timedelta


load_dotenv()  # вызов переменных окружения, файл ".env"

BASE_URL = os.getenv('PANEL_URL')
TOKEN = os.getenv('REMNAWAVE_TOKEN')
SECRET_NAME = os.getenv('SECRET_NAME')
SECRET_VALUE = os.getenv('SECRET_VALUE')


class RemnawaveUsersClient:
    def __init__(self, base_url: str, token: str, secret_name: str = "CNcFrpva", secret_value: str = "jVCXcYuU"):
        self.base_url = base_url.rstrip('/')
        self.token = token
        self.secret_name = secret_name
        self.secret_value = secret_value

        self.client = AsyncClient(
            base_url=self.base_url,
            cookies={secret_name: secret_value},
            headers={
                "Authorization": f"Bearer {token}",
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                "Accept": "application/json",
                "X-Forwarded-Host": base_url.replace("https://", "").replace("http://", ""),
                "X-Forwarded-Proto": "https"
            },
            timeout=60.0,
            follow_redirects=True
        )

    async def _request(self, method: str, endpoint: str, **kwargs) -> Dict:
        """Базовый метод для всех запросов"""
        url = f"/api{endpoint}" if not endpoint.startswith('/api') else endpoint

        response: Response = await self.client.request(method, url, **kwargs)

        if response.status_code >= 400:
            print(f"Ошибка тела ответа: {response.text[:500]}")
            response.raise_for_status()

        try:
            return response.json()
        except json.JSONDecodeError:
            print(f"Не JSON ответ: {response.text[:300]}")
            return {"error": "invalid_json", "raw": response.text}

    # ==================== Управление пользователями ====================

    async def get_all_users(self) -> List[Dict]:
        """Возвращает список всех пользователей"""
        data = await self._request("GET", "/users")

        # Структура: {"response": {"total": N, "users": [...]}}
        users = data.get("response", {}).get("users", [])
        total = data.get("response", {}).get("total", len(users))

        return users

    async def get_user(self, user_id: str) -> Dict:
        """Получить одного пользователя по ID"""
        return await self._request("GET", f"/users/{user_id}")

    async def create_user(self,
                          username: str,
                          activeInternalSquads: list = None,
                          trafficLimitBytes: int = 0,
                          expireAt: int = 30,
                          description: str = "",
                          email: str = "",
                          telegram_id: Optional[int] = None,
                          hwidDeviceLimit: int = 3,
                          status: str = 'ACTIVE') -> Dict:
        """Создать пользователя под реальную структуру твоей панели"""

        # expireAt в формате ISO (как в твоём JSON)
        if expireAt > 0:
            expire_date = datetime.utcnow() + timedelta(days=expireAt)
            expiry_days = expire_date.isoformat() + "Z"  # 2026-05-01T10:03:00.000Z
        else:
            expiry_days = None

        payload = {
            "username": username,
            "activeInternalSquads":activeInternalSquads,
            "trafficLimitBytes": trafficLimitBytes * 1024 * 1024 * 1024 if trafficLimitBytes > 0 else 0,
            "expireAt": expiry_days, # переменная приводит к формату дыты и времени
            "description": description,
            "email": email,
            "telegramId": telegram_id,
            "hwidDeviceLimit": hwidDeviceLimit,
            "status": status,
            "trafficLimitStrategy": "MONTH"  # трафик обновляется раз в месяц
        }


        response = await self._request("POST", "/users", json=payload)
        return response.get("response", response)

    # async def delete_user(self, user_id: str) -> Dict:
    #     """Удалить пользователя"""
    #     return await self._request("DELETE", f"/users/{user_id}")
    #
    # async def reset_user_traffic(self, user_id: str) -> Dict:
    #     """Сбросить трафик пользователя"""
    #     return await self._request("POST", f"/users/{user_id}/reset")
    #
    # async def update_user(self, user_id: str, **kwargs) -> Dict:
    #     """Обновить данные пользователя (dataLimit, expiryTime, note и т.д.)"""
    #     return await self._request("PUT", f"/users/{user_id}", json=kwargs)

    async def get_all_telegram_ids(self) -> List[int]:
        """Получить список ВСЕХ telegram_id пользователей"""
        users = await self.get_all_users()

        telegram_ids = []

        for user in users:
            tg_id = user.get("telegramId")
            if tg_id is not None:  # проверяем, что поле существует и не null
                telegram_ids.append(tg_id)
        return telegram_ids


    async def get_subscription_url(self, telegram_id: int) -> str:
        """Получить subscription URL для пользователя"""
        users = await self.get_all_users()
        for user in users:
            if user.get("telegramId") == telegram_id:
                return user.get("subscriptionUrl")
        return ""


    async def get_user_by_telegram_id(self,telegram_id: int, telegram_username: str):
        """Проверка есть ли пользователь с таким telegram_id, если нет то создаем с пробной подпиской"""
        tg_ids = await self.get_all_telegram_ids() # данные всех пользователей

        if  telegram_id in tg_ids:  # проверяем, что поле существует и не null
            return False # False, если есть пользователь
        else: # если нет пользователя, создаем
            await client.create_user(
                username=telegram_username,
                activeInternalSquads=["6002d566-a23d-40d4-82c7-624c2a7777b0"],
                trafficLimitBytes=10,  # 10 ГБ
                expireAt=3,  # 3 дня
                description="Пробный период 3 дня",
                email=None,
                telegram_id=telegram_id,
                hwidDeviceLimit=1,
                status="ACTIVE")
            return True

    # ==================== Удобные методы ====================

    async def close(self):
        """Закрыть соединение"""
        await self.client.aclose()


# ====================== Пример использования ======================
client = RemnawaveUsersClient(
        base_url=BASE_URL,
        token=TOKEN,  # из Settings → API Tokens
        # secret_name и secret_value можно не менять, если не менял nginx
    )

async def main():

    try:
        # 1. Получить всех пользователей
        users = await client.get_all_users()

        #print(f"\nВсего пользователей в системе: {len(users)}")

        if users:
            # print("\nПример первого пользователя:")
            # print(json.dumps(users[0], indent=2, ensure_ascii=False))

        # 2. Создать нового пользователя
            # Создание пользователя
            new_user = await client.create_user(
                username="qwerty1",
                activeInternalSquads=["6002d566-a23d-40d4-82c7-624c2a7777b0"],
                trafficLimitBytes=100,  # 100 ГБ
                expireAt=30,  # 30 дней
                description="Создано через API 2026",
                email="example@gmail.com",
                telegram_id=123321,
                hwidDeviceLimit=3,
                status="ACTIVE"
            )

            print("\n✅ Пользователь успешно создан!")
            print(json.dumps(new_user, indent=2, ensure_ascii=False))

    finally:
        await client.close()


