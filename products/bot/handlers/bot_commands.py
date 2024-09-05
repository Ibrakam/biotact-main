import os
from datetime import datetime
from urllib.parse import unquote


from aiogram.enums import ContentType
from aiogram.fsm.storage.base import StorageKey
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.utils.formatting import Text
from asgiref.sync import sync_to_async
from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, FSInputFile, ReplyKeyboardRemove, CallbackQuery, LabeledPrice, PreCheckoutQuery, Chat
from aiogram.filters import CommandStart, Command
from django.db.models import Q

from products.models import UserTG, UserCart, Product, Promocode, UsedPromocode, MyOrders, UserAddress
from config import ru, uz, dp, bot, broadcast_router
from products.bot.keyboards.inline_kb import choose_lang, about_us_menu_kb, menu_inline_kb, user_cart_edit, \
    wb_button, product_menu_kb, choose_payment_kb, confirm_order_kb, builder_inline_mk, OrderCallback
from products.bot.keyboards.kb import get_phone_num, menu_kb, stage_order_delivery_kb, send_location_kb, \
    confirm_location_kb, product_kb, category_product_menu, product_edit_menu, product_back_to_category, \
    leave_feedback_kb, settings_kb, phone_number_kb, birthday_kb, choose_time_kb, generate_time_buttons, location_kb
from products.bot.states import RegistrationState, StageOfOrderState, PromocodeState, LeaveFeedback, PromotionState, \
    SettingsState, TimeState, MailingState
from products.bot.locator import geolocators
from dotenv import dotenv_values

config_token = dotenv_values(".env")
CLICK_TOKEN = config_token['CLICK_TOKEN']
PAYME_TOKEN = config_token['PAYME_TOKEN']
ADMIN_ID = -4276762392

payment_router = Router()

main_router = Router()
callback_router2 = Router()

user_location = {}
finally_order = {}

admins = [889121031, -4276762392, 1249487413]


@sync_to_async
def get_all_user():
    try:
        user = UserTG.objects.all()
        return list(user)
    except Exception as e:
        print(e)


@sync_to_async
def get_user_by_phone(phone_number):
    try:
        user = UserTG.objects.get(phone_number=phone_number)
        return user
    except Exception as e:
        print(e)


# async def broadcast_all_users(message):
#     users = await get_all_user()
#     for user in users:
#         try:
#             await message.bot.send_message(user.user_tg_id, message.text.split(" ", 1)[1])
#         except Exception as e:
#             print(f"Не удалось отправить сообщение пользователю {user.phone_number}: {e}")
#             await message.bot.send_message(ADMIN_ID,
#                                            f"Не удалось отправить сообщение пользователю {user.phone_number}: {e}")


# Функция для отправки сообщения пользователю по номеру телефона
async def send_message_by_phone(phone_number, message, message_text):
    user = await get_user_by_phone(phone_number)
    if user:
        try:
            await message.bot.send_message(user.user_tg_id, message_text)
        except Exception as e:
            print(f"Не удалось отправить сообщение пользователю {user.user_tg_id}: {e}")
            await message.bot.send_message(ADMIN_ID,
                                           f"Не удалось отправить сообщение пользователю {user.phone_number}: {e}")

    else:
        print(f"Пользователь с номером телефона {phone_number} не найден.")
        await message.bot.send_message(ADMIN_ID, f"Пользователь с номером телефона {phone_number} не найден.")


# Пример команды для запуска рассылки всем пользователям


# Пример команды для отправки сообщения по номеру телефона
@broadcast_router.message(Command("send"))
async def handle_send_command(message: Message):
    user_id = message.from_user.id
    if user_id in admins:
        args = message.text.split(' ', 1)

        if len(args) != 2:
            await message.reply("Используйте команду в формате: /send <номер_телефона> <сообщение>")
            return

        print(args[1])
        phone_number, message_text = args[1].split(' ', 1)
        print(phone_number, message_text)
        await send_message_by_phone(phone_number, message, message_text)
        await message.reply("Сообщение отправлено.")
    else:
        await message.answer("Недостаточно прав для выполнения этой команды",
                             reply_markup=menu_kb(lang=await get_lang(user_id)))


@callback_router2.callback_query(F.data.in_(["cancel", "confirm", "change"]))
async def root(query: CallbackQuery, state: FSMContext):
    user_id = query.from_user.id
    lang = await get_lang(user_id)
    data = await state.get_data()
    info = await get_all_info(user_id)
    pay = f"{"💴 Наличные" if lang == "ru" else "💴 Naqd"}" if data["payment"][user_id] == "cash" else "💳" + \
                                                                                                     data["payment"][
                                                                                                         user_id]
    if query.data == "cancel":
        await state.clear()
        await query.message.delete()
        del_cart = await delete_user_cart(user_id)
        try:
            finally_order.pop(user_id)
        except:
            pass
        user_location.pop(user_id)
        await menu(lang=lang, message=query.message)
        await state.clear()
    elif query.data == "confirm":
        print(user_location)
        await query.message.delete()
        await user_order_conf_menu(user_id, message=query.message, kb=None, payment_method=pay)
        user_id = query.from_user.id
        print(pay)
        cart_text = await order_menu(user_id, state)
        data_for_option1 = {"action": "Reject", "user_id": user_id}
        data_for_option2 = {"action": "Accept", "user_id": user_id}
        if pay in ["💳Click", "💳Payme"]:
            # Пример заказанных продуктов

            del_cart = await delete_user_cart(user_id)
            try:
                if finally_order[user_id]:
                    await query.message.bot.send_location(chat_id=ADMIN_ID, latitude=finally_order[user_id]['latitude'],
                                                          longitude=finally_order[user_id]["longitude"])
            except:
                pass
            try:
                finally_order.pop(user_id)
            except:
                pass
            user_location.pop(user_id)
            await state.clear()
            await query.message.bot.send_message(ADMIN_ID, cart_text,
                                                 reply_markup=builder_inline_mk(
                                                     text=['Подтвердить', 'Отклонить'],
                                                     call_data=[data_for_option2,
                                                                data_for_option1]))
        else:
            try:
                if finally_order[user_id]:
                    await query.message.bot.send_location(chat_id=ADMIN_ID, latitude=finally_order[user_id]['latitude'],
                                                          longitude=finally_order[user_id]["longitude"])
            except:
                pass
            del_cart = await delete_user_cart(user_id)
            try:
                finally_order.pop(user_id)
            except:
                pass
            user_location.pop(user_id)
            await query.message.bot.send_message(ADMIN_ID, cart_text,
                                                 reply_markup=builder_inline_mk(
                                                     text=['Подтвердить', 'Отклонить'],
                                                     call_data=[data_for_option2,
                                                                data_for_option1]))
        await query.message.answer(
            "✅ Заказ принят.\nВам позвонят для уточнения заказа!" if lang == "ru" else "✅Buyurtma qabul qilindi.\nBuyurtmani aniqlashtirish uchun sizga qo'ng'iroq qilishadi")

        print("good" if info else "bad")
    elif query.data == "change":
        await user_order_conf_menu(user_id, query=query, kb=choose_payment_kb)


@callback_router2.pre_checkout_query(lambda query: True)
async def pre_check(pre_checkout_query: PreCheckoutQuery):
    await pre_checkout_query.bot.answer_pre_checkout_query(pre_checkout_query.id, ok=True)


