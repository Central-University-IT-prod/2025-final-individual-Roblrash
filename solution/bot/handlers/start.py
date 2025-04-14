from aiogram import types, Router
from aiogram.filters import Command
from utils.keyboards import main_menu_keyboard

router = Router()

@router.message(Command("start"))
async def start_command(message: types.Message) -> None:
    await message.answer(
        "Добро пожаловать! Выберите раздел:",
        reply_markup=main_menu_keyboard()
    )
@router.callback_query(lambda c: c.data == "back_main")
async def back_main_handler(callback: types.CallbackQuery) -> None:
    try:
        if callback.message.text:
            await callback.message.edit_text("Главное меню", reply_markup=main_menu_keyboard())
        elif callback.message.caption:
            await callback.message.edit_caption("Главное меню", reply_markup=main_menu_keyboard())
        else:
            await callback.message.answer("Главное меню", reply_markup=main_menu_keyboard())
    except Exception as e:
        await callback.message.answer("Ошибка при возврате в главное меню", reply_markup=main_menu_keyboard())
    await callback.answer()
