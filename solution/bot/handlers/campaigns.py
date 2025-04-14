from uuid import UUID
from aiogram import types, Router
from aiogram.fsm.context import FSMContext
from utils.api_client import api_get, api_post, api_put, api_delete
from utils.keyboards import campaigns_menu_keyboard, cancel_keyboard, skip_keyboard
from utils.states import (
    CampaignStates,
    GetCampaignStates,
    DeleteCampaignStates,
    UpdateCampaignStates,
    ImageGetALLStates
)
from schemas.campaign import CampaignCreate, CampaignUpdate


def validate_uuid(id_str: str) -> bool:
    try:
        UUID(id_str)
        return True
    except Exception:
        return False


def format_campaign_data(campaign: dict) -> str:
    return "\n".join(f"{key}: {value}" for key, value in campaign.items())


def safe_int(text: str, field_name: str) -> int:
    try:
        value = int(text)
        if value < 0:
            raise ValueError
        return value
    except ValueError:
        raise ValueError(f"Введите корректное неотрицательное число для {field_name}.")


def safe_positive_int(text: str, field_name: str) -> int:
    try:
        value = int(text)
        if value <= 0:
            raise ValueError
        return value
    except ValueError:
        raise ValueError(f"Введите корректное число (больше 0) для {field_name}.")


def safe_positive_float(text: str, field_name: str) -> float:
    try:
        value = float(text)
        if value <= 0:
            raise ValueError
        return value
    except ValueError:
        raise ValueError(f"Введите корректное число (больше 0) для {field_name}.")


router = Router()


@router.callback_query(lambda c: c.data == "menu_campaigns")
async def campaigns_menu_handler(callback: types.CallbackQuery) -> None:
    await callback.message.edit_text(
        "Кампании – выберите действие:",
        reply_markup=campaigns_menu_keyboard()
    )
    await callback.answer()


# -------------- Создание кампании (CampaignCreate) --------------

@router.callback_query(lambda c: c.data == "campaign_create")
async def create_campaign_start(callback: types.CallbackQuery, state: FSMContext) -> None:
    await callback.message.edit_text(
        "Создание кампании.\nВведите ID рекламодателя:",
        reply_markup=cancel_keyboard()
    )
    await state.set_state(CampaignStates.waiting_for_advertiser_id)
    await callback.answer()


@router.message(CampaignStates.waiting_for_advertiser_id)
async def process_advertiser_id(message: types.Message, state: FSMContext) -> None:
    advertiser_id = message.text.strip()
    if not advertiser_id:
        await message.answer("Ошибка: ID рекламодателя обязателен. Введите его.", reply_markup=cancel_keyboard())
        return
    if not validate_uuid(advertiser_id):
        await message.answer("Ошибка: неверный формат ID рекламодателя. Ожидается UUID.", reply_markup=cancel_keyboard())
        return
    await state.update_data(advertiser_id=advertiser_id)
    await message.answer("Введите заголовок объявления (не менее 1 символа):", reply_markup=cancel_keyboard())
    await state.set_state(CampaignStates.waiting_for_ad_title)


@router.message(CampaignStates.waiting_for_ad_title)
async def process_ad_title(message: types.Message, state: FSMContext) -> None:
    ad_title = message.text.strip()
    if not ad_title:
        await message.answer("Ошибка: заголовок обязателен. Введите его.", reply_markup=cancel_keyboard())
        return
    await state.update_data(ad_title=ad_title)
    await message.answer("Введите текст рекламного объявления:", reply_markup=cancel_keyboard())
    await state.set_state(CampaignStates.waiting_for_ad_text)


@router.message(CampaignStates.waiting_for_ad_text)
async def process_ad_text(message: types.Message, state: FSMContext) -> None:
    ad_text = message.text.strip()
    if not ad_text:
        await message.answer("Ошибка: текст объявления обязателен. Введите его.", reply_markup=cancel_keyboard())
        return
    await state.update_data(ad_text=ad_text)
    await message.answer("Введите день начала кампании (целое число):", reply_markup=cancel_keyboard())
    await state.set_state(CampaignStates.waiting_for_start_date)


@router.message(CampaignStates.waiting_for_start_date)
async def process_start_date(message: types.Message, state: FSMContext) -> None:
    try:
        start_date = safe_int(message.text.strip(), "дня начала кампании")
    except ValueError as e:
        await message.answer(str(e), reply_markup=cancel_keyboard())
        return
    await state.update_data(start_date=start_date)
    await message.answer("Введите день окончания кампании (целое число):", reply_markup=cancel_keyboard())
    await state.set_state(CampaignStates.waiting_for_end_date)


