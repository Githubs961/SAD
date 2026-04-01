from aiogram import Router
from aiogram.types import Message, CallbackQuery, PreCheckoutQuery, LabeledPrice
from aiogram.filters import Command, CommandStart
from aiogram import F
from aiogram.utils.markdown import hlink
from keyboard.keyboard import keyboard, sub_keyboard, pay_keyboard
from lexicon.lexicon import LEXICON_RU, PLANS, PAY_STARS

# Инициализируем роутер уровня модуля
router = Router()

@router.message(CommandStart())
async def process_start_command(message: Message):
   # if await is_admin(message.chat.id):
        await message.answer(text=LEXICON_RU['/start'],
                             reply_markup=keyboard)


@router.message(Command(commands='help'))
async def process_help_command(message: Message):
    await message.answer(text=LEXICON_RU['/help'],
                         reply_markup=keyboard,
                         disable_web_page_preview=True
                         )


@router.message(F.text == 'Подписка')
async def subscription_list(message: Message):
    await message.answer(text= LEXICON_RU['subscription'],
                         reply_markup=sub_keyboard)


@router.message(F.text == 'Инструкция')
async def manual(message: Message):
    await message.answer(text= LEXICON_RU['/help'],
                         reply_markup=keyboard,
                         disable_web_page_preview=True
                         )

# Обработка при выборе длительности подписки
@router.callback_query(F.data.in_(PLANS.keys()))
async def sub_duration(callback: CallbackQuery):
    plan = callback.data # какую подписку выбрал пользователь при нажатии на инлайнкнопку
    if plan == 'sub_free': # выбрал пробный период

        await callback.message.answer(text='Пробный период активирован')

    else:
        await callback.message.edit_text(text=f'Вы выбрали подписку: {PLANS[plan]}\nСпособ оплаты:',
                                         reply_markup=pay_keyboard(plan.split('_')[1]))
                                        # функция pay_keyboard принимает значение длительности подписки
    await callback.answer()


# Обработчик кнопки back при выборе способа оплаты
@router.callback_query(F.data == 'back')
async def clock_back(callback: CallbackQuery):
    await callback.message.edit_text(text= LEXICON_RU['subscription'],
                                     reply_markup=sub_keyboard
                                     )
    await callback.answer()

# Обработчик оплаты Telegram Stars
@router.callback_query(F.data.in_(PAY_STARS.keys()))
async def pay_stars(callback: CallbackQuery):
    plan = callback.data
    sub_text = f'sub_{plan.split("_")[1]}' # переменная для текста из lexicon.py
    prices = [LabeledPrice(label='XTR', amount=PAY_STARS[plan])]

    await callback.message.answer_invoice(
        title=f'VPN подписка',
        description=f'Тариф: {PLANS[sub_text]}',
        payload=plan,
        currency='XTR',
        prices=prices
    )
    await callback.answer()


# Подтверждение платежа и проверка есть ли подписка
@router.pre_checkout_query()
async def pre_checkout(pre_checkout_q: PreCheckoutQuery):
    await pre_checkout_q.answer(ok=True)


# Проверка что платеж прошел и выполняем условие.....
@router.message(F.succeful_payment)
async def payment(message:Message):
    await message.answer(f'{message.successful_payment.telegram_payment_charge_id}')