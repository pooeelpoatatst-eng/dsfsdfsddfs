from aiogram.fsm.state import State, StatesGroup


class LoginState(StatesGroup):
    qr = State()
    phone = State()
    code = State()
    password = State()
