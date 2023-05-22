import pandas as pd

# Get Indonesia geographical data from Wikipedia
url = 'https://id.wikipedia.org/wiki/Daftar_kota_di_Indonesia'

try:
    table = pd.read_html(url)[0]
except Exception as e:
    print(f"Error retrieving data from {url}: {e}")
    exit()

# Drop empty rows
table = table.drop(index=10).reset_index(drop=True)
# Clean data
table['Kota'] = table['Kota'].str.replace('Kota ', '').str.replace('Administrasi ', '')
table['Provinsi'] = table['Provinsi'].str.replace('Daerah Khusus Ibukota ', '').str.replace('Daerah Istimewa ', '')
# Get city list
city_list = list(table['Kota'])
# Get province that in same lenght with cities for dictonary
province_dict = list(table['Provinsi'])
# Get province list
provinces = list(set(province_dict))
# Create dict for mapping
city_province_dict = dict(zip(city_list, province_dict))



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
    for c in city_list:
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
    >>> get_province('Tangerang')
    'Banten'
    """
    if 'Jakarta' in city_name:
        return 'Jakarta'
    elif 'Yogyakarta' in city_name:
        return 'Yogyakarta'
    for c in city_list:
        if c in city_name:
            return city_province_dict[c]
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