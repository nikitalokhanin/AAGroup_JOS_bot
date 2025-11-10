from aiogram import Router, F
from aiogram.types import Message
from app.texts import NO_ACCESS

admin_router = Router()

async def is_admin(message: Message, admin_ids: list[int]) -> bool:
    return message.from_user and message.from_user.id in admin_ids

@admin_router.message(F.text == "Админ-панель")
async def admin_panel(message: Message):
  await message.answer(
    "Админ-панель (заготовка):\n"
    "- Пользователи (в будущих версиях)\n"
    "- Категории / Заведения — правятся через CSV (categories.csv / venues.csv)\n"
    "- /export — скачать feedback.csv"
)