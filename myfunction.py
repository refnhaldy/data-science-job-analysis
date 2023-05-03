from indodata import *

# A function to standarized the city name
def map_city(city_name):
    """
    This function takes existing city name as an input and returns the standardized
    version of the city.

    Args:
    - city_name (str): the name of a city.

    Returns:
    - str: the standardized version of the city

    Example Usage:

    >>> map_city('Kota Jakarta')
    'Area DKI Jakarta'
    >>> map_city('Jakarta Timur')
    'Jakarta Timur'
    >>> map_city('Bandung, Indonesia')
    'Bandung'
    """
    for c in cities:
        if c in city_name:
            return c
    if 'Jakarta' in city_name:
        return 'Area DKI Jakarta'
    return city_name

# A function to get the province based on the given city
def get_province(city_name):
    """
    This function takes a city name as input and returns the corresponding province name.

    Args:
    - city_name (str): the name of a city

    Returns:
    - str: the name of the province

    Example Usage:

    >>> get_province('Jakarta Timur')
    'Jakarta'
    >>> map_city('Tangerang')
    'Banten'
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
    - province_name (str): the name of a province

    Returns:
    - str: the name of the country
    
    Example Usage:

    >>> get_country('Jakarta')
    'Indonesia'
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