async def order_menu(user_id, state: FSMContext):
    lang = await get_lang(user_id)
    data = await state.get_data()
    info = await get_all_info(user_id)
    user_cart = await get_user_cart(user_id)
    cart_text = ""
    total_price_all = 0
    for item in user_cart:
        cart_text += f"{item['product_name']} x {item['quantity']} = {"{:,.0f}".format(item['total_price']).replace(",", " ")} \n"
        total_price_all += item['total_price']
    pay = f"{"💴 Наличные" if lang == "ru" else "💴 Naqd"}" if data["payment"][user_id] == "cash" else "💳" + \
                                                                                                     data["payment"][
                                                                                                         user_id]

    delivery_or = f"🚕Доставка\n📍 {user_location[user_id][0]}" if \
        user_location[user_id][0] != 'biotact' else "🏃Самовывоз"

    delivery_or_uz = f"🚕Yetkazib berish \n📍 {user_location[user_id][0]}" if \
        user_location[
            user_id][0] != 'biotact' else "🏃 Olib ketish"

    discount = await get_user_promocode_cart(user_id)
    cart_text += (
        f'\n<b>Сумма доставки:</b> {"Бесплатная" if total_price_all >= 233_000 else "30 000 сум"}' if lang == 'ru' else f'\nYetkazib berish miqdori: {"Bepul" if total_price_all >= 233_000 else "30 000 som"}') if \
        user_location[user_id][0] != "biotact" else '\n'
    if discount:
        price_w_discount = total_price_all - (total_price_all * (discount.discount / 100))
        cart_text += f"\n{discount.discount}% скидка по промокоду {discount.promocode_code}" if lang == 'ru' else f"\n{discount.promocode_code} promokodi bilan {discount.discount}% chegirma"
        #       cart_text += (f'\n<b>Сумма доставки:</b> {"Бесплатная" if total_price_all >= 250_000 else "30 000 сум"}' if lang == 'ru' else f'\nYetkazib berish miqdori: {"Bepul" if total_price_all >= 250_000 else "30 000 som"}') if user_location[user_id][0] != "biotact" else '\n'
        cart_text += f"\n<b>Итого: </b> <s>{"{:,.0f}".format(total_price_all).replace(",", " ")} сум</s>  {"{:,.0f}".format(price_w_discount).replace(',', ' ')} сум" if lang == 'ru' else f"\n<b>Jami: </b><s>{"{:,.0f}".format(total_price_all).replace(',', ' ')} som</s> {"{:,.0f}".format(price_w_discount).replace(',', ' ')} so'm"
        cart_text += f"""\n\n{"Имя" if lang == 'ru' else "Ismi"}: {info[1]}
{"Телефон" if lang == "ru" else "Telefon"}: {info[0]}
{(f"Дoполнительный номер:{user_location[user_id][1]}" if lang == "ru" else f"Qo'shimcha raqam:{user_location[user_id][1]}") if user_location[user_id][1] else ("Дополнительный номер:НЕТ" if lang == "ru" else f"Qo'shimcha raqam:YOQ")}
{"Тип заказа" if lang == "ru" else "Turi"}: {delivery_or if lang == 'ru' else delivery_or_uz}
{"Тип оплаты" if lang == "ru" else "To'lov turi"}: 
{pay}: {"{:,.0f}".format(price_w_discount).replace(',', ' ')} сум
{(f"Комментарий к заказу: {user_location[user_id][2]}" if lang == "ru" else f"Xabar: {user_location[user_id][2]}") if user_location[user_id][2] else ("Комментарий к заказу: НЕТ" if lang == "ru" else f"Xabar: YOQ")}

        """
        return cart_text
    else:
        cart_text += f"\n<b>Итого: </b> {"{:,.0f}".format(total_price_all).replace(",", " ")} сум" if lang == 'ru' else f"\n<b>Jami: </b>{"{:,.0f}".format(total_price_all).replace(',', ' ')}so'm"
        cart_text += f"""\n\n{"Имя" if lang == 'ru' else "Ismi"}: {info[1]}
{"Телефон" if lang == "ru" else "Telefon"}: {info[0]}
{(f"Дoполнительный номер:{user_location[user_id][1]}" if lang == "ru" else f"Qo'shimcha raqam:user_location[user_id][1]") if user_location[user_id][1] else ("Дополнительный номер:НЕТ" if lang == "ru" else f"Qo'shimcha raqam:YOQ")}
{"Тип заказа" if lang == "ru" else "Turi"}: {delivery_or if lang == 'ru' else delivery_or_uz}
{"Тип оплаты" if lang == "ru" else "To'lov turi"}:
{pay}: {"{:,.0f}".format(total_price_all).replace(",", " ")}
{(f"Комментарий к заказу: {user_location[user_id][2]}" if lang == "ru" else f"Xabar: {user_location[user_id][2]}") if user_location[user_id][2] else ("Комментарий к заказу: НЕТ" if lang == "ru" else f"Xabar: YOQ")}
                        """
        return cart_text


@sync_to_async
def create_user_order(user_id, order_text):
    MyOrders.objects.create(user_id=user_id, order_text=order_text)
    return True


@main_router.callback_query(OrderCallback.filter())
async def root(query: CallbackQuery, callback_data: OrderCallback):
    lang = await get_lang(callback_data.user_id)
    if callback_data.action == "Accept":
        if lang == "ru":
            await query.message.bot.send_message(callback_data.user_id,
                                                 "😊Ваш заказ оформлен и скоро будет у вас!",
                                                 reply_markup=menu_kb(lang))
        else:
            await query.message.bot.send_message(callback_data.user_id,
                                                 "😊Sizning buyurtmangiz bajarildi va tez orada sizda bo'ladi!",
                                                 reply_markup=menu_kb(lang))
        admin_response_text = query.message.text + "\n\n✅ Заказ принят"
        result = await create_user_order(callback_data.user_id, query.message.text)
    elif callback_data.action == "Reject":
        if lang == "ru":
            await query.message.bot.send_message(callback_data.user_id,
                                                 "😔 К сожалению вы отклонили заказ",
                                                 reply_markup=menu_kb(lang))
        else:
            await query.message.bot.send_message(callback_data.user_id,
                                                 "Buyurtma qabul qilinmadi. Buyurtmani aniqlashtirish uchun sizga qo'ng'iroq qilishadi",
                                                 reply_markup=menu_kb(lang))
        admin_response_text = query.message.text + "\n\n❌ Заказ отклонен"

    await query.message.edit_text(admin_response_text, reply_markup=None)


@main_router.message(Command("terms"))
async def terms(message: Message):
    user_id = message.from_user.id
    lang = await get_lang(user_id)
    await message.reply(ru['terms_text'] if lang == "ru" else uz['terms_text'], parse_mode="HTML")


# print(product_service.get_all_product())

