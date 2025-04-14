from aiogram import types, Router
from aiogram.fsm.context import FSMContext
from utils.api_client import api_post
from utils.states import AiTextStates
from utils.keyboards import cancel_keyboard

router = Router()

@router.callback_query(lambda c: c.data == "menu_ai_text")
async def ai_text_start(callback: types.CallbackQuery, state: FSMContext) -> None:
    await callback.message.edit_text(
        "Введите заголовок объявления:",
        reply_markup=cancel_keyboard()
    )
    await state.set_state(AiTextStates.waiting_for_ad_title)
    await callback.answer()

@router.message(AiTextStates.waiting_for_ad_title)
async def process_ad_title(message: types.Message, state: FSMContext) -> None:
    await state.update_data(ad_title=message.text.strip())
    await message.answer(
        "Введите название рекламодателя:",
        reply_markup=cancel_keyboard()
    )
    await state.set_state(AiTextStates.waiting_for_advertiser_name)

@router.message(AiTextStates.waiting_for_advertiser_name)
async def process_advertiser_name(message: types.Message, state: FSMContext) -> None:
    await state.update_data(advertiser_name=message.text.strip())
    data = await state.get_data()
    payload = {
        "ad_title": data["ad_title"],
        "advertiser_name": data["advertiser_name"]
    }
    endpoint = "/generate_ad_text"
    response = await api_post(endpoint, json_data=payload)
    if response.status_code == 200:
        result = response.json()
        await message.answer(
            f"Сгенерированный рекламный текст:\n{result.get('ad_text')}",
            reply_markup=cancel_keyboard()
        )
    else:
        await message.answer(
            f"Ошибка генерации рекламного текста: {response.text}",
            reply_markup=cancel_keyboard()
        )
    await state.clear()
