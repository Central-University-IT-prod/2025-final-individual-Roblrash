from aiogram import types, Router
from utils.api_client import api_post
from utils.keyboards import moderation_menu_keyboard, cancel_keyboard

router = Router()

@router.callback_query(lambda c: c.data == "menu_moderation")
async def moderation_menu(callback: types.CallbackQuery) -> None:
    await callback.message.edit_text(
        "Модерация – выберите действие:",
        reply_markup=moderation_menu_keyboard()
    )
    await callback.answer()

@router.callback_query(lambda c: c.data in ["moderation_on", "moderation_off"])
async def toggle_moderation(callback: types.CallbackQuery) -> None:
    enabled = callback.data == "moderation_on"
    endpoint = "/moderation/toggle"
    payload = {"enabled": enabled}
    response = await api_post(endpoint, json_data=payload)
    if response.status_code == 200:
        state_text = "включена" if enabled else "выключена"
        await callback.message.answer(
            f"Модерация успешно {state_text}.",
            reply_markup=cancel_keyboard()
        )
    else:
        await callback.message.answer(
            f"Ошибка переключения модерации: {response.text}",
            reply_markup=cancel_keyboard()
        )
    await callback.answer()
