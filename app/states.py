from aiogram.fsm.state import StatesGroup, State

class RegFlow(StatesGroup):
    venue = State()
    position = State()
    name = State()

class OSFlow(StatesGroup):
    table = State()
    category = State()
    comment = State()