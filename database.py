import sqlite3
import asyncio
from datetime import datetime, timedelta
from pathlib import Path
from lexicon.lexicon import PAY_STARS


DB_PATH = Path("bot_database.db")

# 🔒 Глобальный lock для записи
db_lock = asyncio.Lock()

# Создаём подключение
def get_db_connection():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row  # чтобы возвращались словари
    return conn


# Инициализация базы данных
def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()

    # 🔥 включаем WAL режим (уменьшает блокировки)
    cursor.execute("PRAGMA journal_mode=WAL;")

    # Таблица платежей
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS payments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            provider TEXT NOT NULL, 
            status TEXT DEFAULT 'PENDING', 
            user_id INTEGER NOT NULL,
            transactionId TEXT UNIQUE NOT NULL,
            plan_key TEXT NOT NULL,
            amount INTEGER NOT NULL,
            currency TEXT NOT NULL,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            processed_at TEXT,
            redirect TEXT
        )
    ''')
    # Статусы   -- PENDING / CONFIRMED / CANCELED


    cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_traffic (
            user_id INTEGER PRIMARY KEY,
            node_id TEXT NOT NULL,              -- нода (Яндекс)
            used_bytes INTEGER DEFAULT 0,       -- сколько использовано
            traffic_limit INTEGER NOT NULL,     -- лимит (например 50GB)
            period_start TEXT NOT NULL,         -- начало периода
            period_end TEXT NOT NULL,           -- конец (через 30 дней)
            last_total_bytes INTEGER DEFAULT 0, -- прошлое значение из API
            updated_at TEXT,
            is_active INTEGER DEFAULT 1
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            uuid TEXT
        )
    ''')

    conn.commit()
    conn.close()
    print("✅ База данных успешно инициализирована")


# Сохранение пользователя в БД
async def save_user(user_id: int, username: str, uuid: str):
    async with db_lock:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("""
            INSERT OR REPLACE INTO users (user_id, username, uuid)
            VALUES (?, ?, ?)
        """, (user_id, username, uuid))

        conn.commit()
        conn.close()


# Сохранение платежа STARS
async def save_payment(user_id: int, provider: str, status: str, transactionId: str, plan_key: str, amount: int, currency:str, redirect: str = None):
    async with db_lock:  # 🔒 защита от параллельной записи
        conn = get_db_connection()
        cursor = conn.cursor()

        try:
            cursor.execute('''
                INSERT INTO payments 
                (user_id, provider, status, transactionId, plan_key, amount, currency, redirect, processed_at )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (user_id, provider, status, transactionId, plan_key, amount,currency, redirect, datetime.utcnow().isoformat()))

            conn.commit()
            print(f"✅ Платёж {transactionId} сохранён")
            return True
        except sqlite3.IntegrityError:
            print(f"Платёж {transactionId} уже был сохранён ранее")
            return False
        except Exception as e:
            print(f"❌ Ошибка сохранения платежа: {e}")
        finally:
            conn.close()



# проверка существующего плвтежа Platega
def get_active_payment(user_id: int, plan_key: str):
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT * FROM payments
        WHERE user_id = ?
        AND plan_key = ?
        AND status = 'PENDING'
        AND created_at > datetime('now', '-30 minutes')
        ORDER BY id DESC
        LIMIT 1
    """, (user_id, plan_key))

    row = cursor.fetchone()
    conn.close()
    return row




# Проверяем и Обнавляем БД после платежа Platega
def update_db(status, transaction_id):
    conn = get_db_connection()
    cursor = conn.cursor()

    # 👉 берём старый статус
    cursor.execute("""
        SELECT status, user_id, plan_key
        FROM payments
        WHERE transactionId = ?
    """, (transaction_id,))

    row = cursor.fetchone()

    if not row:
        conn.close()
        return None

    old_status = row["status"]

    # 👉 обновляем только если статус изменился
    if old_status != status:
        cursor.execute("""
            UPDATE payments
            SET status = ?, processed_at = ?
            WHERE transactionId = ?
        """, (
            status,
            datetime.utcnow().isoformat(),
            transaction_id
        ))
        conn.commit()

    conn.close()

    return {
        "user_id": row["user_id"],
        "plan_key": row["plan_key"],
        "old_status": old_status
    }




# Платеж не оплачен пометка EXPIRED в БД
async def expire_old_payments():
    while True:
        now = datetime.utcnow()
        next_run = now.replace(hour=3, minute=0, second=0, microsecond=0)

        if next_run <= now:
            next_run += timedelta(days=1)

        sleep_time = (next_run - now).total_seconds()
        await asyncio.sleep(sleep_time)

        # 🔥 твоя очистка
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("""
                UPDATE payments
                SET status = 'EXPIRED',
                    processed_at = ?
                WHERE status = 'PENDING'
                AND created_at < datetime('now', '-30 minutes')
            """, (datetime.utcnow().isoformat(),))

        conn.commit()
        conn.close()

        print("🧹 Очистка выполнена")



# Трафик пользователя, для личного кабинета
def get_user_traffic(user_id: int):
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT used_bytes, traffic_limit, period_end
        FROM user_traffic
        WHERE user_id = ?
    """, (user_id,))

    row = cursor.fetchone()
    conn.close()

    return row

