def campaign_matches_client(targeting: dict, client) -> bool:
    """
    Если таргетинг отсутствует (None), кампания подходит для всех.
    Если в таргетинге конкретное поле равно None, то по этому параметру ограничение отсутствует.
    """
    if targeting is None:
        return True

    if targeting.get("gender") is not None:
        if targeting["gender"].upper() != client.gender.upper() and targeting["gender"].upper() != 'ALL':
            return False

    if targeting.get("age_from") is not None:
        if client.age < targeting["age_from"]:
            return False
    if targeting.get("age_to") is not None:
        if client.age > targeting["age_to"]:
            return False

    if targeting.get("location") is not None:
        if targeting["location"] != client.location:
            return False

    return True

