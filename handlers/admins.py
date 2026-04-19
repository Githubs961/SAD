from dotenv import load_dotenv
from aiogram.filters import BaseFilter, Command
from aiogram.types import Message
import os

from database import get_db_connection
from handlers.user import router


IDS = os.getenv('ADMINS_ID')

# Проверка на админку по ID
class AdminFilter(BaseFilter):
    """Фильтр для проверки, является ли пользователь админом"""
    async def __call__(self, message: Message) -> bool:
        return str(message.from_user.id) in IDS

# Объект фильтра
admin_filter = AdminFilter()




# Использование в роутере:
@router.message(Command("dbcheck"), admin_filter)
async def db_check(message: Message):
    conn = get_db_connection()
    cursor = conn.cursor()

    # Проверяем платежи
    cursor.execute("SELECT * FROM payments ORDER BY id DESC LIMIT 5")
    payments = cursor.fetchall()

    text = "Последние платежи:\n\n"
    for p in payments:
        text += f"ID: {p['id']} | CHARGE_ID: {p['telegram_payment_charge_id']} | User: {p['user_id']} | Plan: {p['plan_key']} | Amount: {p['amount']} XTR\n\n"
    # Проверяем подписки
    cursor.execute("SELECT * FROM user_subscriptions LIMIT 5")
    subs = cursor.fetchall()

    text += "\n\nПодписки:\n"
    for s in subs:
        text += f"User: {s['user_id']} | Plan: {s['plan_key']} | До: {s['expire_at'][:10]}\n"

    conn.close()
    await message.answer(text)
