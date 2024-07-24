from aiogram.filters import Command
from aiogram.types import Message
from aiogram.fsm.context import FSMContext

from config import delete_mailing_router, broadcast_router, ru
from products.bot.handlers.bot_commands import get_lang, admins, get_all_user
from products.bot.keyboards.kb import menu_kb, product_back_to_category
from products.bot.states import MailingState

list_message_id = []


@delete_mailing_router.message(Command("delete_mailing"))
async def delete_mailing(message: Message):
    user_id = message.from_user.id
    lang = await get_lang(user_id)

    if user_id not in admins:
        await message.answer("Недостаточно прав для выполнения этой команды", reply_markup=menu_kb(lang))
        return

    # Получаем список ID сообщений для удаления
    messages_to_delete = list_message_id  # Предполагается, что list_message_id доступен глобально

    if not messages_to_delete:
        await message.answer("Нет активной рассылки для удаления", reply_markup=menu_kb(lang))
        return

    all_users = await get_all_user()
    success = 0
    unsuccess = 0
    errors = []

    for user in all_users:
        for msg_id in messages_to_delete:
            try:
                await message.bot.delete_message(chat_id=user.user_tg_id, message_id=msg_id)
                success += 1
            except Exception as e:
                unsuccess += 1
                errors.append(f"Ошибка удаления для пользователя {user.user_tg_id}: {str(e)}")

    # Очищаем список ID сообщений после попытки удаления
    list_message_id.clear()

    result_message = f"Удаление рассылки завершено!\n" \
                     f"Успешно удалено: {success}\n" \
                     f"Не удалось удалить: {unsuccess}"

    if errors:
        result_message += "\n\nПодробности ошибок:"
        for error in errors[:10]:  # Ограничиваем вывод первыми 10 ошибками
            result_message += f"\n- {error}"
        if len(errors) > 10:
            result_message += f"\n... и еще {len(errors) - 10} ошибок."

    await message.answer(result_message, reply_markup=menu_kb(lang))


@broadcast_router.message(MailingState.mailing)
async def mailing_admin(message: Message, state: FSMContext):
    user_id = message.from_user.id
    lang = await get_lang(user_id)
    if user_id in admins:
        if message.text == ru['inline_keyboard_button']['back']:
            await message.bot.send_message(message.from_user.id, "🚫Действие отменено", reply_markup=menu_kb(lang))
            await state.clear()
            return

        all_users = await get_all_user()
        success = 0
        unsuccess = 0
        global list_message_id
        list_message_id = []  # Очищаем список перед новой рассылкой

        for i in all_users:
            try:
                message_id = await message.bot.copy_message(chat_id=i.user_tg_id, from_chat_id=message.from_user.id,
                                                            message_id=message.message_id,
                                                            reply_markup=message.reply_markup)
                success += 1
                list_message_id.append((i.user_tg_id, message_id.message_id))  # Сохраняем пару (user_id, message_id)
            except:
                unsuccess += 1

        await message.bot.send_message(message.from_user.id, f"Рассылка завершена!\n"
                                                             f"Успешно отправлено: {success}\n"
                                                             f"Неуспешно: {unsuccess}",
                                       reply_markup=menu_kb(lang))
        print(list_message_id)
        await state.clear()
    else:
        await message.answer("Недостаточно прав для выполнения этой команды",
                             reply_markup=menu_kb(lang=await get_lang(user_id)))


@broadcast_router.message(Command("broadcast"))
async def handle_broadcast_command(message: Message, state: FSMContext):
    user_id = message.from_user.id
    if user_id in admins:
        await message.answer("Введите сообщение для рассылки, либо отправьте фотографии/видео с описанием",
                             reply_markup=product_back_to_category("ru"))
        await state.set_state(MailingState.mailing)
    else:
        await message.answer("Недостаточно прав для выполнения этой команды",
                             reply_markup=menu_kb(lang=await get_lang(user_id)))
