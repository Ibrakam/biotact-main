import os
import sys
import asyncio
import logging


from django.core.wsgi import get_wsgi_application

from config import dp, bot

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

# Установка переменной окружения для настроек Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'biotact.settings')
# print("DJANGO_SETTINGS_MODULE =", os.environ.get('DJANGO_SETTINGS_MODULE'))  # Логирование

application = get_wsgi_application()

from products.bot.handlers.bot_commands import main_router, callback_router2, broadcast_router
from products.bot.handlers.callback_queries import callback_router


async def main():
    dp.include_router(main_router)
    dp.include_router(callback_router)
    dp.include_router(callback_router2)
    dp.include_router(broadcast_router)
    await bot.delete_webhook()
    await dp.start_polling(bot)


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())
