from aiogram.types import InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

def main_menu_keyboard():
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="Кампании", callback_data="menu_campaigns"),
        InlineKeyboardButton(text="Статистика", callback_data="menu_stats")
    )
    builder.row(
        InlineKeyboardButton(text="Изображения", callback_data="menu_images"),
        InlineKeyboardButton(text="Модерация", callback_data="menu_moderation")
    )
    builder.row(
        InlineKeyboardButton(text="Генерация реклам. текста", callback_data="menu_ai_text")
    )
    return builder.as_markup()

def campaigns_menu_keyboard():
    builder = InlineKeyboardBuilder()
    builder.button(text="Создать кампанию", callback_data="campaign_create")
    builder.button(text="Получить кампанию", callback_data="campaign_get")
    builder.button(text="Обновить кампанию", callback_data="campaign_update")
    builder.button(text="Удалить кампанию", callback_data="campaign_delete")
    builder.button(text="Список кампаний", callback_data="campaign_list")
    builder.button(text="Главное меню", callback_data="back_main")
    builder.adjust(1)
    return builder.as_markup()

def stats_menu_keyboard():
    builder = InlineKeyboardBuilder()
    builder.button(text="Статистика кампании", callback_data="stats_campaign")
    builder.button(text="Статистика рекламодателя", callback_data="stats_advertiser")
    builder.button(text="Дневная статистика кампании", callback_data="stats_campaign_daily")
    builder.button(text="Дневная статистика рекламодателя", callback_data="stats_advertiser_daily")
    builder.button(text="Главное меню", callback_data="back_main")
    builder.adjust(1)
    return builder.as_markup()

def images_menu_keyboard():
    builder = InlineKeyboardBuilder()
    builder.button(text="Загрузить изображение", callback_data="image_upload")
    builder.button(text="Обновить изображение", callback_data="image_update")
    builder.button(text="Удалить изображение", callback_data="image_delete")
    builder.button(text="Получить изображение", callback_data="image_get")
    builder.button(text="Главное меню", callback_data="back_main")
    builder.adjust(1)
    return builder.as_markup()

def moderation_menu_keyboard():
    builder = InlineKeyboardBuilder()
    builder.button(text="Включить модерацию", callback_data="moderation_on")
    builder.button(text="Выключить модерацию", callback_data="moderation_off")
    builder.button(text="Главное меню", callback_data="back_main")
    builder.adjust(1)
    return builder.as_markup()

def cancel_keyboard():
    builder = InlineKeyboardBuilder()
    builder.button(text="Главное меню", callback_data="back_main")
    builder.adjust(1)
    return builder.as_markup()

def skip_keyboard(field: str):
    builder = InlineKeyboardBuilder()
    builder.button(text="Пропустить", callback_data=f"skip_{field}")
    builder.button(text="Главное меню", callback_data="back_main")
    builder.adjust(2)
    return builder.as_markup()