async def menu(lang, message=None, query=None):
    try:
        user_location.pop(message.from_user.id if message else query.from_user.id)
    except:
        pass
    if lang == 'ru':
        try:
            if message:
                await message.answer("Для заказа нажмите 🛍️Заказать", reply_markup=menu_kb(lang))
                await message.answer(ru['message_hello'], parse_mode='HTML',
                                     reply_markup=menu_inline_kb(lang))
            elif query:

                await query.message.delete()
                # await query.message.answer_photo(photo=FSInputFile(script_path), caption=ru['message_hello'],
                #                                  parse_mode='HTML', reply_markup=menu_kb(lang))
                await query.message.answer("Для заказа нажмите 🛍️Заказать", reply_markup=menu_kb(lang))
                await query.message.answer(ru['message_hello'], parse_mode='HTML',
                                           reply_markup=menu_inline_kb(lang))
        except Exception as e:
            if message:
                print(e)

                # await message.answer_photo(photo=FSInputFile(script_path), caption=ru['message_hello'], parse_mode='HTML',
                #                            reply_markup=menu_kb(lang))
                await message.answer("Для заказа нажмите 🛍️Заказать", reply_markup=menu_kb(lang))
                await message.answer(ru['message_hello'], parse_mode='HTML',
                                     reply_markup=menu_inline_kb(lang))
            elif query:
                await query.message.delete()
                # await query.message.answer_photo(photo=FSInputFile(script_path), caption=ru['message_hello'],
                #                                  parse_mode='HTML', reply_markup=menu_kb(lang))
                await query.message.answer("Для заказа нажмите 🛍️Заказать", reply_markup=menu_kb(lang))
                await query.message.answer(ru['message_hello'], parse_mode='HTML',
                                           reply_markup=menu_inline_kb(lang))

    elif lang == 'uz':
        try:

            if message:
                # await message.answer_photo(photo=FSInputFile(script_path), caption=uz['message_hello'], parse_mode='HTML',
                #                            reply_markup=menu_kb(lang))
                await message.answer("Buyurtma berish uchun 🛍️buyurtma tugmasini bosing", reply_markup=menu_kb(lang))
                await message.answer(uz['message_hello'], parse_mode='HTML',
                                     reply_markup=menu_inline_kb(lang))

            elif query:
                await query.message.delete()
                # await query.message.answer_photo(photo=FSInputFile(script_path), caption=uz['message_hello'],
                #                                  parse_mode='HTML', reply_markup=menu_kb(lang))
                await query.message.answer("Buyurtma berish uchun 🛍️buyurtma tugmasini bosing",
                                           reply_markup=menu_kb(lang))
                await query.message.answer(uz['message_hello'], parse_mode='HTML',
                                           reply_markup=menu_inline_kb(lang))
        except Exception as e:
            if message:
                # await message.answer_photo(photo=FSInputFile(script_path), caption=uz['message_hello'], parse_mode='HTML',
                #                            reply_markup=menu_kb(lang))
                await message.answer("Buyurtma berish uchun 🛍️buyurtma tugmasini bosing", reply_markup=menu_kb(lang))
                await message.answer(uz['message_hello'], parse_mode='HTML',
                                     reply_markup=menu_inline_kb(lang))

            elif query:
                await query.message.delete()
                # await query.message.answer_photo(photo=FSInputFile(script_path), caption=uz['message_hello'],
                #                                  parse_mode='HTML', reply_markup=menu_kb(lang))
                await query.message.answer("Buyurtma berish uchun 🛍️buyurtma tugmasini bosing",
                                           reply_markup=menu_kb(lang))
                await query.message.answer(uz['message_hello'], parse_mode='HTML',
                                           reply_markup=menu_inline_kb(lang))


@sync_to_async
def get_user(user_id):
    user = UserTG.objects.get(user_tg_id=user_id)
    if user:
        return True
    return False


@sync_to_async
def get_user_info(user_id):
    user = UserTG.objects.get(user_tg_id=user_id)
    if user:
        return user
    return False


@sync_to_async
def get_lang(user_id):
    return UserTG.objects.get(user_tg_id=user_id).lang


@sync_to_async
def update_lang(user_id, lang):
    try:
        UserTG.objects.filter(user_tg_id=user_id).update(lang=lang)
        return True
    except Exception as e:
        raise e


@sync_to_async
def update_phone(user_id, phone_number):
    try:
        UserTG.objects.filter(user_tg_id=user_id).update(phone_number=phone_number)
        return True
    except Exception as e:
        raise e


@sync_to_async
def update_birthday(user_id, birthday):
    try:
        UserTG.objects.filter(user_tg_id=user_id).update(birthday=birthday)
        return True
    except Exception as e:
        raise e


@main_router.message(CommandStart())
async def start(message: Message, state: FSMContext):
    data = await state.get_data()
    print(data.get('message'))
    try:
        checker = await get_user(message.from_user.id)
        if checker:
            lang = await get_lang(message.from_user.id)
            await menu(lang=lang, message=message)
        else:
            # await message.answer_photo(photo=FSInputFile(photo_path),
            #                            caption=ru['message_hello'] + "\n" + uz['message_hello'], parse_mode='HTML')
            await message.answer(ru['message_hello'] + "\n" + uz['message_hello'], parse_mode='HTML')
            await message.answer("Выберите язык/Tilni tanlang", reply_markup=choose_lang())
    except Exception as e:
        # await message.answer_photo(photo=FSInputFile(photo_path),
        #                            caption=ru['message_hello'] + "\n" + uz['message_hello'], parse_mode='HTML')
        await message.answer(ru['message_hello'] + "\n" + uz['message_hello'], parse_mode='HTML')

        await message.answer("""Здравствуйте! Добро пожаловать в наш бот!
Давайте для начала выберем язык
обслуживания!""", reply_markup=choose_lang())
        raise e


"""States"""


@main_router.message(RegistrationState.get_name)
async def get_name(message: Message, state: FSMContext):
    data = await state.get_data()
    data[str(message.from_user.id)].append(message.text)
    if data[str(message.from_user.id)][0] == 'ru':
        await message.answer(ru['message_reg_phone'], reply_markup=get_phone_num(data[str(message.from_user.id)][0]))
        await state.set_state(RegistrationState.get_phone)
    else:
        await message.answer(uz['message_reg_phone'], reply_markup=get_phone_num(data[str(message.from_user.id)][0]))
        await state.set_state(RegistrationState.get_phone)


@sync_to_async
def add_user(user_id, name, lang, phone_number):
    UserTG.objects.create(user_tg_id=user_id, user_name=name, lang=lang, phone_number=phone_number)
    return True


@main_router.message(RegistrationState.get_phone)
async def get_phone(message: Message, state: FSMContext):
    user_id = message.from_user.id
    data = await state.get_data()
    if message.contact:
        phone_number = message.contact.phone_number
        lang = data[str(message.from_user.id)][0]
        name = data[str(message.from_user.id)][1]
        result = await add_user(user_id, name, lang, phone_number)
        if result:
            await message.answer('Спасибо за регистрацию!', reply_markup=ReplyKeyboardRemove())
            await state.clear()
            await menu(message=message, lang=lang)
    else:
        await message.answer('Пожалуйста, введите свой номер телефона')
        await state.set_state(RegistrationState.get_phone)


@main_router.message(F.text.in_([ru['inline_keyboard_button']['about_us'], uz['inline_keyboard_button']['about_us']]))
async def about_us(message: Message):
    user_id = message.from_user.id
    lang = await get_lang(user_id)
    if lang == 'ru':
        await message.answer(ru['about_us_menu'], parse_mode="HTML", reply_markup=about_us_menu_kb(lang='ru'))
    elif lang == 'uz':
        await message.answer(uz['about_us_menu'], parse_mode="HTML", reply_markup=about_us_menu_kb(lang='uz'))