@router.message(CampaignStates.waiting_for_end_date)
async def process_end_date(message: types.Message, state: FSMContext) -> None:
    try:
        end_date = safe_int(message.text.strip(), "дня окончания кампании")
    except ValueError as e:
        await message.answer(str(e), reply_markup=cancel_keyboard())
        return
    data = await state.get_data()
    if "start_date" in data and end_date < data["start_date"]:
        await message.answer("Ошибка: день окончания не может быть меньше дня начала. Повторите ввод.", reply_markup=cancel_keyboard())
        return
    await state.update_data(end_date=end_date)
    await message.answer("Введите лимит показов (целое число > 0):", reply_markup=cancel_keyboard())
    await state.set_state(CampaignStates.waiting_for_impressions_limit)


@router.message(CampaignStates.waiting_for_impressions_limit)
async def process_impressions_limit(message: types.Message, state: FSMContext) -> None:
    try:
        impressions_limit = safe_positive_int(message.text.strip(), "лимита показов")
    except ValueError as e:
        await message.answer(str(e), reply_markup=cancel_keyboard())
        return
    await state.update_data(impressions_limit=impressions_limit)
    await message.answer("Введите лимит кликов (целое число > 0):", reply_markup=cancel_keyboard())
    await state.set_state(CampaignStates.waiting_for_clicks_limit)


@router.message(CampaignStates.waiting_for_clicks_limit)
async def process_clicks_limit(message: types.Message, state: FSMContext) -> None:
    try:
        clicks_limit = safe_positive_int(message.text.strip(), "лимита кликов")
    except ValueError as e:
        await message.answer(str(e), reply_markup=cancel_keyboard())
        return
    data = await state.get_data()
    if "impressions_limit" in data and clicks_limit > data["impressions_limit"]:
        await message.answer("Ошибка: лимит кликов не может превышать лимит показов. Повторите ввод.", reply_markup=cancel_keyboard())
        return
    await state.update_data(clicks_limit=clicks_limit)
    await message.answer("Введите стоимость за показ (число с плавающей точкой > 0):", reply_markup=cancel_keyboard())
    await state.set_state(CampaignStates.waiting_for_cost_per_impression)


@router.message(CampaignStates.waiting_for_cost_per_impression)
async def process_cost_per_impression(message: types.Message, state: FSMContext) -> None:
    try:
        cost_per_impression = safe_positive_float(message.text.strip(), "стоимости за показ")
    except ValueError as e:
        await message.answer(str(e), reply_markup=cancel_keyboard())
        return
    await state.update_data(cost_per_impression=cost_per_impression)
    await message.answer("Введите стоимость за клик (число с плавающей точкой > 0):", reply_markup=cancel_keyboard())
    await state.set_state(CampaignStates.waiting_for_cost_per_click)


@router.message(CampaignStates.waiting_for_cost_per_click)
async def process_cost_per_click(message: types.Message, state: FSMContext) -> None:
    try:
        cost_per_click = safe_positive_float(message.text.strip(), "стоимости за клик")
    except ValueError as e:
        await message.answer(str(e), reply_markup=cancel_keyboard())
        return
    await state.update_data(cost_per_click=cost_per_click)
    await message.answer(
        "Введите пол для таргетинга (MALE, FEMALE или ALL; можно оставить пустым):",
        reply_markup=skip_keyboard("target_gender")
    )
    await state.set_state(CampaignStates.waiting_for_target_gender)


@router.message(CampaignStates.waiting_for_target_gender)
async def process_target_gender(message: types.Message, state: FSMContext) -> None:
    text = message.text.strip()
    if text.isdigit():
        await message.answer("Ошибка: вместо пола введено число. Если хотите пропустить, нажмите «Пропустить».", reply_markup=skip_keyboard("target_gender"))
        return
    if text and text not in ("MALE", "FEMALE", "ALL"):
        await message.answer("Ошибка: пол должен быть введён как MALE, FEMALE или ALL. Повторите ввод или нажмите «Пропустить».", reply_markup=skip_keyboard("target_gender"))
        return
    await state.update_data(target_gender=text if text else None)
    await message.answer(
        "Введите минимальный возраст для таргетинга (целое число; можно оставить пустым):",
        reply_markup=skip_keyboard("target_age_from")
    )
    await state.set_state(CampaignStates.waiting_for_target_age_from)


@router.callback_query(lambda c: c.data == "skip_target_gender")
async def skip_target_gender(callback: types.CallbackQuery, state: FSMContext) -> None:
    await state.update_data(target_gender=None)
    await state.set_state(CampaignStates.waiting_for_target_age_from)
    await callback.message.edit_text(
        "Пол для таргетинга пропущен.\nВведите минимальный возраст для таргетинга (целое число; можно оставить пустым):",
        reply_markup=skip_keyboard("target_age_from")
    )
    await callback.answer()


