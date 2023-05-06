import pandas as pd

# Get Indonesia geographical data from Wikipedia
url = 'https://id.wikipedia.org/wiki/Daftar_kota_di_Indonesia_menurut_jumlah_penduduk'

try:
    table = pd.read_html(url)[0]
except Exception as e:
    print(f"Error retrieving data from {url}: {e}")
    exit()

city_list = list(table['Kota'])
city_list = [city.replace('Kota ', '') for city in city_list]

province_list = list(table['Provinsi'].unique())
province_list[0] = 'Jakarta'
province_list[22] = 'Yogyakarta'

city_province_dict = dict(zip(city_list, province_list))