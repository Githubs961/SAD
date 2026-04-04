from aiogram.utils.markdown import hlink

IOS = 'https://apps.apple.com/ru/app/happ-proxy-utility-plus/id6746188973' #Ссылка на HAPP
ANDROID = 'https://play.google.com/store/apps/details?id=com.happproxy' #Ссылка на HAPP

LEXICON_RU: dict[str, str] = {
    '/start': '<b>Добро пожаловать в SAD VPN !!!</b>!!!',
    '/help': f'Для использования SAD VPN необходимо следовать инструкции.\n'
             f'1) Установите приложение Happ:\n'
             f' {hlink(title="Для Iphone",url=IOS)}\n'
             f' {hlink(title="Для Android", url=ANDROID)}',

    'subscription': 'Оформите подписку на SAD VPN.',
    'personal_account': '👤 <b>Личный кабинет</b>'
}


LEXICON_COMMANDS: dict[str, str] = {
    '/start': 'Начало работы с ботом',
    '/help': 'Инструкция'
}

PLANS = {
    "sub_1w": "🗓 7 дней",
    "sub_1m": "📅 1 месяц",
    "sub_2m": "📆 2 месяца",
}
PAY_STARS = {
    "pay_1w": 30,
    "pay_1m": 100,
    "pay_2m": 150,
}
PAY_SBP = {
    "pay_1w": 50,
    "pay_1m": 150,
    "pay_2m": 250,
}