@router.message(CampaignStates.waiting_for_target_age_from)
async def process_target_age_from(message: types.Message, state: FSMContext) -> None:
    text = message.text.strip()
    age_from = None
    if text:
        try:
            age_from = int(text)
            if age_from < 0:
                raise ValueError
        except ValueError:
            await message.answer("Ошибка: введите корректное неотрицательное число для минимального возраста или нажмите «Пропустить».", reply_markup=skip_keyboard("target_age_from"))
            return
    await state.update_data(target_age_from=age_from)
    await message.answer(
        "Введите максимальный возраст для таргетинга (целое число; можно оставить пустым):",
        reply_markup=skip_keyboard("target_age_to")
    )
    await state.set_state(CampaignStates.waiting_for_target_age_to)


@router.callback_query(lambda c: c.data == "skip_target_age_from")
async def skip_target_age_from(callback: types.CallbackQuery, state: FSMContext) -> None:
    await state.update_data(target_age_from=None)
    await state.set_state(CampaignStates.waiting_for_target_age_to)
    await callback.message.edit_text(
        "Минимальный возраст для таргетинга пропущен.\nВведите максимальный возраст для таргетинга (целое число; можно оставить пустым):",
        reply_markup=skip_keyboard("target_age_to")
    )
    await callback.answer()


@router.message(CampaignStates.waiting_for_target_age_to)
async def process_target_age_to(message: types.Message, state: FSMContext) -> None:
    text = message.text.strip()
    age_to = None
    if text:
        try:
            age_to = int(text)
            if age_to < 0:
                raise ValueError
        except ValueError:
            await message.answer("Ошибка: введите корректное неотрицательное число для максимального возраста или нажмите «Пропустить».", reply_markup=skip_keyboard("target_age_to"))
            return
    await state.update_data(target_age_to=age_to)
    await message.answer(
        "Введите локацию для таргетинга (например, город; можно оставить пустым):",
        reply_markup=skip_keyboard("target_location")
    )
    await state.set_state(CampaignStates.waiting_for_target_location)


@router.callback_query(lambda c: c.data == "skip_target_age_to")
async def skip_target_age_to(callback: types.CallbackQuery, state: FSMContext) -> None:
    await state.update_data(target_age_to=None)
    await state.set_state(CampaignStates.waiting_for_target_location)
    await callback.message.edit_text(
        "Максимальный возраст для таргетинга пропущен.\nВведите локацию для таргетинга (например, город; можно оставить пустым):",
        reply_markup=skip_keyboard("target_location")
    )
    await callback.answer()


@router.message(CampaignStates.waiting_for_target_location)
async def process_target_location(message: types.Message, state: FSMContext) -> None:
    location = message.text.strip() or None
    await state.update_data(target_location=location)
    data = await state.get_data()
    if data.get("target_age_from") is not None and data.get("target_age_to") is not None:
        if data["target_age_to"] < data["target_age_from"]:
            await message.answer("Ошибка: значение максимального возраста должно быть не меньше минимального возраста.", reply_markup=cancel_keyboard())
            return
    targeting = {
        "gender": data.get("target_gender"),
        "age_from": data.get("target_age_from"),
        "age_to": data.get("target_age_to"),
        "location": data.get("target_location")
    }
    payload = {
        "ad_title": data["ad_title"],
        "ad_text": data["ad_text"],
        "start_date": data["start_date"],
        "end_date": data["end_date"],
        "impressions_limit": data["impressions_limit"],
        "clicks_limit": data["clicks_limit"],
        "cost_per_impression": data["cost_per_impression"],
        "cost_per_click": data["cost_per_click"],
        "targeting": targeting
    }
    try:
        campaign_data = CampaignCreate(**payload)
    except Exception as e:
        await message.answer(f"Ошибка валидации данных кампании: {e}", reply_markup=cancel_keyboard())
        return
    advertiser_id = data["advertiser_id"]
    endpoint = f"/advertisers/{advertiser_id}/campaigns"
    response = await api_post(endpoint, json_data=campaign_data.dict())
    if response.status_code == 201:
        campaign = response.json()
        formatted = "\n".join(f"{key}: {value}" for key, value in campaign.items())
        await message.answer(f"Кампания успешно создана!\n\nДанные кампании:\n{formatted}", reply_markup=cancel_keyboard())
    else:
        await message.answer(f"Ошибка создания кампании: {response.text}", reply_markup=cancel_keyboard())
    await state.clear()


