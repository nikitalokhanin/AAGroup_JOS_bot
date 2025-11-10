from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder


def main_menu(is_admin: bool = False) -> ReplyKeyboardMarkup:
    buttons = [[KeyboardButton(text="Оставить обратную связь")]]
    if is_admin:
        buttons.append([KeyboardButton(text="Админ-панель")])
    buttons.append([KeyboardButton(text="Отмена")])
    return ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)


def inline_list(options: list[str], prefix: str):
    kb = InlineKeyboardBuilder()
    for i, opt in enumerate(options):
        kb.button(text=opt, callback_data=f"{prefix}:{i}")
    kb.adjust(2)
    return kb.as_markup()