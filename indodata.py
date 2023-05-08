import pandas as pd

# Get Indonesia geographical data from Wikipedia
url = 'https://id.wikipedia.org/wiki/Daftar_kota_di_Indonesia_menurut_jumlah_penduduk'

try:
    table = pd.read_html(url)[0]
except Exception as e:
    print(f"Error retrieving data from {url}: {e}")
    exit()

# Get city list
city_list = list(table['Kota'])
city_list = [city.replace('Kota ', '') for city in city_list]

# Get province that in same lenght with cities for dictonary
province_dict = list(table['Provinsi'])
for i in range(len(province_dict)):
    if province_dict[i] == 'Daerah Khusus Ibukota Jakarta':
        province_dict[i] = 'Jakarta'
    elif province_dict[i] == 'Daerah Istimewa Yogyakarta':
        province_dict[i] = 'Yogyakarta'

# Get province list
province_list = list(set(province_dict))

# Create dict for mapping
city_province_dict = dict(zip(city_list, province_dict))