@main_router.message(F.text.in_(["🇷🇺ru", "🇺🇿uz"]))
async def public_offer(message: Message):
    user_id = message.from_user.id
    if message.text == "🇷🇺ru":
        result = await update_lang(user_id, 'ru')
        if result:
            lang = await get_lang(user_id)
            await menu(message=message, lang=lang)
    elif message.text == "🇺🇿uz":
        result = await update_lang(user_id, 'uz')
        if result:
            lang = await get_lang(user_id)
            await menu(message=message, lang=lang)


@sync_to_async
def get_user_cart(user_id):
    user_cart_items = UserCart.objects.filter(user_id=user_id)
    user_cart_dict = {}

    for item in user_cart_items:
        product_name = item.products.product_name
        if product_name in user_cart_dict:
            user_cart_dict[product_name]['quantity'] += item.quantity
            user_cart_dict[product_name]['total_price'] += item.total_price
        else:
            user_cart_dict[product_name] = {
                "id": item.products.id,
                'product_name': product_name,
                'quantity': item.quantity,
                'total_price': item.total_price
            }
    user_cart_list = list(user_cart_dict.values())
    print(user_cart_list)
    return user_cart_list


@sync_to_async
def get_user_promocode_cart(user_id):
    user_cart_items = UserCart.objects.filter(user_id=user_id)
    try:
        if not user_cart_items.first().promocode:
            return None

        user_promocode = Promocode.objects.filter(promocode_code=user_cart_items.first().promocode).first()
        return user_promocode if user_promocode else None
    except Exception as e:
        print(e)
        return None


async def user_cart_menu(lang: str, user_id, message=None, query=None):
    print(user_location)
    if message:
        user_cart = await get_user_cart(user_id)
        if user_cart:
            try:
                discount = await get_user_promocode_cart(user_id)
            except Exception as e:
                print(e)
                discount = None
            total_price_all = 0
            cart_text = ""
            for item in user_cart:
                cart_text += f"<b>{item['product_name']} </b>- {item['quantity']} шт. - {"{:,.0f}".format(item['total_price']).replace(",", " ")} сум\n"
                total_price_all += item['total_price']

            if discount:
                price_w_discount = total_price_all - (total_price_all * (discount.discount / 100))
                cart_text += f"\n{discount.discount}% скидка по промокоду {discount.promocode_code}" if lang == 'ru' else f"\n{discount.promocode_code} promokodi bilan {discount.discount}% chegirma"
                await bot.send_message(
                    chat_id=user_id,
                    text=cart_text + f"\n\n<b>Итого: </b> <s>{"{:,.0f}".format(total_price_all).replace(",", " ")}</s>  {"{:,.0f}".format(price_w_discount).replace(',', ' ')} сум" if lang == 'ru' else f"\n<b>Jami: </b><s>{"{:,.0f}".format(total_price_all).replace(',', ' ')}</s> {"{:,.0f}".format(price_w_discount).replace(',', ' ')} so'm",
                    reply_markup=user_cart_edit(lang, True if discount > 0 else False, user_cart),
                    parse_mode="HTML"
                )
            else:
                await bot.send_message(
                    chat_id=user_id,
                    text=cart_text + f"\n\n<b>Итого:</b> {"{:,.0f}".format(total_price_all).replace(",", " ")} сум" if lang == 'ru' else f"\n\n<b>Jami:</b> {"{:,.0f}".format(total_price_all).replace(",", " ")} so'm",
                    reply_markup=user_cart_edit(lang, True if discount else False, user_cart),
                    parse_mode="HTML"
                )

        else:
            cart_text = "Ваша корзина пуста" if lang == 'ru' else "Sizning savatingiz bo'sh"

            await message.answer(cart_text,
                                 reply_markup=user_cart_edit(lang, False, user_cart))
    elif query:
        user_cart = await get_user_cart(query.from_user.id)

        if user_cart:
            discount = await get_user_promocode_cart(query.from_user.id)
            total_price_all = 0
            cart_text = "<b>Корзина:\n\n</b>" if lang == 'ru' else "<b>Savatdagi mahsulotlaringiz:</b>\n\n"
            for item in user_cart:
                cart_text += f"- {item['quantity']} шт. - {"{:,.0f}".format(item['total_price']).replace(",", " ")} сум\n"
                total_price_all += item['total_price']
            if discount:
                total_price_all -= total_price_all * (discount.discount / 100)
                await query.message.edit_text(
                    cart_text + f"\n\n{"{:,.0f}".format(total_price_all).replace(",", " ")} сум c учетом скидки {discount}%" if lang == 'ru' else f"\n\n{"{:,.0f}".format(total_price_all).replace(",", " ")} so'm {discount}% skidka bilan",
                    reply_markup=user_cart_edit(lang, True if discount else False, user_cart), parse_mode="HTML")
            else:
                await query.message.edit_text(
                    cart_text + f"\n\n {"{:,.0f}".format(total_price_all).replace(",", " ")} сум" if lang == 'ru' else f"\n\n {"{:,.0f}".format(total_price_all).replace(",", " ")} so'm",
                    reply_markup=user_cart_edit(lang, True if discount else False, user_cart), parse_mode="HTML")
        else:
            cart_text = "Ваша корзина пуста" if lang == 'ru' else "Sizning savatingiz bo'sh"

            await query.message.edit_text(cart_text,
                                          reply_markup=user_cart_edit(lang, False, user_cart))


storage = MemoryStorage()


async def user_cart_from_tg(user_id):

    lang = await get_lang(user_id)
    storage_key = StorageKey(user_id=user_id, bot_id=bot.id, chat_id=user_id)
    state = FSMContext(storage=storage, key=storage_key)
    chat = Chat(id=user_id, type="private")
    message = Message(message_id=0, date=datetime.now(), chat=chat)
    await state.set_state(StageOfOrderState.choose_product)
    await bot.send_message(user_id, "Корзина:" if lang == 'ru' else "Savatingiz:",
                           reply_markup=product_back_to_category(lang))
    await user_cart_menu(message=message, lang=lang, user_id=user_id)


# except Exception as e:
#     await bot.send_message(user_id, ("Давайте начнем заказ" if lang == 'ru' else "Buyurtmani boshlaymiz"),
#                            reply_markup=stage_order_delivery_kb(lang))
#     await state.set_state(StageOfOrderState.get_delivery)
#     raise e


@main_router.message(F.text.in_([ru['inline_keyboard_button']['cart'], uz['inline_keyboard_button']['cart']]))
async def cart(message: Message, state: FSMContext):
    lang = await get_lang(message.from_user.id)
    try:
        if user_location[message.from_user.id]:
            await state.set_state(StageOfOrderState.choose_product)
            await message.answer("Корзина:" if lang == 'ru' else "Savatingiz:",
                                 reply_markup=product_back_to_category(lang))
            await user_cart_menu(message=message, lang=lang, user_id=message.from_user.id)

        else:
            await message.answer("Давайте начнем заказ" if lang == 'ru' else "Buyurtmani boshlaymiz",
                                 reply_markup=stage_order_delivery_kb(lang))
            await state.set_state(StageOfOrderState.get_delivery)
    except Exception as e:
        await message.answer("Давайте начнем заказ" if lang == 'ru' else "Buyurtmani boshlaymiz",
                             reply_markup=stage_order_delivery_kb(lang))
        await state.set_state(StageOfOrderState.get_delivery)
        raise e


@sync_to_async
def get_all_product():
    return list(Product.objects.all())


