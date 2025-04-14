from aiogram.fsm.state import State, StatesGroup

class CampaignStates(StatesGroup):
    waiting_for_advertiser_id = State()
    waiting_for_ad_title = State()
    waiting_for_ad_text = State()
    waiting_for_start_date = State()
    waiting_for_end_date = State()
    waiting_for_impressions_limit = State()
    waiting_for_clicks_limit = State()
    waiting_for_cost_per_impression = State()
    waiting_for_cost_per_click = State()
    waiting_for_target_gender = State()
    waiting_for_target_age_from = State()
    waiting_for_target_age_to = State()
    waiting_for_target_location = State()

class UpdateCampaignStates(StatesGroup):
    waiting_for_advertiser_id = State()
    waiting_for_campaign_id = State()
    waiting_for_update_ad_title = State()
    waiting_for_update_ad_text = State()
    waiting_for_update_start_date = State()
    waiting_for_update_end_date = State()
    waiting_for_update_impressions_limit = State()
    waiting_for_update_clicks_limit = State()
    waiting_for_update_cost_per_impression = State()
    waiting_for_update_cost_per_click = State()
    waiting_for_update_target_gender = State()
    waiting_for_update_target_age_from = State()
    waiting_for_update_target_age_to = State()
    waiting_for_update_target_location = State()

class GetCampaignStates(StatesGroup):
    waiting_for_advertiser_id = State()
    waiting_for_campaign_id = State()

class DeleteCampaignStates(StatesGroup):
    waiting_for_advertiser_id = State()
    waiting_for_campaign_id = State()

class StatsCampaignStates(StatesGroup):
    waiting_for_campaign_id = State()
    waiting_for_campaign_id_daily = State()

class StatsAdvertiserStates(StatesGroup):
    waiting_for_advertiser_id = State()
    waiting_for_advertiser_id_daily = State()

class ImageUploadStates(StatesGroup):
    waiting_for_ad_id = State()
    waiting_for_image = State()

class ImageUpdateStates(StatesGroup):
    waiting_for_ad_id = State()
    waiting_for_image = State()

class ImageDeleteStates(StatesGroup):
    waiting_for_ad_id = State()

class ImageGetStates(StatesGroup):
    waiting_for_ad_id = State()

class ImageGetALLStates(StatesGroup):
    waiting_for_list_advertiser_id = State()

class AiTextStates(StatesGroup):
    waiting_for_ad_title = State()
    waiting_for_advertiser_name = State()
