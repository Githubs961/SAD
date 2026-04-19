from aiogram import Router, types, Bot
from aiogram.types import Message, CallbackQuery, PreCheckoutQuery, LabeledPrice
from aiogram.filters import Command, CommandStart, or_f, CommandObject
from aiogram import F
from datetime import datetime
from aiogram.utils.markdown import hlink

from database import grant_subscription, save_payment, get_db_connection
from remnawave_api.api_remnavawe import (get_user,
                                         create_new_user,
                                         format_expire_date, invalidate_user_cache)
from keyboard.keyboard import keyboard, sub_keyboard, pay_keyboard, profile_keyboard, instruction_keyboard, \
    devices_keyboard
from lexicon.lexicon import LEXICON_RU, PLANS, PAY_STARS, INSTRUCTION

# Инициализируем роутер уровня модуля
router = Router()


@router.message(CommandStart())
async def process_start_command(message: Message):
   # if await is_admin(message.chat.id):
        await message.answer(text=LEXICON_RU['/start'],
                             reply_markup=keyboard,disable_web_page_preview=True)


# @router.message(Command(commands='help'))
# async def process_help_command(message: Message):
#     await message.answer(text=LEXICON_RU['/help'],
#                          disable_web_page_preview=True
#                          )


#
@router.message(or_f(F.text == "🔐 Получить доступ", Command("access")))
async def subscription_list(message: Message):
    # Проверка что нет пользователя с таким tg_id и после выдать пробную подписку
    if not await get_user(str(message.from_user.id)): #если пользователя нет то создаем
        sub_url = await create_new_user(telegram_id=str(message.from_user.id),
                                         username=message.from_user.username)# ссылка для подключения
        await message.answer(text=f'🎁 Пробный период 3 дня активирован\n\n 🏡 Перейдите в Личный кабинет для использования',# Ссылка для подключения:\n{sub_url}
                             reply_markup=sub_keyboard)
    else:
        await message.answer(text= LEXICON_RU['subscription'],
                             reply_markup=sub_keyboard)



@router.message(or_f(F.text == "🏡 Личный кабинет", Command("profile"))) #or Command(commands='profile')
async def show_profile(message: Message):
    user = await get_user(str(message.from_user.id))
    # если пользователь найден
    if user:
        await message.answer(text= f"🆔 <b>ID:</b> {user['username']}\n\n"
                                   f"⚡️ <b>Статус подписки:</b> {user['status']}\n"
                                   f"📅 <b> Действует до:</b> {format_expire_date(user['expire_at'])}\n\n"
                                   f"📱 <b>Лимит устройств:</b> {user['hwid_device_limit']}\n",
                             reply_markup=profile_keyboard(user['subscription_url']),
                             disable_web_page_preview=True
                         )
    else:
        await message.answer(text='❌ У вас нет действующей подписки\n '
                                  '🔒 Получите доступ')


# Обработчик кнопки "Назад" в личный кабинет
@router.callback_query(F.data == "back_to_profile")
async def back_to_profile(callback: CallbackQuery):
    user = await get_user(str(callback.from_user.id))

    if user:
        # Редактируем текущее сообщение (то, где был список устройств)
        # и показываем в нём профиль
        await callback.message.edit_text(
            text=f"🆔 <b>ID:</b> {user['username']}\n\n"
                 f"⚡️ <b>Статус подписки:</b> {user['status']}\n"
                 f"📅 <b>Действует до:</b> {format_expire_date(user['expire_at'])}\n\n"
                 f"📱 <b>Лимит устройств:</b> {user['hwid_device_limit']}\n",
            reply_markup=profile_keyboard(user['subscription_url']),
            disable_web_page_preview=True,
            parse_mode="HTML"
        )
    else:
        await callback.message.edit_text(
            text='❌ У вас нет действующей подписки\n🔒 Получите доступ'
        )

    await callback.answer()


@router.message(or_f(F.text == 'ℹ️ Инструкция',Command('help')))
async def manual(message: Message):
    await message.answer(text= f'{INSTRUCTION["step_1"]}',

                         reply_markup=instruction_keyboard(1),
                         disable_web_page_preview=True
                         )

# Обработка нажатий на клавиатуру инструкции
@router.callback_query(F.data.startswith("instruction:"))
async def navigate_instruction(callback: CallbackQuery):
    step = int(callback.data.split(":")[1])

    await callback.message.edit_text(
        INSTRUCTION[f"step_{step}"],
        reply_markup=instruction_keyboard(step),
        parse_mode="HTML"
    )

    await callback.answer()


# Обработка при выборе длительности подписки
@router.callback_query(F.data.in_(PLANS.keys()))
async def sub_duration(callback: CallbackQuery):
    plan = callback.data # какую подписку выбрал пользователь при нажатии на инлайн кнопку
    await callback.message.edit_text(text=f'Вы выбрали подписку: {PLANS[plan]}\nСпособ оплаты 👇',
                                         reply_markup=pay_keyboard(plan.split('_')[1]))
                                        # функция pay_keyboard принимает значение длительности подписки
    await callback.answer()


# Обработчик кнопки back
@router.callback_query(F.data == 'back')
async def click_back(callback: CallbackQuery):
    await callback.message.edit_text(text= LEXICON_RU['subscription'],
                                     reply_markup=sub_keyboard
                                     )
    await callback.answer()


# обработка кнопки "Мои устройства"
@router.callback_query(F.data == 'my_devices')
async def click_add_device(callback: CallbackQuery):
    user = await get_user(str(callback.from_user.id))
    devices = user['devices']
    if not devices:
        await callback.answer("У вас пока нет подключённых устройств", show_alert=True)
        return
    if devices: # не верная проверка на устройства нужно перепроверить
        text = ''
        for i, dev in enumerate(devices,1): # dev это объект поэтому обращаемся через . а не  dev['device_model']
            text += f"{i}. <b>{str(dev.device_model)}</b>\n"
            text += f"   Приложение: {dev.user_agent}\n"
            text += f"   Добавлено: {dev.created_at.strftime('%d.%m.%Y %H:%M')}\n\n"
        await callback.message.edit_text(text=text,parse_mode="HTML", reply_markup=devices_keyboard()) #добавить клавиатуру с устр-вами для удаления

    await callback.answer()








# Проверка платежа для Админа /dbcheck
# @router.message(Command("dbcheck"))
# async def db_check(message: Message):
#     conn = get_db_connection()
#     cursor = conn.cursor()
#
#     # Проверяем платежи
#     cursor.execute("SELECT * FROM payments ORDER BY id DESC LIMIT 5")
#     payments = cursor.fetchall()
#
#     text = "Последние платежи:\n\n"
#     for p in payments:
#         text += f"ID: {p['id']} | CHARGE_ID: {p['telegram_payment_charge_id']} | User: {p['user_id']} | Plan: {p['plan_key']} | Amount: {p['amount']} XTR\n\n"
#     # Проверяем подписки
#     cursor.execute("SELECT * FROM user_subscriptions LIMIT 5")
#     subs = cursor.fetchall()
#
#     text += "\n\nПодписки:\n"
#     for s in subs:
#         text += f"User: {s['user_id']} | Plan: {s['plan_key']} | До: {s['expire_at'][:10]}\n"
#
#     conn.close()
#     await message.answer(text)