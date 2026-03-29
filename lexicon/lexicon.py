from aiogram.utils.markdown import hlink

IOS = 'https://apps.apple.com/ru/app/happ-proxy-utility-plus/id6746188973'
ANDROID = 'https://play.google.com/store/apps/details?id=com.happproxy'

LEXICON_RU: dict[str, str] = {
    '/start': '<b>Добро пожаловать в SAD VPN !!!</b>!!!',
    '/help': f'Для использования SAD VPN необходимо следовать инструкции.\n'
             f'1) Установите приложение Happ:\n'
             f' {hlink(title="Для Iphone",url=IOS)}\n'
             f' {hlink(title="Для Android", url=ANDROID)}',
    'admin': 'Вы авторизованы!\nИспользуйте доступные команды',
    'not_admin': 'Для использования бота введите ключ...',
    'not_news': 'Свежих новостей нет!',
    'subscription': 'Оформите подписку на SAD VPN.'
}


LEXICON_COMMANDS: dict[str, str] = {
    '/start': 'Начало работы с ботом',
    '/help': 'Инструкция'
}

PLANS = {
    "sub_1w": "🗓 1 неделя",
    "sub_1m": "📅 1 месяц",
    "sub_2m": "📆 2 месяца",
}
PAY_STARS = {
    "pay_1w": 1,
    "pay_1m": 100,
    "pay_2m": 150,
}
PAY_SBP = {
    "pay_1w": 30,
    "pay_1m": 99,
    "pay_2m": 149,
}