from aiogram.fsm.state import State, StatesGroup


class LoginState(StatesGroup):
    phone = State()
    code = State()
    password = State()