@main_router.message(Command("order"))
@main_router.message(
    F.text.in_([ru['inline_keyboard_button']['choose_product'], uz['inline_keyboard_button']['choose_product']]))
async def choose_product(message: Message, state: FSMContext):
    user_id = message.from_user.id
    lang = await get_lang(user_id)
    all_pr = await get_all_product()
    print(lang)
    if lang == 'ru':
        await message.answer("Выберите тип доставки",
                             reply_markup=stage_order_delivery_kb(lang))
        await state.set_state(StageOfOrderState.get_delivery)
    else:
        await message.answer("Yetkazib berish turini tanlang",
                             reply_markup=stage_order_delivery_kb(lang))
        await state.set_state(StageOfOrderState.get_delivery)


@sync_to_async
def get_adress(user_id):
    try:
        adress = list(UserAddress.objects.filter(user_id=user_id).all())
        return adress
    except:
        return None


@main_router.message(StageOfOrderState.get_delivery)
async def get_delivery(message: Message, state: FSMContext):
    user_id = message.from_user.id
    lang = await get_lang(user_id)
    all_pr = await get_all_product()
    my_adress = await get_adress(user_id)
    print(my_adress)
    if message.text == ru['inline_keyboard_button']['delivery'] or message.text == uz['inline_keyboard_button'][
        'delivery']:
        await message.answer(
            "Чтобы продолжить заказ, отправьте свое местоположение" if lang == 'ru' else "Iltimos, manzilni yuboring",
            reply_markup=send_location_kb(lang, my_adress))
        await state.set_state(StageOfOrderState.get_location)
    elif message.text == uz['inline_keyboard_button']['pickup'] or message.text == ru['inline_keyboard_button'][
        'pickup']:
        user_location[user_id] = ["biotact"]

        await message.answer(
            f"Нажмите на {"📍Отправить локацию магазина"}" if lang == 'ru' else "📍Do'kon manzilini yuborish tugmasini bosing",
            reply_markup=location_kb(lang))

        await state.set_state(StageOfOrderState.location_address)
    elif message.text == uz['inline_keyboard_button']['back'] or message.text == ru['inline_keyboard_button']['back']:
        await menu(lang=lang, message=message)
        await state.clear()


@main_router.message(StageOfOrderState.location_address)
async def root(message: Message, state: FSMContext):
    user_id = message.from_user.id
    lang = await get_lang(user_id)
    if message.text in [ru['inline_keyboard_button']['back'], uz['inline_keyboard_button']['back']]:
        user_location.pop(user_id)
        await menu(lang=await get_lang(message.from_user.id), message=message)
        await state.clear()
    elif message.text in ["📍Отправить локацию магазина", "📍Magazin manzilini yuborish"]:
        await message.answer_location(latitude=41.348964, longitude=69.179064)
        await message.answer(ru['address'] if lang == 'ru' else uz['address'])
        await message.answer(ru['choose_product_menu_2'] if lang == 'ru' else uz['choose_product_menu_2'],
                             parse_mode="HTML",
                             reply_markup=category_product_menu(lang))
        message_id = await message.answer(
            f"""{"Закажите через новое удобное меню" if lang == "ru" else "Buyurtmani qabul qilish uchun qulay menyu"} 👇😉""",
            reply_markup=wb_button(lang))
        await state.update_data(message_id=message_id)
        data = await state.get_data()
        print(data.get('message_id'))
        await state.update_data(message_id=message_id)
        await state.set_state(StageOfOrderState.start_order)


@sync_to_async
def add_adress(user_id, address):
    UserAddress.objects.create(user_id=user_id, address=address)
    return True


@main_router.message(StageOfOrderState.get_location)
async def get_location(message: Message, state: FSMContext):
    user_id = message.from_user.id
    lang = await get_lang(user_id)
    my_address = await get_adress(user_id)
    if message.location:
        longitude = message.location.longitude
        latitude = message.location.latitude
        finally_order[user_id] = {"longitude": longitude, "latitude": latitude}
        location = geolocators(latitude, longitude)
        await message.answer(
            f"Ваш адрес: {location}" + """\nПодтвердите адрес?""" if lang == "ru" else f"Sizning manzilingiz: {location}" + """
Tasdiqlash?""", reply_markup=confirm_location_kb(lang))
        user_location[user_id] = [location]
    if message.text == '✅Подтвердить' or message.text == '✅Tasdiqlash':
        await message.answer(
            "Укажите удобное для вас время 🕒" if lang == "ru" else "Buyurtmani qabul qilish uchun qulay vaqtni tanlang 🕒",
            reply_markup=choose_time_kb(lang))
        await state.set_state(StageOfOrderState.get_time)
    if message.text in [ru['inline_keyboard_button']['send_location1'], uz['inline_keyboard_button']['send_location1']]:
        longitude = finally_order[user_id]['longitude']
        latitude = finally_order[user_id]['latitude']
        location = geolocators(latitude, longitude)
        result = await add_adress(user_id, location)
        await message.answer("✅Адрес добавлен" if lang == "ru" else "✅Manzil qo'shildi")

    if message.text in [i.address for i in my_address]:
        await message.answer(
            "Укажите удобное для вас время 🕒" if lang == "ru" else "Buyurtmani qabul qilish uchun qulay vaqtni tanlang 🕒",
            reply_markup=choose_time_kb(lang))
        user_location[user_id] = [message.text]
        await state.set_state(StageOfOrderState.get_time)

    if message.text == uz['inline_keyboard_button']['back'] or message.text == ru['inline_keyboard_button']['back']:
        await state.clear()
        await menu(lang=lang, message=message)


@main_router.message(StageOfOrderState.get_time)
async def get_time(message: Message, state: FSMContext):
    user_id = message.from_user.id
    lang = await get_lang(user_id)
    my_address = await get_adress(user_id)
    print(my_address)
    if message.text == uz['inline_keyboard_button']['back'] or message.text == ru['inline_keyboard_button']['back']:
        await message.answer("Пожалуйста, скиньте свой адрес" if lang == 'ru' else "Iltimos, manzilni yuboring",
                             reply_markup=send_location_kb(lang, my_address))
        await state.set_state(StageOfOrderState.get_location)
    elif message.text in ["Ближайшее время", "Tez orada"]:
        await message.answer(ru['choose_product_menu_1'] if lang == 'ru' else uz['choose_product_menu_1'],
                             parse_mode="HTML",
                             reply_markup=category_product_menu(lang))
        await state.set_state(StageOfOrderState.start_order)
        await message.answer(
            f"""{"Закажите через новое удобное меню" if lang == "ru" else "Buyurtmani qabul qilish uchun qulay menyu"} 👇😉""",
            reply_markup=wb_button(lang))
    elif message.text in ["Выбрать время", "Aniq muddatda"]:
        await message.answer(
            "Укажите удобное для вас время 🕒" if lang == "ru" else "Buyurtmani qabul qilish uchun qulay vaqtni tanlang 🕒",
            reply_markup=generate_time_buttons(lang))
        await state.set_state(TimeState.choose_time)


