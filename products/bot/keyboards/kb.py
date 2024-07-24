from datetime import datetime

import pytz
from aiogram.utils.keyboard import ReplyKeyboardBuilder
from aiogram.types import KeyboardButton, ReplyKeyboardMarkup
from aiogram.types import Location

from products.bot.handlers.some_func import json_loader

ru = json_loader()['menu']['ru']['inline_keyboard_button']
uz = json_loader()['menu']['uz']['inline_keyboard_button']


def get_phone_num(lang='ru'):
    buttons = [
        [
            KeyboardButton(text="☎️ОТПРАВИТЬ КОНТАКТ" if lang == "ru" else "☎️TELEFON RAQAMINI YUBORISH",
                           request_contact=True)
        ]
    ]
    kb = ReplyKeyboardMarkup(resize_keyboard=True, keyboard=buttons)
    return kb


def menu_kb(lang: str = 'ru'):
    buttons = [
        [
            KeyboardButton(text=ru['choose_product'] if lang == 'ru' else uz['choose_product']),

        ],
        [
            KeyboardButton(text=ru['promotion'] if lang == 'ru' else uz['promotion']),
            KeyboardButton(text=ru['leave_feedback'] if lang == 'ru' else uz['leave_feedback'])
        ],
        [
            KeyboardButton(text=ru['my_orders'] if lang == 'ru' else uz['my_orders']),
            KeyboardButton(text=ru['settings'] if lang == 'ru' else uz['settings'])
        ],
        [
            KeyboardButton(text=ru['about_delivery'] if lang == 'ru' else uz['about_delivery']),
            KeyboardButton(text=ru['about_us'] if lang == 'ru' else uz['about_us']),
        ]

    ]

    kb = ReplyKeyboardMarkup(resize_keyboard=True, keyboard=buttons)
    return kb


def stage_order_delivery_kb(lang: str):
    buttons = [
        [
            KeyboardButton(text=ru['delivery'] if lang == 'ru' else uz['delivery']),
            KeyboardButton(text=ru['pickup'] if lang == 'ru' else uz['pickup']),
        ],
        [
            KeyboardButton(text=ru['back'] if lang == 'ru' else uz['back'])
        ]
    ]
    kb = ReplyKeyboardMarkup(resize_keyboard=True, keyboard=buttons)
    return kb


def send_location_kb(lang: str, my_adress: list):
    buttons = [
        [
            KeyboardButton(text=ru['send_location'] if lang == 'ru' else uz['send_location'], request_location=True)
        ],

        [
            KeyboardButton(text=ru['back'] if lang == 'ru' else uz['back'])
        ]
    ]
    print(my_adress)
    try:
        for i in my_adress:
            button = KeyboardButton(text=i.address)
            buttons.insert(1, [button])
    except:
        pass
    kb = ReplyKeyboardMarkup(resize_keyboard=True, keyboard=buttons)

    return kb


def confirm_location_kb(lang: str):
    buttons = [
        [
            KeyboardButton(text="Переотправить локацию" if lang == 'ru' else "Lokatsiyani qayta yuborish", request_location=True),
            KeyboardButton(text="✅Подтвердить" if lang == "ru" else "✅Tasdiqlash")
        ],
        [
            KeyboardButton(text=ru['send_location1'] if lang == 'ru' else uz['send_location1']),
            KeyboardButton(text=ru['back'] if lang == 'ru' else uz['back'])
        ]
    ]
    kb = ReplyKeyboardMarkup(resize_keyboard=True, keyboard=buttons)

    return kb


def location_kb(lang: str):
    buttons = [
        [
            KeyboardButton(text="📍Отправить локацию магазина" if lang == 'ru' else "📍Magazin manzilini yuborish"),
            KeyboardButton(text=ru['back'] if lang == 'ru' else uz['back'])
        ]
    ]
    kb = ReplyKeyboardMarkup(resize_keyboard=True, keyboard=buttons)

    return kb


def payment_kb(lang: str):
    buttons = [
        [
            KeyboardButton(text=ru['back'] if lang == 'ru' else uz['back']),
            KeyboardButton(text="Наличные" if lang == 'ru' else "Naqd"),

        ],
        [
            KeyboardButton(text="Теримнал/Карта" if lang == 'ru' else "Terminal/Karta"),
            KeyboardButton(text="Payme")
        ],
        [
            KeyboardButton(text="Click")
        ]
    ]
    kb = ReplyKeyboardMarkup(resize_keyboard=True, keyboard=buttons)

    return kb


def choose_time_kb(lang: str):
    buttons = [
        [
            KeyboardButton(text="Ближайшее время" if lang == "ru" else "Tez orada"),
            KeyboardButton(text="Выбрать время" if lang == "ru" else "Aniq muddatda"),
        ],
        [
            KeyboardButton(text=ru['back'] if lang == 'ru' else uz['back'])
        ]
    ]
    kb = ReplyKeyboardMarkup(resize_keyboard=True, keyboard=buttons)

    return kb


def product_kb(lang: str, all_pr: list = None) -> ReplyKeyboardMarkup:
    kb = ReplyKeyboardBuilder()
    kb.add(KeyboardButton(text=ru['back'] if lang == 'ru' else uz['back']))
    kb.add(KeyboardButton(text=ru['cart'] if lang == 'ru' else uz['cart']))
    for i in all_pr:
        kb.add(KeyboardButton(text=i.product_name))

    kb.adjust(2)
    return kb.as_markup()


