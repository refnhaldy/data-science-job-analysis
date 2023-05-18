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