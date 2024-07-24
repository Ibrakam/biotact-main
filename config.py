import os

from aiogram import Bot, Dispatcher, Router
from aiogram.client.default import DefaultBotProperties

from products.bot.handlers.some_func import json_loader
from dotenv import dotenv_values
print("Current working directory:", os.getcwd())

config_token = dotenv_values(".env")
print(config_token.keys())
api_key = config_token['API_KEY']
bot_token = config_token['BOT_TOKEN']

default = DefaultBotProperties(parse_mode='HTML')
bot = Bot(token=bot_token, default=default)
delete_mailing_router = Router()
broadcast_router = Router()
dp = Dispatcher()

ru_kb = json_loader()['menu']['ru']['inline_keyboard_button']
uz_kb = json_loader()['menu']['uz']['inline_keyboard_button']
ru = json_loader()['menu']['ru']
uz = json_loader()['menu']['uz']