@router.callback_query(lambda c: c.data == "skip_target_location")
async def skip_target_location(callback: types.CallbackQuery, state: FSMContext) -> None:
    await state.update_data(target_location=None)
    data = await state.get_data()
    targeting = {
        "gender": data.get("target_gender"),
        "age_from": data.get("target_age_from"),
        "age_to": data.get("target_age_to"),
        "location": None
    }
    payload = {
        "ad_title": data["ad_title"],
        "ad_text": data["ad_text"],
        "start_date": data["start_date"],
        "end_date": data["end_date"],
        "impressions_limit": data["impressions_limit"],
        "clicks_limit": data["clicks_limit"],
        "cost_per_impression": data["cost_per_impression"],
        "cost_per_click": data["cost_per_click"],
        "targeting": targeting
    }
    try:
        campaign_data = CampaignCreate(**payload)
    except Exception as e:
        await callback.message.answer(f"Ошибка валидации данных кампании: {e}", reply_markup=cancel_keyboard())
        await callback.answer()
        return
    advertiser_id = data["advertiser_id"]
    endpoint = f"/advertisers/{advertiser_id}/campaigns"
    response = await api_post(endpoint, json_data=campaign_data.dict())
    if response.status_code == 201:
        campaign = response.json()
        formatted = "\n".join(f"{key}: {value}" for key, value in campaign.items())
        await callback.message.answer(f"Кампания успешно создана!\n\nДанные кампании:\n{formatted}", reply_markup=cancel_keyboard())
    else:
        await callback.message.answer(f"Ошибка создания кампании: {response.text}", reply_markup=cancel_keyboard())
    await state.clear()
    await callback.answer()


# -------------- Получение кампании --------------

@router.callback_query(lambda c: c.data == "campaign_get")
async def get_campaign_start(callback: types.CallbackQuery, state: FSMContext) -> None:
    await callback.message.edit_text("Введите ID рекламодателя для получения кампании:", reply_markup=cancel_keyboard())
    await state.set_state(GetCampaignStates.waiting_for_advertiser_id)
    await callback.answer()


@router.message(GetCampaignStates.waiting_for_advertiser_id)
async def process_get_advertiser_id(message: types.Message, state: FSMContext) -> None:
    advertiser_id = message.text.strip()
    if not advertiser_id:
        await message.answer("Ошибка: ID рекламодателя обязателен.", reply_markup=cancel_keyboard())
        return
    if not validate_uuid(advertiser_id):
        await message.answer("Ошибка: неверный формат ID рекламодателя. Ожидается UUID.", reply_markup=cancel_keyboard())
        return
    await state.update_data(advertiser_id=advertiser_id)
    await message.answer("Введите ID кампании для получения:", reply_markup=cancel_keyboard())
    await state.set_state(GetCampaignStates.waiting_for_campaign_id)


@router.message(GetCampaignStates.waiting_for_campaign_id)
async def process_get_campaign_id(message: types.Message, state: FSMContext) -> None:
    campaign_id = message.text.strip()
    if not campaign_id:
        await message.answer("Ошибка: ID кампании обязателен.", reply_markup=cancel_keyboard())
        return
    if not validate_uuid(campaign_id):
        await message.answer("Ошибка: неверный формат ID кампании. Ожидается UUID.", reply_markup=cancel_keyboard())
        return
    data = await state.get_data()
    advertiser_id = data.get("advertiser_id")
    endpoint = f"/advertisers/{advertiser_id}/campaigns/{campaign_id}"
    response = await api_get(endpoint)
    if response.status_code == 200:
        campaign = response.json()
        formatted = "\n".join(f"{key}: {value}" for key, value in campaign.items())
        await message.answer(f"Данные кампании:\n{formatted}", reply_markup=cancel_keyboard())
    else:
        await message.answer(f"Ошибка получения кампании: {response.text}", reply_markup=cancel_keyboard())
    await state.clear()


# -------------- Обновление кампании (CampaignUpdate) --------------

@router.callback_query(lambda c: c.data == "campaign_update")
async def update_campaign_start(callback: types.CallbackQuery, state: FSMContext) -> None:
    await callback.message.edit_text("Введите ID рекламодателя для обновления кампании:", reply_markup=cancel_keyboard())
    await state.set_state(UpdateCampaignStates.waiting_for_advertiser_id)
    await callback.answer()