@main_router.message(TimeState.choose_time)
async def choose_time_func(message: Message, state: FSMContext):
    user_id = message.from_user.id
    lang = await get_lang(user_id)
    selected_time = message.text
    if message.text == uz['inline_keyboard_button']['back'] or message.text == ru['inline_keyboard_button']['back']:
        await message.answer(
            "Укажите удобное для вас время 🕒" if lang == "ru" else "Buyurtmani qabul qilish uchun qulay vaqtni tanlang 🕒",
            reply_markup=choose_time_kb(lang))
        await state.set_state(StageOfOrderState.get_time)
        return
    try:
        datetime.strptime(selected_time, '%H:%M')
        await message.answer(ru['choose_product_menu_1'] if lang == 'ru' else uz['choose_product_menu_1'],
                             parse_mode="HTML",
                             reply_markup=category_product_menu(lang))
        await state.set_state(StageOfOrderState.start_order)
        message_id = await message.answer(
            f"""{"Закажите через новое удобное меню" if lang == "ru" else "Buyurtmani qabul qilish uchun qulay menyu"} 👇😉""",
            reply_markup=wb_button(lang))
        await state.update_data(message_id=message_id)
        data = await state.get_data()
        print(data.get('message_id'))
    except ValueError:
        await message.answer("Неправильный формат времени" if lang == 'ru' else "Noto'g'ri vaqtni kiritdingiz",
                             reply_markup=choose_time_kb(lang))


# @main_router.message(F.text == ru['inline_keyboard_button']['back'] or F.text == uz['inline_keyboard_button']['back'])
# async def back_to_menu(message: Message, state: FSMContext):
#     user_id = message.from_user.id
#     lang = await get_lang(user_id)
#     await state.clear()
#     await menu(lang=lang, message=message)


@sync_to_async
def get_user_promocode(user_id=None, lang=None, promocode=None):
    # Проверка, что промокод существует
    if not Promocode.objects.filter(promocode_code=promocode).exists():
        return "❌Данного промокода нет" if lang == 'ru' else '❌Bu promokod mavjud emas'

    # Проверка, что промокод уже был использован данным пользователем
    if UsedPromocode.objects.filter(Q(promocode=promocode) & Q(user_id=user_id)).exists():
        return "Такой промокод уже использован" if lang == 'ru' else 'Bu promokod avval foydalanilgan'

    # Получение данных о промокоде
    promocode_user = Promocode.objects.filter(promocode_code=promocode)
    if promocode_user.exists():
        UserCart.objects.filter(user_id=user_id).update(promocode=promocode_user.first().promocode_code)
        return "✅ Промокод активирован" if lang == 'ru' else 'Promokod aktivlashtirildi'
    else:
        return False


@sync_to_async
def update_user_cart(user_id, promocode):
    UserCart.objects.filter(user_id=user_id).update(promocode=promocode)


@main_router.message(PromocodeState.get_promocode)
async def get_promocode(message: Message, state: FSMContext):
    user_id = message.from_user.id
    lang = await get_lang(user_id)
    result = await get_user_promocode(user_id, lang, message.text)
    await state.clear()
    await message.answer(result)
    await user_cart_menu(lang=lang, message=message, user_id=user_id)


@sync_to_async
def get_all_info(user_id):
    user = UserTG.objects.get(user_tg_id=user_id)
    return [user.phone_number, user.user_name]


@sync_to_async
def delete_user_cart(user_id):
    UserCart.objects.filter(user_id=user_id).delete()
    return True


@main_router.message(StageOfOrderState.user_cart)
async def root(message: Message, state: FSMContext):
    user_id = message.from_user.id
    lang = await get_lang(user_id)
    if message.text in [ru['inline_keyboard_button']['back'], uz['inline_keyboard_button']['back']]:
        await state.clear()
        await message.delete()
        await user_cart_menu(lang=lang, message=message, user_id=user_id)
        return
    if message.text in [ru['inline_keyboard_button']['supp_phone_num'], uz['inline_keyboard_button']['supp_phone_num']]:
        await state.set_state(StageOfOrderState.user_payment)
        await user_order_conf_menu(user_id, message=message)
        user_location[user_id].append(None)
        return
    comment = message.text
    user_location[user_id].append(comment)
    await state.set_state(StageOfOrderState.user_payment)
    await user_order_conf_menu(user_id, message=message)


def get_delivery_text(user_id, total_price_all, lang):
    if not user_location.get(user_id) or not user_location[user_id] or user_location[user_id][0] == "biotact":
        return '\n'

    if lang == 'ru':
        delivery_price = "Бесплатная" if total_price_all >= 233_000 else "30 000 сум"
        return f'\n<b>Сумма доставки:</b> {delivery_price}'
    else:
        delivery_price = "Bepul" if total_price_all >= 233_000 else "30 000 som"
        return f'\nYetkazib berish miqdori: {delivery_price}'


async def user_order_conf_menu(user_id, query=None, message=None, kb=choose_payment_kb, payment_method=""):
    lang = await get_lang(user_id)
    info = await get_all_info(user_id)
    print(user_location)
    cart_text = ""
    user_cart = await get_user_cart(user_id)
    discount = await get_user_promocode_cart(user_id)
    total_price_all = 0
    for item in user_cart:
        cart_text += f"{item['product_name']} x {item['quantity']} = {"{:,.0f}".format(item['total_price']).replace(",", " ")} \n"
        total_price_all += item['total_price']

    delivery_or = f"🚕Доставка\n📍 {user_location[user_id][0]}" if \
        user_location[user_id][0] != 'biotact' else "🏃Самовывоз"

    delivery_or_uz = f"🚕Yetkazib berish \n📍 {user_location[user_id][0]}" if \
        user_location[
            user_id][0] != 'biotact' else "🏃 Olib ketish"
    cart_text += get_delivery_text(user_id, total_price_all, lang)
    if discount:
        price_w_discount = total_price_all - (total_price_all * (discount / 100))
        cart_text += f"\n{discount}% промокод." if lang == 'ru' else f"\n{discount}% chegirma."
        cart_text += f"\n<b>Итого: </b> <s>{"{:,.0f}".format(total_price_all).replace(",", " ")} сум</s>  {"{:,.0f}".format(price_w_discount).replace(',', ' ')}сум" if lang == 'ru' else f"\n<b>Jami: </b><s>{"{:,.0f}".format(total_price_all).replace(',', ' ')} som</s> {"{:,.0f}".format(price_w_discount).replace(',', ' ')} so'm"
        cart_text += f"""\n\n{"Имя" if lang == 'ru' else "Ismi"}: {info[1]}
{"Телефон" if lang == "ru" else "Telefon"}: {info[0]}
{"Тип заказа" if lang == "ru" else "Turi"}: {delivery_or if lang == 'ru' else delivery_or_uz}
{"Тип оплаты" if lang == "ru" else "To'lov turi"}: 
{payment_method}: {"{:,.0f}".format(price_w_discount).replace(',', ' ')} сум
"""
        if message:
            await message.answer(cart_text, reply_markup=kb(lang) if kb else None)
        elif query:
            await query.message.edit_text(cart_text, reply_markup=kb(lang) if kb else None)
    else:
        cart_text += f"\n<b>Итого: </b> {"{:,.0f}".format(total_price_all).replace(",", " ")} сум" if lang == 'ru' else f"\n<b>Jami: </b>{"{:,.0f}".format(total_price_all).replace(',', ' ')}so'm"
        cart_text += f"""\n\n{"Имя" if lang == 'ru' else "Ismi"}: {info[1]}
{"Телефон" if lang == "ru" else "Telefon"}: {info[0]}
{"Тип заказа" if lang == "ru" else "Turi"}: {delivery_or if lang == 'ru' else delivery_or_uz}
{"Тип оплаты" if lang == "ru" else "To'lov turi"}:
{payment_method}: {"{:,.0f}".format(total_price_all).replace(",", " ")}
            """
        if message:
            await message.answer(cart_text, reply_markup=kb(lang) if kb else None)
        elif query:
            await query.message.edit_text(cart_text, reply_markup=kb(lang) if kb else None)


