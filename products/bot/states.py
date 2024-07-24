from aiogram.fsm.state import State, StatesGroup


class RegistrationState(StatesGroup):
    get_name = State()
    get_phone = State()


class StageOfOrderState(StatesGroup):
    get_delivery = State()
    get_location = State()
    get_time = State()
    location_address = State()
    start_order = State()
    choose_product = State()
    get_product = State()
    user_cart = State()
    user_payment = State()


class TimeState(StatesGroup):
    choose_time = State()


class PromocodeState(StatesGroup):
    get_promocode = State()


class LeaveFeedback(StatesGroup):
    get_feedback = State()


class PromotionState(StatesGroup):
    get_promotion = State()


class SettingsState(StatesGroup):
    get_settings = State()
    get_birthday = State()
    get_phone = State()

class MailingState(StatesGroup):
    mailing = State()