@router.message(UpdateCampaignStates.waiting_for_advertiser_id)
async def process_update_advertiser_id(message: types.Message, state: FSMContext) -> None:
    advertiser_id = message.text.strip()
    if not advertiser_id:
        await message.answer("Ошибка: ID рекламодателя обязателен.", reply_markup=cancel_keyboard())
        return
    if not validate_uuid(advertiser_id):
        await message.answer("Ошибка: неверный формат ID рекламодателя. Ожидается UUID.", reply_markup=cancel_keyboard())
        return
    await state.update_data(advertiser_id=advertiser_id)
    await message.answer("Введите ID кампании для обновления:", reply_markup=cancel_keyboard())
    await state.set_state(UpdateCampaignStates.waiting_for_campaign_id)


@router.message(UpdateCampaignStates.waiting_for_campaign_id)
async def process_update_campaign_id(message: types.Message, state: FSMContext) -> None:
    campaign_id = message.text.strip()
    if not campaign_id:
        await message.answer("Ошибка: ID кампании обязателен.", reply_markup=cancel_keyboard())
        return
    if not validate_uuid(campaign_id):
        await message.answer("Ошибка: неверный формат ID кампании. Ожидается UUID.", reply_markup=cancel_keyboard())
        return
    await state.update_data(campaign_id=campaign_id)
    await message.answer("Введите новый заголовок объявления (обязательно):", reply_markup=cancel_keyboard())
    await state.set_state(UpdateCampaignStates.waiting_for_update_ad_title)


@router.message(UpdateCampaignStates.waiting_for_update_ad_title)
async def process_update_ad_title(message: types.Message, state: FSMContext) -> None:
    ad_title = message.text.strip()
    if not ad_title:
        await message.answer("Ошибка: заголовок обязателен. Введите новый заголовок.", reply_markup=cancel_keyboard())
        return
    await state.update_data(update_ad_title=ad_title)
    await message.answer("Введите новый текст рекламного объявления (обязательно):", reply_markup=cancel_keyboard())
    await state.set_state(UpdateCampaignStates.waiting_for_update_ad_text)


@router.message(UpdateCampaignStates.waiting_for_update_ad_text)
async def process_update_ad_text(message: types.Message, state: FSMContext) -> None:
    ad_text = message.text.strip()
    if not ad_text:
        await message.answer("Ошибка: текст обязателен. Введите новый текст.", reply_markup=cancel_keyboard())
        return
    await state.update_data(update_ad_text=ad_text)
    await message.answer("Введите новый день начала кампании (целое число, обязательно):", reply_markup=cancel_keyboard())
    await state.set_state(UpdateCampaignStates.waiting_for_update_start_date)


@router.message(UpdateCampaignStates.waiting_for_update_start_date)
async def process_update_start_date(message: types.Message, state: FSMContext) -> None:
    try:
        start_date = safe_int(message.text.strip(), "дня начала кампании")
    except ValueError as e:
        await message.answer(str(e), reply_markup=cancel_keyboard())
        return
    await state.update_data(update_start_date=start_date)
    await message.answer("Введите новый день окончания кампании (целое число, обязательно):", reply_markup=cancel_keyboard())
    await state.set_state(UpdateCampaignStates.waiting_for_update_end_date)


@router.message(UpdateCampaignStates.waiting_for_update_end_date)
async def process_update_end_date(message: types.Message, state: FSMContext) -> None:
    try:
        end_date = safe_int(message.text.strip(), "дня окончания кампании")
    except ValueError as e:
        await message.answer(str(e), reply_markup=cancel_keyboard())
        return
    data = await state.get_data()
    if "update_start_date" in data and end_date < data["update_start_date"]:
        await message.answer("Ошибка: день окончания не может быть меньше дня начала. Повторите ввод.", reply_markup=cancel_keyboard())
        return
    await state.update_data(update_end_date=end_date)
    await message.answer("Введите новый лимит показов (целое число > 0, обязательно):", reply_markup=cancel_keyboard())
    await state.set_state(UpdateCampaignStates.waiting_for_update_impressions_limit)


@router.message(UpdateCampaignStates.waiting_for_update_impressions_limit)
async def process_update_impressions_limit(message: types.Message, state: FSMContext) -> None:
    try:
        impressions_limit = safe_positive_int(message.text.strip(), "лимита показов")
    except ValueError as e:
        await message.answer(str(e), reply_markup=cancel_keyboard())
        return
    await state.update_data(update_impressions_limit=impressions_limit)
    await message.answer("Введите новый лимит кликов (целое число ≥ 0, обязательно):", reply_markup=cancel_keyboard())
    await state.set_state(UpdateCampaignStates.waiting_for_update_clicks_limit)