@main_router.message(StageOfOrderState.user_payment)
async def payment(message: Message, state: FSMContext):
    user_id = message.from_user.id
    lang = await get_lang(user_id)
    data = await state.get_data()
    print(data)
    payment_data = f"{"💴 Наличные" if lang == "ru" else "💴 Naqd"}" if data["payment"][user_id] == "cash" else "💳" + \
                                                                                                              data[
                                                                                                                  "payment"][
                                                                                                                  user_id]

    if message.text == ru['inline_keyboard_button']['supp_phone_num'] or message.text == uz['inline_keyboard_button'][
        'supp_phone_num']:
        await user_order_conf_menu(message=message, user_id=user_id, kb=confirm_order_kb, payment_method=payment_data)
        user_location[user_id].append(None)
        return
    phone_num = message.text

    user_location[user_id].append(phone_num)
    await user_order_conf_menu(message=message, user_id=user_id, kb=confirm_order_kb, payment_method=payment_data)


@sync_to_async
def get_all_product_by(category):
    if category in ["Мерч", "Merch"]:
        products = list(Product.objects.filter(category='merch').all())
    elif category in ["Эксклюзивные сеты", "Ekskluziv Setlar"]:
        products = list(Product.objects.filter(category='sets').all())
    elif category in ["Продукция", "Mahsulotlar"]:
        products = list(Product.objects.filter(category='products').all())
    else:
        return False

    return products


@main_router.message(StageOfOrderState.start_order)
# @main_router.message(F.text.in_(["Продукты", "Mahsulotlar", "Сеты", "Setlar", "Мерч", "Merch"]))
async def gain(message: Message, state: FSMContext):
    user_id = message.from_user.id
    lang = await get_lang(user_id)
    all_product = await get_all_product_by(message.text)
    # all_product_dict[user_id] = all_product
    if message.text in ["Продукция", "Mahsulotlar", "Эксклюзивные сеты", "Ekskluziv Setlar", "Мерч", "Merch"]:
        await state.set_state(StageOfOrderState.choose_product)
        await message.answer("Выберите продукт" if lang == "ru" else "Productni tanlang",
                             reply_markup=product_kb(lang, all_product))

    elif message.text in [ru['inline_keyboard_button']['back'], uz['inline_keyboard_button']['back']]:
        await state.set_state(StageOfOrderState.get_delivery)
        if lang == 'ru':
            await message.answer("Выберите тип доставки",
                                 reply_markup=stage_order_delivery_kb(lang))
            await state.set_state(StageOfOrderState.get_delivery)
        else:
            await message.answer("Yetkazib berish turini tanlang",
                                 reply_markup=stage_order_delivery_kb(lang))


@sync_to_async
def get_product(product_id):
    return Product.objects.get(id=product_id)


def get_image(filename):
    try:
        current_path = os.path.abspath(os.getcwd())
        image_path = os.path.join(current_path, 'media', filename)

        with open(image_path, 'rb') as photo:
            return photo.read()

    except Exception as e:
        print(Exception, e)


async def product_menu(message, product_id):
    user_id = message.from_user.id
    product = await get_product(product_id)
    lang = await get_lang(user_id)
    price = float(product.price)
    formatted_price = "{:,.0f} сум".format(price).replace(",", " ")
    current_path = os.path.abspath(os.getcwd())
    decoded_file_name = unquote(product.product_image.url)
    if lang == "ru":
        await message.answer_photo(
            photo=FSInputFile(current_path + decoded_file_name),
            caption=f"<b>{product.product_name}</b>\n\n"
                    f"{formatted_price}\n\n{product.description_ru}",
            parse_mode="HTML", reply_markup=product_menu_kb(lang=lang))
    else:
        await message.answer_photo(
            photo=FSInputFile(current_path + decoded_file_name),
            caption=f"<b>{product.product_name}</b>\n\n"
                    f"{formatted_price}\n\n{product.description_uz}",
            parse_mode="HTML", reply_markup=product_menu_kb(lang=lang))


@main_router.message(StageOfOrderState.choose_product)
async def product_dec_menu(message: Message, state: FSMContext):
    user_id = message.from_user.id
    lang = await get_lang(user_id)
    if message.text in [ru['inline_keyboard_button']['back'], uz['inline_keyboard_button']['back']]:
        await state.set_state(StageOfOrderState.start_order)
        await message.answer(
            f"""{"Закажите через новое удобное меню" if lang == "ru" else "Buyurtmani qabul qilish uchun qulay menyu"} 👇😉""",
            reply_markup=wb_button(lang))
        await message.answer(ru['choose_product_menu'] if lang == 'ru' else uz['choose_product_menu'],
                             parse_mode="HTML",
                             reply_markup=category_product_menu(lang))

    all_product = await get_all_product()
    print(all_product)
    product_list = [product.product_name for product in all_product]
    if message.text in product_list:
        product_id = all_product[product_list.index(message.text)].id
        await state.set_data({"user": {user_id: {'product_id': product_id, 'pr_count': 1}}})
        await state.set_state(StageOfOrderState.get_product)
        print(all_product[product_list.index(message.text)].id)
        print(message.text)
        await message.answer("Выберите количество продукции" if lang == "ru" else "Mahsulot miqdorini tanlang",
                             reply_markup=product_edit_menu(lang))
        await product_menu(message, product_id)


@main_router.message(StageOfOrderState.get_product)
async def gain(message: Message, state: FSMContext):
    user_id = message.from_user.id
    lang = await get_lang(user_id)
    all_product = await get_all_product()
    product_list = [product.product_name for product in all_product]
    if message.text in [ru['inline_keyboard_button']['back'], uz['inline_keyboard_button']['back']]:
        await state.set_state(StageOfOrderState.choose_product)
        await message.answer(
            f"""{"Закажите через новое удобное меню" if lang == "ru" else "Buyurtmani qabul qilish uchun qulay menyu"} 👇😉""",
            reply_markup=wb_button(lang))
        await message.answer(ru['choose_product_menu'] if lang == 'ru' else uz['choose_product_menu'],
                             parse_mode="HTML",
                             reply_markup=product_kb(lang, all_product))
    elif message.text in ["\uD83D\uDCB3 Корзина", "\uD83D\uDCB3 Savatim"]:
        pass


@main_router.message(Command("feedback"))
@main_router.message(
    F.text.in_([ru['inline_keyboard_button']['leave_feedback'], uz['inline_keyboard_button']['leave_feedback']]))
async def about_us(message: Message, state: FSMContext):
    await state.clear()
    user_id = message.from_user.id
    lang = await get_lang(user_id)
    await state.set_state(LeaveFeedback.get_feedback)
    await message.answer(
        "Оставьте свой отзыв. Нам важно ваше мнение." if lang == 'ru' else "Sharhingizni qoldiring. Sizning fikringiz biz uchun muhim.",
        reply_markup=leave_feedback_kb(lang))


