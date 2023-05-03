from indodata import *

# A function to get the province based on the given city
def get_province(city_name):
    """
    This function takes a city name as input and returns the corresponding province name.

    Args:
    - city (str): the name of a city

    Returns:
    - str: the name of the province
    """
    if 'Jakarta' in city_name:
        return 'Jakarta'
    elif 'Yogyakarta' in city_name:
        return 'Yogyakarta'
    for c in cities:
        if c in city_name:
            return city_prov_dict[c]
    return city_name

# A function to get the country based on the given province
def get_country(province_name):
    """
    This function takes a province name as input and returns the corresponding country name.

    Args:
    - city (str): the name of a province

    Returns:
    - str: the name of the country
    """
    if 'Jakarta' in province_name:
        return 'Indonesia'
    elif 'Yogyakarta' in province_name:
        return 'Indonesia'
    for p in provinces:
        """
        p is checked first to make sure it is exist in the province name

        e.g. 'Jakarta' is in 'Area Jakarta' not 'Area Jakarta' is in 'Jakarta'
        """
        if p in province_name:
            return 'Indonesia'
    return

# A function to standarized the city name
def map_city(city_name):
    for c in cities:
        if c in city_name:
            return c
    if 'Jakarta' in city_name:
        return 'Area DKI Jakarta'
    return city_name