@router.message(UpdateCampaignStates.waiting_for_update_clicks_limit)
async def process_update_clicks_limit(message: types.Message, state: FSMContext) -> None:
    try:
        clicks_limit = safe_positive_int(message.text.strip(), "лимита кликов")
    except ValueError as e:
        await message.answer(str(e), reply_markup=cancel_keyboard())
        return
    data = await state.get_data()
    if "update_impressions_limit" in data and clicks_limit > data["update_impressions_limit"]:
        await message.answer("Ошибка: лимит кликов не может превышать лимит показов. Повторите ввод.", reply_markup=cancel_keyboard())
        return
    await state.update_data(update_clicks_limit=clicks_limit)
    await message.answer("Введите новую стоимость за показ (число с плавающей точкой > 0, обязательно):", reply_markup=cancel_keyboard())
    await state.set_state(UpdateCampaignStates.waiting_for_update_cost_per_impression)


@router.message(UpdateCampaignStates.waiting_for_update_cost_per_impression)
async def process_update_cost_per_impression(message: types.Message, state: FSMContext) -> None:
    try:
        cost_per_impression = safe_positive_float(message.text.strip(), "стоимости за показ")
    except ValueError as e:
        await message.answer(str(e), reply_markup=cancel_keyboard())
        return
    await state.update_data(update_cost_per_impression=cost_per_impression)
    await message.answer("Введите новую стоимость за клик (число с плавающей точкой > 0, обязательно):", reply_markup=cancel_keyboard())
    await state.set_state(UpdateCampaignStates.waiting_for_update_cost_per_click)


@router.message(UpdateCampaignStates.waiting_for_update_cost_per_click)
async def process_update_cost_per_click(message: types.Message, state: FSMContext) -> None:
    try:
        cost_per_click = safe_positive_float(message.text.strip(), "стоимости за клик")
    except ValueError as e:
        await message.answer(str(e), reply_markup=cancel_keyboard())
        return
    await state.update_data(update_cost_per_click=cost_per_click)
    await message.answer(
        "Введите новый пол для таргетинга (MALE, FEMALE или ALL; можно оставить пустым):",
        reply_markup=skip_keyboard("update_target_gender")
    )
    await state.set_state(UpdateCampaignStates.waiting_for_update_target_gender)


@router.message(UpdateCampaignStates.waiting_for_update_target_gender)
async def process_update_target_gender(message: types.Message, state: FSMContext) -> None:
    text = message.text.strip()
    if text.isdigit():
        await message.answer("Ошибка: вместо пола введено число. Если хотите пропустить, нажмите «Пропустить».", reply_markup=skip_keyboard("update_target_gender"))
        return
    if text and text not in ("MALE", "FEMALE", "ALL"):
        await message.answer("Ошибка: пол должен быть введён как MALE, FEMALE или ALL. Повторите ввод или нажмите «Пропустить».", reply_markup=skip_keyboard("update_target_gender"))
        return
    await state.update_data(update_target_gender=text if text else None)
    await message.answer("Введите новый минимальный возраст для таргетинга (целое число; можно оставить пустым):", reply_markup=skip_keyboard("update_target_age_from"))
    await state.set_state(UpdateCampaignStates.waiting_for_update_target_age_from)


@router.callback_query(lambda c: c.data == "skip_update_target_gender")
async def skip_update_target_gender(callback: types.CallbackQuery, state: FSMContext) -> None:
    await state.update_data(update_target_gender=None)
    await state.set_state(UpdateCampaignStates.waiting_for_update_target_age_from)
    await callback.message.edit_text(
        "Пол для таргетинга пропущен.\nВведите новый минимальный возраст для таргетинга (целое число; можно оставить пустым):",
        reply_markup=skip_keyboard("update_target_age_from")
    )
    await callback.answer()


@router.message(UpdateCampaignStates.waiting_for_update_target_age_from)
async def process_update_target_age_from(message: types.Message, state: FSMContext) -> None:
    text = message.text.strip()
    age_from = None
    if text:
        try:
            age_from = int(text)
            if age_from < 0:
                raise ValueError
        except ValueError:
            await message.answer("Ошибка: введите корректное неотрицательное число для минимального возраста или нажмите «Пропустить».", reply_markup=skip_keyboard("update_target_age_from"))
            return
    await state.update_data(update_target_age_from=age_from)
    await message.answer("Введите новый максимальный возраст для таргетинга (целое число; можно оставить пустым):", reply_markup=skip_keyboard("update_target_age_to"))
    await state.set_state(UpdateCampaignStates.waiting_for_update_target_age_to)


