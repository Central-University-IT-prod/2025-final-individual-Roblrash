import pytest
from src.services.ad_matching import campaign_matches_client
from src.schemas.client import ClientOut

VALID_UUID = "00000000-0000-0000-0000-000000000000"

@pytest.mark.parametrize(
    "targeting, client, expected",
    [
        (
            {"gender": "MALE", "age_from": 18, "age_to": 30, "location": "CityA"},
            {"client_id": VALID_UUID, "login": "user", "age": 25, "location": "CityA", "gender": "MALE"},
            True,
        ),
        (
            {"gender": "FEMALE", "age_from": 18, "age_to": 30, "location": "CityA"},
            {"client_id": VALID_UUID, "login": "user", "age": 25, "location": "CityA", "gender": "MALE"},
            False,
        ),
        (
            {"age_from": 20, "age_to": 40},
            {"client_id": VALID_UUID, "login": "user", "age": 18, "location": "CityB", "gender": "FEMALE"},
            False,
        ),
        (
            {},
            {"client_id": VALID_UUID, "login": "user", "age": 50, "location": "CityC", "gender": "FEMALE"},
            True,
        ),
    ],
)
def test_campaign_matches_client(targeting, client, expected):
    client_obj = ClientOut(**client)
    result = campaign_matches_client(targeting, client_obj)
    assert result == expected
