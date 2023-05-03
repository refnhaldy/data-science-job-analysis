import pandas as pd

# Get Indonesia geographical data from Wikipedia
url = 'https://id.wikipedia.org/wiki/Daftar_kota_di_Indonesia_menurut_jumlah_penduduk'
table = pd.read_html(url)[0]
cities = list(table['Kota'])
cities = [city.replace('Kota ', '') for city in cities]
provinces = list(table['Provinsi'].unique())
city_prov_dict = dict(zip(cities, table['Provinsi']))