@main_router.message(LeaveFeedback.get_feedback)
async def about_us(message: Message, state: FSMContext):
    user_id = message.from_user.id
    lang = await get_lang(user_id)
    user_info = await get_user_info(user_id)
    if message.text in [ru['inline_keyboard_button']['back'], uz['inline_keyboard_button']['back']]:
        await menu(lang=lang, message=message)
        await state.clear()
    else:
        await message.bot.send_message(ADMIN_ID, user_info.phone_number + "\n" + message.text)
        await message.answer("Спасибо за ваш отзыв", reply_markup=menu_kb(lang))
        await state.clear()
        await menu(lang=lang, message=message)


@main_router.message(F.text.in_([ru['inline_keyboard_button']['promotion'], uz['inline_keyboard_button']['promotion']]))
async def about_us(message: Message, state: FSMContext):
    user_id = message.from_user.id
    lang = await get_lang(user_id)
    await message.answer(ru['promotions'] if lang == "ru" else uz['promotion'],
                         reply_markup=menu_kb(lang))
    await state.set_state(PromotionState.get_promotion)


@sync_to_async
def get_user_orders(user_id):
    user_orders = MyOrders.objects.filter(user_id=user_id).all()
    return list(user_orders) if user_orders else None


@main_router.message(F.text.in_([ru['inline_keyboard_button']['my_orders'], uz['inline_keyboard_button']['my_orders']]))
async def about_us(message: Message, state: FSMContext):
    user_id = message.from_user.id
    lang = await get_lang(user_id)
    user_orders = await get_user_orders(user_id)
    if user_orders:
        await message.answer("Ваши заказы", reply_markup=menu_kb(lang))
        for i in user_orders:
            await message.answer(i.order_text, reply_markup=menu_kb(lang))
    else:
        await message.answer("У вас нет заказов" if lang == "ru" else "Sizda buyurtmalar yo'q",
                             reply_markup=menu_kb(lang))


@main_router.message(PromotionState.get_promotion)
async def about_us(message: Message, state: FSMContext):
    user_id = message.from_user.id
    lang = await get_lang(user_id)
    if message.text in [ru['inline_keyboard_button']['back'], uz['inline_keyboard_button']['back']]:
        await state.clear()
        await message.delete()
        await menu(lang=lang, message=message)


@sync_to_async
def get_birthday(user_id):
    user = UserTG.objects.get(user_tg_id=user_id)
    if user.birthday:
        return [user.birthday, user.phone_number]
    elif user.phone_number:
        return [None, user.phone_number]
    else:
        return None


async def settings_menu(message, state: FSMContext):
    user_id = message.from_user.id
    lang = await get_lang(user_id)
    user_info = await get_birthday(user_id)
    birthday = user_info[0] if user_info else None
    await message.answer("Выберите настройку" if lang == "ru" else "Sozlamani tanlang",
                         reply_markup=settings_kb(lang, birthday))
    await state.set_state(SettingsState.get_settings)


@main_router.message(F.text.in_([ru['inline_keyboard_button']['settings'], uz['inline_keyboard_button']['settings']]))
async def root(message: Message, state: FSMContext):
    user_id = message.from_user.id
    lang = await get_lang(user_id)
    await settings_menu(message, state)


@main_router.message(SettingsState.get_settings)
async def root(message: Message, state: FSMContext):
    user_id = message.from_user.id
    lang = await get_lang(user_id)
    user_info = await get_birthday(user_id)
    print(user_info)
    birthday = user_info[0] if user_info else None
    phone_number = user_info[1] if user_info else None
    if message.text in [ru['inline_keyboard_button']['back'], uz['inline_keyboard_button']['back']]:
        await state.clear()
        await message.delete()
        await menu(lang=lang, message=message)
    elif message.text in ["Добавить день рождение", "Tug'ilgan kunini qo'shish"]:
        await message.answer(
            "Введите свой день рождения в формате, похожем на «01-12-2000»" if lang == 'ru' else "Tug'ilgan kunni «01-12-2000» shu formatda kiriting",
            reply_markup=birthday_kb(lang))
        await state.set_state(SettingsState.get_birthday)
    elif message.text in ["Изменить день рождения", "Tug'ilgan kunini o'zgartirish"]:
        await message.answer(
            "Ваша дата рождения:" + birthday + "\n\nНапишите новую дату рождения в формате, похожем на «01-12-2000»" if lang == 'ru' else
            "Sizning tug'ilgan kuni: " + birthday + "\n\nYangi tug'ilgan kunni «01-12-2000» shu formatda kiriting",
            reply_markup=birthday_kb(lang))
        await state.set_state(SettingsState.get_birthday)
    elif message.text in ["Изменить номер телефона", "Telefon raqamini o'zgartirish"]:
        await message.answer("Ваш номер телефона: " + str(
            phone_number) + "\n\nНапишите свой новый номер" if lang == 'ru' else "Sizning telefon raqamingiz: " + str(
            phone_number) + "\n\nTelefon raqamini yozing", reply_markup=phone_number_kb(lang))
        await state.set_state(SettingsState.get_phone)
    elif message.text in ["🇷🇺Поменять на русский", "🇺🇿Ozbekchaga o'zgartirish"]:
        await message.delete()
        if message.text == "🇷🇺Поменять на русский":
            result = await update_lang(user_id, 'ru')
        elif message.text == "🇺🇿Ozbekchaga o'zgartirish":
            result = await update_lang(user_id, 'uz')
        await settings_menu(message, state)


@main_router.message(SettingsState.get_birthday)
async def root(message: Message, state: FSMContext):
    user_id = message.from_user.id
    lang = await get_lang(user_id)
    if message.text in [ru['inline_keyboard_button']['back'], uz['inline_keyboard_button']['back']]:
        await state.clear()
        await message.delete()
        await settings_menu(message, state)
        return
    birthday = message.text
    try:
        # Проверка формата даты
        datetime.strptime(birthday, '%d-%m-%Y')

        # Сохраните день рождения в базу данных
        result = await update_birthday(user_id, birthday)
        response = "Ваш день рождения успешно сохранен!" if lang == 'ru' else "Tug'ilgan kuningiz muvaffaqiyatli saqlandi!"
        await message.answer(response)
        await state.clear()
        await settings_menu(message, state)
    except ValueError:
        response = "Неверный формат даты. Попробуйте еще раз." if lang == 'ru' else "Noto'g'ri sana formati. Iltimos, qayta urinib ko'ring."
        await message.answer(response, reply_markup=birthday_kb(lang))


@main_router.message(SettingsState.get_phone)
async def root(message: Message, state: FSMContext):
    user_id = message.from_user.id
    lang = await get_lang(user_id)
    if message.text in [ru['inline_keyboard_button']['back'], uz['inline_keyboard_button']['back']]:
        await state.clear()
        await message.delete()
        await settings_menu(message, state)
    if message.contact:
        phone = message.contact.phone_number
        result = await update_phone(user_id, phone)
        await message.answer("Ваш номер телефона: " + phone if lang == 'ru' else "Sizning telefon raqamingiz: " + phone)
        await settings_menu(message, state)


@main_router.message(
    F.text.in_([ru['inline_keyboard_button']['about_delivery'], uz['inline_keyboard_button']['about_delivery']]))
async def back(message: Message, state: FSMContext):
    user_id = message.from_user.id
    lang = await get_lang(user_id)
    await message.answer(ru['delivery_menu'] if lang == "ru" else uz['delivery_menu'])
