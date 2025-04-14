import io
import httpx
from aiogram import types, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import BufferedInputFile
from utils.api_client import api_post, api_delete, api_get, api_put_image
from utils.keyboards import images_menu_keyboard, cancel_keyboard
from utils.states import (
    ImageUploadStates,
    ImageUpdateStates,
    ImageDeleteStates,
    ImageGetStates
)

router = Router()

@router.callback_query(lambda c: c.data == "menu_images")
async def images_menu(callback: types.CallbackQuery) -> None:
    await callback.message.edit_text(
        "Изображения – выберите действие:",
        reply_markup=images_menu_keyboard()
    )
    try:
        await callback.answer()
    except Exception:
        pass

@router.callback_query(lambda c: c.data == "image_upload")
async def image_upload_start(callback: types.CallbackQuery, state: FSMContext) -> None:
    await callback.message.edit_text(
        "Введите ID рекламного объявления для загрузки изображения:",
        reply_markup=cancel_keyboard()
    )
    await state.set_state(ImageUploadStates.waiting_for_ad_id)
    try:
        await callback.answer()
    except Exception:
        pass

@router.message(ImageUploadStates.waiting_for_ad_id)
async def process_image_upload_ad_id(message: types.Message, state: FSMContext) -> None:
    ad_id = message.text.strip()
    await state.update_data(ad_id=ad_id)
    await message.answer(
        "Отправьте изображение (фотографией):",
        reply_markup=cancel_keyboard()
    )
    await state.set_state(ImageUploadStates.waiting_for_image)

@router.message(ImageUploadStates.waiting_for_image, lambda message: message.content_type == "photo")
async def process_image_upload_photo(message: types.Message, state: FSMContext) -> None:
    data = await state.get_data()
    ad_id = data["ad_id"]
    photo = message.photo[-1]
    file_info = await message.bot.get_file(photo.file_id)
    file_path = file_info.file_path
    file_url = f"https://api.telegram.org/file/bot{message.bot.token}/{file_path}"
    async with httpx.AsyncClient() as client:
        resp = await client.get(file_url)
        image_bytes = resp.content
    files = {"file": ("image.jpg", image_bytes, "image/jpeg")}
    endpoint = f"/ads/{ad_id}/upload-image"
    response = await api_post(endpoint, files=files)
    if response.status_code == 200:
        result = response.json()
        await message.answer(
            f"Изображение загружено:\nURL: {result.get('image_url')}",
            reply_markup=cancel_keyboard()
        )
    else:
        await message.answer(
            f"Ошибка загрузки изображения: {response.text}",
            reply_markup=cancel_keyboard()
        )
    await state.clear()

@router.callback_query(lambda c: c.data == "image_update")
async def image_update_start(callback: types.CallbackQuery, state: FSMContext) -> None:
    await callback.message.edit_text(
        "Введите ID рекламного объявления для обновления изображения:",
        reply_markup=cancel_keyboard()
    )
    await state.set_state(ImageUpdateStates.waiting_for_ad_id)
    try:
        await callback.answer()
    except Exception:
        pass

@router.message(ImageUpdateStates.waiting_for_ad_id)
async def process_image_update_ad_id(message: types.Message, state: FSMContext) -> None:
    ad_id = message.text.strip()
    await state.update_data(ad_id=ad_id)
    await message.answer(
        "Отправьте новое изображение (фотографией):",
        reply_markup=cancel_keyboard()
    )
    await state.set_state(ImageUpdateStates.waiting_for_image)

@router.message(ImageUpdateStates.waiting_for_image, lambda message: message.content_type == "photo")
async def process_image_update_photo(message: types.Message, state: FSMContext) -> None:
    data = await state.get_data()
    ad_id = data["ad_id"]
    photo = message.photo[-1]
    file_info = await message.bot.get_file(photo.file_id)
    file_path = file_info.file_path
    file_url = f"https://api.telegram.org/file/bot{message.bot.token}/{file_path}"
    async with httpx.AsyncClient() as client:
        resp = await client.get(file_url)
        image_bytes = resp.content
    files = {"file": ("image.jpg", image_bytes, "image/jpeg")}
    endpoint = f"/ads/{ad_id}/update-image"
    response = await api_put_image(endpoint, files=files)
    if response.status_code == 200:
        result = response.json()
        await message.answer(
            f"Изображение обновлено:\nURL: {result.get('image_url')}",
            reply_markup=cancel_keyboard()
        )
    else:
        await message.answer(
            f"Ошибка обновления изображения: {response.text}",
            reply_markup=cancel_keyboard()
        )
    await state.clear()


@router.callback_query(lambda c: c.data == "image_delete")
async def image_delete_start(callback: types.CallbackQuery, state: FSMContext) -> None:
    await callback.message.edit_text(
        "Введите ID рекламного объявления для удаления изображения:",
        reply_markup=cancel_keyboard()
    )
    await state.set_state(ImageDeleteStates.waiting_for_ad_id)
    try:
        await callback.answer()
    except Exception:
        pass

@router.message(ImageDeleteStates.waiting_for_ad_id)
async def process_image_delete(message: types.Message, state: FSMContext) -> None:
    ad_id = message.text.strip()
    endpoint = f"/ads/{ad_id}/delete-image"
    response = await api_delete(endpoint)
    if response.status_code == 200:
        await message.answer(
            "Изображение успешно удалено!",
            reply_markup=cancel_keyboard()
        )
    else:
        await message.answer(
            f"Ошибка удаления изображения: {response.text}",
            reply_markup=cancel_keyboard()
        )
    await state.clear()

@router.callback_query(lambda c: c.data == "image_get")
async def image_get_start(callback: types.CallbackQuery, state: FSMContext) -> None:
    await callback.message.edit_text(
        "Введите ID рекламного объявления для получения изображения:",
        reply_markup=cancel_keyboard()
    )
    await state.set_state(ImageGetStates.waiting_for_ad_id)
    try:
        await callback.answer()
    except Exception:
        pass

@router.message(ImageGetStates.waiting_for_ad_id)
async def process_image_get(message: types.Message, state: FSMContext) -> None:
    ad_id = message.text.strip()
    endpoint = f"/ads/{ad_id}/image"
    response = await api_get(endpoint)
    if response.status_code == 200:
        image_bytes = response.content
        buffer = io.BytesIO(image_bytes)
        buffer.seek(0)
        file = BufferedInputFile(buffer.getvalue(), filename="image.jpg")
        await message.answer_photo(
            photo=file,
            reply_markup=cancel_keyboard()
        )
    else:
        await message.answer(
            f"Ошибка получения изображения: {response.text}",
            reply_markup=cancel_keyboard()
        )
    await state.clear()

