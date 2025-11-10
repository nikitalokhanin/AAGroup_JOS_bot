import asyncio
import logging
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, CallbackQuery, FSInputFile
from aiogram.fsm.context import FSMContext
from aiogram.filters import Command

from app.config import settings
from app.texts import *
from app.states import RegFlow, OSFlow
from app.keyboards import main_menu, inline_list
from app.storage.csv_store import CSVStore
from app.admin.handlers import admin_router, is_admin

# ----------------------------------------------------------
# Инициализация
# ----------------------------------------------------------

logging.basicConfig(level=logging.INFO)

bot = Bot(settings.bot_token)
dp = Dispatcher()
store = CSVStore(settings.data_dir)

INITIAL_POSITIONS = ["официант", "хостес", "менеджер"]

# ----------------------------------------------------------
# /start
# ----------------------------------------------------------

@dp.message(Command("start"))
async def start(message: Message, state: FSMContext):
    user = store.get_user(message.from_user.id)
    if user:
        admin = message.from_user.id in settings.admin_ids
        await message.answer(WELCOME_BACK, reply_markup=main_menu(is_admin=admin))
    else:
        venues = store.list_venues() or ["Заведение 1", "Заведение 2"]
        await state.set_state(RegFlow.venue)
        await message.answer(ASK_VENUE, reply_markup=inline_list(venues, prefix="venue"))

# ----------------------------------------------------------
# Выбор заведения
# ----------------------------------------------------------

@dp.callback_query(F.data.startswith("venue:"))
async def pick_venue(cb: CallbackQuery, state: FSMContext):
    try:
        venues = store.list_venues() or ["Заведение 1", "Заведение 2"]
        idx = int(cb.data.split(":")[1])
        if idx < 0 or idx >= len(venues):
            await cb.answer("Неверный выбор", show_alert=False)
            return

        await state.update_data(venue=venues[idx])
        await state.set_state(RegFlow.position)
        await cb.message.answer(ASK_POSITION, reply_markup=inline_list(INITIAL_POSITIONS, prefix="pos"))
        await cb.answer()
    except Exception as e:
        print("ERROR in pick_venue:", e)
        await cb.answer("Ошибка. Попробуй ещё раз.", show_alert=False)

# ----------------------------------------------------------
# Выбор должности
# ----------------------------------------------------------

@dp.callback_query(F.data.startswith("pos:"))
async def pick_pos(cb: CallbackQuery, state: FSMContext):
    idx = int(cb.data.split(":")[1])
    if idx < 0 or idx >= len(INITIAL_POSITIONS):
        await cb.answer("Неверный выбор")
        return
    await state.update_data(position=INITIAL_POSITIONS[idx])
    await state.set_state(RegFlow.name)
    await cb.message.answer(ASK_NAME)
    await cb.answer()

# ----------------------------------------------------------
# Ввод имени
# ----------------------------------------------------------

@dp.message(RegFlow.name)
async def set_name(message: Message, state: FSMContext):
    name = (message.text or "").strip()
    if not name:
        await message.answer("Пожалуйста, введи имя текстом")
        return
    data = await state.get_data()
    store.upsert_user(
        telegram_id=message.from_user.id,
        username=message.from_user.username or "",
        full_name=name,
        role="employee",
        venue=data.get("venue"),
        position=data.get("position"),
    )
    await state.clear()
    admin = message.from_user.id in settings.admin_ids
    await message.answer(REG_DONE, reply_markup=main_menu(is_admin=admin))

# ----------------------------------------------------------
# /help
# ----------------------------------------------------------

@dp.message(Command("help"))
async def help_cmd(message: Message):
    await message.answer(HELP)

# ----------------------------------------------------------
# Оставить обратную связь
# ----------------------------------------------------------

@dp.message(Command("os"))
@dp.message(F.text == BTN_LEAVE_FEEDBACK)
async def os_start(message: Message, state: FSMContext):
    user = store.get_user(message.from_user.id)
    if not user:
        await message.answer(NOT_REGISTERED)
        return
    await state.set_state(OSFlow.table)
    await message.answer(ASK_TABLE)

@dp.message(OSFlow.table)
async def os_table(message: Message, state: FSMContext):
    try:
        table = int(message.text.strip())
        if table <= 0 or table > 500:
            raise ValueError
    except Exception:
        await message.answer(ERR_INT)
        return

    await state.update_data(table=table)
    cats = store.list_categories()
    await state.set_state(OSFlow.category)

    # 1. Спрашиваем категорию
    await message.answer(ASK_CATEGORY, reply_markup=inline_list(cats, prefix="cat"))

    # 2. Отправляем одну и ту же подсказку-картинку
    try:
        await message.answer_photo(
            FSInputFile("assets/tips.jpg"),
            caption="Подсказка по категориям 👆"
        )
    except Exception as e:
        print("Не удалось отправить подсказку-картинку:", e)

@dp.callback_query(F.data.startswith("cat:"))
async def os_category(cb: CallbackQuery, state: FSMContext):
    cats = store.list_categories()
    idx = int(cb.data.split(":")[1])
    if idx < 0 or idx >= len(cats):
        await cb.answer("Неверный выбор")
        return
    await state.update_data(category=cats[idx])
    await state.set_state(OSFlow.comment)
    await cb.message.answer(ASK_COMMENT)
    await cb.answer()

@dp.message(OSFlow.comment)
async def os_comment(message: Message, state: FSMContext):
    comment = (message.text or "").strip()
    user = store.get_user(message.from_user.id)
    if not user:
        await message.answer(NOT_REGISTERED)
        await state.clear()
        return
    data = await state.get_data()
    store.add_feedback(
        telegram_id=message.from_user.id,
        venue=user.get("venue"),
        position=user.get("position"),
        employee_name=user.get("full_name"),
        table_number=data.get("table"),
        category=data.get("category"),
        comment=comment,
    )
    await state.clear()
    admin = message.from_user.id in settings.admin_ids
    await message.answer(SAVED, reply_markup=main_menu(is_admin=admin))

# ----------------------------------------------------------
# Экспорт CSV для админа
# ----------------------------------------------------------

@dp.message(Command("export"))
async def export_cmd(message: Message):
    if not await is_admin(message, settings.admin_ids):
        await message.answer(NO_ACCESS)
        return
    await message.answer(EXPORT_READY)
    path = store.feedback_csv_path()
    await message.answer_document(FSInputFile(path, filename="feedback.csv"))

# ----------------------------------------------------------
# Отмена
# ----------------------------------------------------------

@dp.message(F.text == BTN_CANCEL)
async def cancel_any(message: Message, state: FSMContext):
    await state.clear()
    admin = message.from_user.id in settings.admin_ids
    await message.answer(CANCELLED, reply_markup=main_menu(is_admin=admin))

# ----------------------------------------------------------
# Страховочный callback
# ----------------------------------------------------------

@dp.callback_query()
async def fallback_cb(cb: CallbackQuery):
    print("UNHANDLED CALLBACK:", cb.data)
    await cb.answer()

# ----------------------------------------------------------
# Entry point
# ----------------------------------------------------------

async def main():
    if not settings.bot_token:
        raise RuntimeError("BOT_TOKEN не задан в .env")
    dp.include_router(admin_router)
    print("Starting polling...")
    try:
        await dp.start_polling(bot)
    except Exception as e:
        import traceback
        print("Polling crashed with error:", e)
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())