def category_product_menu(lang: str) -> ReplyKeyboardMarkup:
    buttons = [
        [
            KeyboardButton(text=ru['back'] if lang == 'ru' else uz['back']),
            KeyboardButton(text=ru['cart'] if lang == 'ru' else uz['cart'])
        ],
        [
            KeyboardButton(text="Продукция" if lang == 'ru' else "Mahsulotlar"),
            KeyboardButton(text="Эксклюзивные сеты" if lang == 'ru' else "Ekskluziv Setlar")
        ],
        # [
        #     KeyboardButton(text="Мерч" if lang == 'ru' else "Merch")
        # ]
    ]

    kb = ReplyKeyboardMarkup(resize_keyboard=True, keyboard=buttons)
    return kb


def product_edit_menu(lang: str) -> ReplyKeyboardMarkup:
    buttons = [
        [
            KeyboardButton(text=ru['back'] if lang == 'ru' else uz['back']),
            KeyboardButton(text=ru['cart'] if lang == 'ru' else uz['cart'])
        ]
    ]

    kb = ReplyKeyboardMarkup(resize_keyboard=True, keyboard=buttons)
    return kb


def product_back_to_category(lang: str):
    buttons = [
        [
            KeyboardButton(text=ru['back'] if lang == 'ru' else uz['back'])
        ]
    ]

    kb = ReplyKeyboardMarkup(resize_keyboard=True, keyboard=buttons)
    return kb


def get_supp_phone_num(lang: str) -> ReplyKeyboardMarkup:
    buttons = [
        [
            KeyboardButton(text=ru["supp_phone_num"] if lang == "ru" else uz["supp_phone_num"])
        ],
        [
            KeyboardButton(text=ru['back'] if lang == 'ru' else uz['back'])
        ]
    ]
    kb = ReplyKeyboardMarkup(resize_keyboard=True, keyboard=buttons)
    return kb


def leave_feedback_kb(lang: str):
    buttons = [
        [
            KeyboardButton(text=ru['back'] if lang == 'ru' else uz['back'])
        ]
    ]

    kb = ReplyKeyboardMarkup(resize_keyboard=True, keyboard=buttons)
    return kb


def settings_kb(lang: str, birth: str = None):
    buttons = [
        [
            KeyboardButton(text="🇺🇿Ozbekchaga o'zgartirish" if lang == 'ru' else "🇷🇺Поменять на русский"),
            KeyboardButton(
                text=("Добавить день рождение" if lang == "ru" else "Tug'ilgan kunini qo'shish") if birth is None else (
                    "Изменить день рождения" if lang == "ru" else "Tug'ilgan kunini o'zgartirish")),
        ],
        [
            KeyboardButton(text="Изменить номер телефона" if lang == "ru" else "Telefon raqamini o'zgartirish"),
            KeyboardButton(text=ru['back'] if lang == 'ru' else uz['back'])
        ]
    ]
    kb = ReplyKeyboardMarkup(resize_keyboard=True, keyboard=buttons)
    return kb


def phone_number_kb(lang: str):
    buttons = [
        [
            KeyboardButton(text="☎️ОТПРАВИТЬ КОНТАКТ" if lang == "ru" else "☎️TELEFON RAQAMINI YUBORISH",
                           request_contact=True)
        ],
        [
            KeyboardButton(text=ru['back'] if lang == 'ru' else uz['back'])
        ]
    ]

    kb = ReplyKeyboardMarkup(resize_keyboard=True, keyboard=buttons)
    return kb


def birthday_kb(lang: str):
    buttons = [
        [
            KeyboardButton(text=ru['back'] if lang == 'ru' else uz['back'])
        ]
    ]
    kb = ReplyKeyboardMarkup(resize_keyboard=True, keyboard=buttons)
    return kb


def generate_time_buttons(lang: str):
    now = datetime.now(tz=pytz.timezone('Asia/Tashkent'))
    buttons = [[
        KeyboardButton(text=ru['back'] if lang == 'ru' else uz['back'])
    ]]
    current_hour = 10
    if current_hour == 24:
        current_hour = 0

    for hour in range(current_hour, 21):
        time_str = f"{hour:02d}:00"
        buttons.append([KeyboardButton(text=time_str)])

    keyboard = ReplyKeyboardMarkup(resize_keyboard=True, keyboard=buttons)
    return keyboard


def dop_phone_num(lang: str) -> ReplyKeyboardMarkup:
    buttons = [
        [
            KeyboardButton(text=ru['supp_phone_num'] if lang == "ru" else uz["supp_phone_num"])
        ],
        [
            KeyboardButton(text=ru['back'] if lang == 'ru' else uz['back'])
        ]
    ]
    kb = ReplyKeyboardMarkup(resize_keyboard=True, keyboard=buttons)
    return kb


def pass_kb(lang: str):
    buttons = [
        [
            KeyboardButton(text=ru['supp_phone_num'] if lang == "ru" else uz["supp_phone_num"])
        ]
    ]

    kb = ReplyKeyboardMarkup(resize_keyboard=True, keyboard=buttons)
    return kb