@router.callback_query(lambda c: c.data == "skip_update_target_age_from")
async def skip_update_target_age_from(callback: types.CallbackQuery, state: FSMContext) -> None:
    await state.update_data(update_target_age_from=None)
    await state.set_state(UpdateCampaignStates.waiting_for_update_target_age_to)
    await callback.message.edit_text(
        "Минимальный возраст для таргетинга пропущен.\nВведите новый максимальный возраст для таргетинга (целое число; можно оставить пустым):",
        reply_markup=skip_keyboard("update_target_age_to")
    )
    await callback.answer()


@router.message(UpdateCampaignStates.waiting_for_update_target_age_to)
async def process_update_target_age_to(message: types.Message, state: FSMContext) -> None:
    text = message.text.strip()
    age_to = None
    if text:
        try:
            age_to = int(text)
            if age_to < 0:
                raise ValueError
        except ValueError:
            await message.answer("Ошибка: введите корректное неотрицательное число для максимального возраста или нажмите «Пропустить».", reply_markup=skip_keyboard("update_target_age_to"))
            return
    await state.update_data(update_target_age_to=age_to)
    await message.answer("Введите новую локацию для таргетинга (например, город; можно оставить пустым):", reply_markup=skip_keyboard("update_target_location"))
    await state.set_state(UpdateCampaignStates.waiting_for_update_target_location)


@router.callback_query(lambda c: c.data == "skip_update_target_age_to")
async def skip_update_target_age_to(callback: types.CallbackQuery, state: FSMContext) -> None:
    await state.update_data(update_target_age_to=None)
    await state.set_state(UpdateCampaignStates.waiting_for_update_target_location)
    await callback.message.edit_text(
        "Максимальный возраст для таргетинга пропущен.\nВведите новую локацию для таргетинга (например, город; можно оставить пустым):",
        reply_markup=skip_keyboard("update_target_location")
    )
    await callback.answer()


@router.message(UpdateCampaignStates.waiting_for_update_target_location)
async def process_update_target_location(message: types.Message, state: FSMContext) -> None:
    location = message.text.strip() or None
    await state.update_data(update_target_location=location)
    data = await state.get_data()
    if data.get("update_target_age_from") is not None and data.get("update_target_age_to") is not None:
        if data["update_target_age_to"] < data["update_target_age_from"]:
            await message.answer("Ошибка: значение максимального возраста должно быть не меньше минимального возраста.", reply_markup=cancel_keyboard())
            return
    targeting = {
        "gender": data.get("update_target_gender"),
        "age_from": data.get("update_target_age_from"),
        "age_to": data.get("update_target_age_to"),
        "location": data.get("update_target_location")
    }
    payload = {
        "ad_title": data["update_ad_title"],
        "ad_text": data["update_ad_text"],
        "start_date": data["update_start_date"],
        "end_date": data["update_end_date"],
        "impressions_limit": data["update_impressions_limit"],
        "clicks_limit": data["update_clicks_limit"],
        "cost_per_impression": data["update_cost_per_impression"],
        "cost_per_click": data["update_cost_per_click"],
        "targeting": targeting
    }
    try:
        update_data = CampaignUpdate(**payload)
    except Exception as e:
        await message.answer(f"Ошибка валидации данных кампании: {e}", reply_markup=cancel_keyboard())
        return
    advertiser_id = data["advertiser_id"]
    campaign_id = data["campaign_id"]
    endpoint = f"/advertisers/{advertiser_id}/campaigns/{campaign_id}"
    response = await api_put(endpoint, json_data=update_data.dict())
    if response.status_code == 200:
        campaign = response.json()
        formatted = "\n".join(f"{key}: {value}" for key, value in campaign.items())
        await message.answer(f"Кампания успешно обновлена!\n\nДанные кампании:\n{formatted}", reply_markup=cancel_keyboard())
    else:
        await message.answer(f"Ошибка обновления кампании: {response.text}", reply_markup=cancel_keyboard())
    await state.clear()


@router.callback_query(lambda c: c.data == "skip_update_target_location")
async def skip_update_target_location(callback: types.CallbackQuery, state: FSMContext) -> None:
    await state.update_data(update_target_location=None)
    data = await state.get_data()
    targeting = {
        "gender": data.get("update_target_gender"),
        "age_from": data.get("update_target_age_from"),
        "age_to": data.get("update_target_age_to"),
        "location": None
    }
    payload = {
        "ad_title": data["update_ad_title"],
        "ad_text": data["update_ad_text"],
        "start_date": data["update_start_date"],
        "end_date": data["update_end_date"],
        "impressions_limit": data["update_impressions_limit"],
        "clicks_limit": data["update_clicks_limit"],
        "cost_per_impression": data["update_cost_per_impression"],
        "cost_per_click": data["update_cost_per_click"],
        "targeting": targeting
    }
    try:
        update_data = CampaignUpdate(**payload)
    except Exception as e:
        await callback.message.answer(f"Ошибка валидации данных кампании: {e}", reply_markup=cancel_keyboard())
        await callback.answer()
        return
    advertiser_id = data["advertiser_id"]
    campaign_id = data["campaign_id"]
    endpoint = f"/advertisers/{advertiser_id}/campaigns/{campaign_id}"
    response = await api_put(endpoint, json_data=update_data.dict())
    if response.status_code == 200:
        campaign = response.json()
        formatted = "\n".join(f"{key}: {value}" for key, value in campaign.items())
        await callback.message.answer(f"Кампания успешно обновлена!\n\nДанные кампании:\n{formatted}", reply_markup=cancel_keyboard())
    else:
        await callback.message.answer(f"Ошибка обновления кампании: {response.text}", reply_markup=cancel_keyboard())
    await state.clear()
    await callback.answer()


