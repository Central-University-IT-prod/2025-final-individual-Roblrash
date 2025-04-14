from aiogram import types, Router
from aiogram.fsm.context import FSMContext
from utils.api_client import api_get
from utils.keyboards import stats_menu_keyboard, cancel_keyboard
from utils.states import StatsCampaignStates, StatsAdvertiserStates

router = Router()

@router.callback_query(lambda c: c.data == "menu_stats")
async def stats_menu(callback: types.CallbackQuery) -> None:
    await callback.message.edit_text(
        "Статистика – выберите действие:",
        reply_markup=stats_menu_keyboard()
    )
    await callback.answer()

@router.callback_query(lambda c: c.data == "stats_campaign")
async def stats_campaign_start(callback: types.CallbackQuery, state: FSMContext) -> None:
    await callback.message.edit_text(
        "Введите ID кампании для получения статистики:",
        reply_markup=cancel_keyboard()
    )
    await state.set_state(StatsCampaignStates.waiting_for_campaign_id)
    await callback.answer()

@router.message(StatsCampaignStates.waiting_for_campaign_id)
async def process_stats_campaign(message: types.Message, state: FSMContext) -> None:
    campaign_id = message.text.strip()
    endpoint = f"/stats/campaigns/{campaign_id}"
    response = await api_get(endpoint)
    if response.status_code == 200:
        stats = response.json()
        text = (
            f"Статистика кампании {campaign_id}:\n"
            f"Показы: {stats.get('impressions_count')}\n"
            f"Клики: {stats.get('clicks_count')}\n"
            f"Конверсия: {stats.get('conversion'):.2f}%\n"
            f"Расход на показы: {stats.get('spent_impressions')}\n"
            f"Расход на клики: {stats.get('spent_clicks')}\n"
            f"Итого: {stats.get('spent_total')}"
        )
    else:
        text = f"Ошибка получения статистики: {response.text}"
    await message.answer(text, reply_markup=cancel_keyboard())
    await state.clear()

@router.callback_query(lambda c: c.data == "stats_advertiser")
async def stats_advertiser_start(callback: types.CallbackQuery, state: FSMContext) -> None:
    await callback.message.edit_text(
        "Введите ID рекламодателя для получения статистики:",
        reply_markup=cancel_keyboard()
    )
    await state.set_state(StatsAdvertiserStates.waiting_for_advertiser_id)
    await callback.answer()

@router.message(StatsAdvertiserStates.waiting_for_advertiser_id)
async def process_stats_advertiser(message: types.Message, state: FSMContext) -> None:
    advertiser_id = message.text.strip()
    endpoint = f"/stats/advertisers/{advertiser_id}/campaigns"
    response = await api_get(endpoint)
    if response.status_code == 200:
        stats = response.json()
        text = (
            f"Статистика рекламодателя {advertiser_id}:\n"
            f"Показы: {stats.get('impressions_count')}\n"
            f"Клики: {stats.get('clicks_count')}\n"
            f"Конверсия: {stats.get('conversion'):.2f}%\n"
            f"Расход на показы: {stats.get('spent_impressions')}\n"
            f"Расход на клики: {stats.get('spent_clicks')}\n"
            f"Итого: {stats.get('spent_total')}"
        )
    else:
        text = f"Ошибка получения статистики: {response.text}"
    await message.answer(text, reply_markup=cancel_keyboard())
    await state.clear()

@router.callback_query(lambda c: c.data == "stats_campaign_daily")
async def stats_campaign_daily_start(callback: types.CallbackQuery, state: FSMContext) -> None:
    await callback.message.edit_text(
        "Введите ID кампании для получения статистики по дням:",
        reply_markup=cancel_keyboard()
    )
    await state.set_state(StatsCampaignStates.waiting_for_campaign_id_daily)
    await callback.answer()

@router.message(StatsCampaignStates.waiting_for_campaign_id_daily)
async def process_stats_campaign_daily(message: types.Message, state: FSMContext) -> None:
    campaign_id = message.text.strip()
    endpoint = f"/stats/campaigns/{campaign_id}/daily"
    response = await api_get(endpoint)
    if response.status_code == 200:
        daily_stats = response.json()
        if not daily_stats:
            text = f"Нет статистики по дням для кампании {campaign_id}."
        else:
            text = f"Статистика по дням для кампании {campaign_id}:\n\n"
            for stat in daily_stats:
                text += (
                    f"Дата: {stat.get('date')}\n"
                    f"Показы: {stat.get('impressions_count')}\n"
                    f"Клики: {stat.get('clicks_count')}\n"
                    f"Конверсия: {stat.get('conversion'):.2f}%\n"
                    f"Расход на показы: {stat.get('spent_impressions')}\n"
                    f"Расход на клики: {stat.get('spent_clicks')}\n"
                    f"Итого: {stat.get('spent_total')}\n\n"
                )
    else:
        text = f"Ошибка получения статистики: {response.text}"
    await message.answer(text, reply_markup=cancel_keyboard())
    await state.clear()

@router.callback_query(lambda c: c.data == "stats_advertiser_daily")
async def stats_advertiser_daily_start(callback: types.CallbackQuery, state: FSMContext) -> None:
    await callback.message.edit_text(
        "Введите ID рекламодателя для получения статистики по дням:",
        reply_markup=cancel_keyboard()
    )
    await state.set_state(StatsAdvertiserStates.waiting_for_advertiser_id_daily)
    await callback.answer()

@router.message(StatsAdvertiserStates.waiting_for_advertiser_id_daily)
async def process_stats_advertiser_daily(message: types.Message, state: FSMContext) -> None:
    advertiser_id = message.text.strip()
    endpoint = f"/stats/advertisers/{advertiser_id}/campaigns/daily"
    response = await api_get(endpoint)
    if response.status_code == 200:
        daily_stats = response.json()
        if not daily_stats:
            text = f"Нет статистики по дням для рекламодателя {advertiser_id}."
        else:
            text = f"Статистика по дням для рекламодателя {advertiser_id}:\n\n"
            for stat in daily_stats:
                text += (
                    f"Дата: {stat.get('date')}\n"
                    f"Показы: {stat.get('impressions_count')}\n"
                    f"Клики: {stat.get('clicks_count')}\n"
                    f"Конверсия: {stat.get('conversion'):.2f}%\n"
                    f"Расход на показы: {stat.get('spent_impressions')}\n"
                    f"Расход на клики: {stat.get('spent_clicks')}\n"
                    f"Итого: {stat.get('spent_total')}\n\n"
                )
    else:
        text = f"Ошибка получения статистики: {response.text}"
    await message.answer(text, reply_markup=cancel_keyboard())
    await state.clear()