# -------------- Удаление кампании --------------

@router.callback_query(lambda c: c.data == "campaign_delete")
async def delete_campaign_start(callback: types.CallbackQuery, state: FSMContext) -> None:
    await callback.message.edit_text("Введите ID рекламодателя для удаления кампании:", reply_markup=cancel_keyboard())
    await state.set_state(DeleteCampaignStates.waiting_for_advertiser_id)
    await callback.answer()


@router.message(DeleteCampaignStates.waiting_for_advertiser_id)
async def process_delete_advertiser_id(message: types.Message, state: FSMContext) -> None:
    advertiser_id = message.text.strip()
    if not advertiser_id:
        await message.answer("Ошибка: ID рекламодателя обязателен. Введите его.", reply_markup=cancel_keyboard())
        return
    if not validate_uuid(advertiser_id):
        await message.answer("Ошибка: неверный формат ID рекламодателя. Ожидается UUID.", reply_markup=cancel_keyboard())
        return
    await state.update_data(advertiser_id=advertiser_id)
    await message.answer("Введите ID кампании для удаления:", reply_markup=cancel_keyboard())
    await state.set_state(DeleteCampaignStates.waiting_for_campaign_id)


@router.message(DeleteCampaignStates.waiting_for_campaign_id)
async def process_delete_campaign_id(message: types.Message, state: FSMContext) -> None:
    campaign_id = message.text.strip()
    if not campaign_id:
        await message.answer("Ошибка: ID кампании обязателен. Введите его.", reply_markup=cancel_keyboard())
        return
    if not validate_uuid(campaign_id):
        await message.answer("Ошибка: неверный формат ID кампании. Ожидается UUID.", reply_markup=cancel_keyboard())
        return
    data = await state.get_data()
    advertiser_id = data["advertiser_id"]
    endpoint = f"/advertisers/{advertiser_id}/campaigns/{campaign_id}"
    response = await api_delete(endpoint)
    if response.status_code == 204:
        await message.answer("Кампания успешно удалена!", reply_markup=cancel_keyboard())
    else:
        await message.answer(f"Ошибка удаления кампании: {response.text}", reply_markup=cancel_keyboard())
    await state.clear()


@router.callback_query(lambda c: c.data == "campaign_list")
async def list_campaigns_start(callback: types.CallbackQuery, state: FSMContext) -> None:
    await callback.message.edit_text(
        "Введите ID рекламодателя для получения списка кампаний:",
        reply_markup=cancel_keyboard()
    )
    await state.set_state(ImageGetALLStates.waiting_for_list_advertiser_id)
    await callback.answer()


@router.message(ImageGetALLStates.waiting_for_list_advertiser_id)
async def process_list_advertiser_id(message: types.Message, state: FSMContext) -> None:
    advertiser_id = message.text.strip()
    if not advertiser_id:
        await message.answer("Ошибка: ID рекламодателя обязателен.", reply_markup=cancel_keyboard())
        return
    if not validate_uuid(advertiser_id):
        await message.answer("Ошибка: неверный формат ID рекламодателя. Ожидается UUID.", reply_markup=cancel_keyboard())
        return

    endpoint = f"/advertisers/{advertiser_id}/campaigns"
    response = await api_get(endpoint)
    if response.status_code == 200:
        campaigns = response.json()
        if not campaigns:
            await message.answer("Нет кампаний для данного рекламодателя.", reply_markup=cancel_keyboard())
        else:
            text = "Список кампаний:\n\n"
            for campaign in campaigns:
                text += format_campaign_data(campaign) + "\n\n"
            await message.answer(text, reply_markup=cancel_keyboard())
    else:
        await message.answer(f"Ошибка получения кампаний: {response.text}", reply_markup=cancel_keyboard())
    await state.clear()
