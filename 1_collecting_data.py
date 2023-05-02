__version__ = "0.2.0"

import pandas as pd
import itertools
import requests
import gspread

from bs4 import BeautifulSoup
from oauth2client.service_account import ServiceAccountCredentials

# def map_province(prov):
#     for p in provinces_en:
#         if p in prov:
#             return provinces_dict.get(p, prov)
#     return prov

def get_province(city):
    if 'Jakarta' in city:
        return 'Jakarta'
    elif 'Yogyakarta' in city:
        return 'Yogyakarta'
    
    for key in city_prov_dict.keys():
        if key in city:
            return city_prov_dict[key]
    return city

# Get list of cities in indonesian from Wikipedia
url = 'https://id.wikipedia.org/wiki/Daftar_kota_di_Indonesia_menurut_jumlah_penduduk'
table = pd.read_html(url)[0]
cities = list(table['Kota'])
cities = [city.replace('Kota ', '') for city in cities]
provinces = list(table['Provinsi'].unique())
# prov_test = ['Jakarta', 'Jawa Timur', 'Jawa Barat']

# Create Province_Ciies dictonary
city_prov = list(table['Provinsi'])
city_prov_dict = dict(zip(cities, city_prov))

# # Get list of cities in english from Wikipedia
# url_en = 'https://en.wikipedia.org/wiki/List_of_Indonesian_cities_by_population'
# table_en = pd.read_html(url_en)[1]
# cities_en = list(table_en['City'])
# provinces_en = list(table_en['Province'].unique())

# Set search terms
terms = ['Data%20Engineer', 'Data%20Scientist', 'Data%20Analyst']

# Initialize variables
data = []

# Loop through all possible combinations of terms and cities
for term, province in itertools.product(terms, provinces):
    province = province.replace(' ', '%20')
    url = f'https://www.linkedin.com/jobs/search?keywords={term}&location={province}&locationId=&geoId=&f_TPR=&position=1&pageNum=0'

    headers = {'Accept-Language': 'id-ID,id;q=0.9,en-US;q=0.8,en;q=0.7'}

    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        jobs_container = soup.find('ul', 'jobs-search__results-list')
        jobs = jobs_container.find_all('li')
    except (requests.exceptions.HTTPError, ValueError):
        continue

    if jobs is None:
        continue

    for job in jobs:
        # Get job information
        job_title = job.find('h3', 'base-search-card__title').text.strip()
        company_name = job.find('h4', 'base-search-card__subtitle').text.strip()
        city = job.find('span', 'job-search-card__location').text.strip()
        date_posted = job.find('time', 'job-search-card__listdate')

        date_posted = date_posted.get('datetime') if date_posted else None

        # Add job information to data list
        data.append([job_title, company_name, city, date_posted])

# Create pandas DataFrame from data list
columns = ['job_title', 'company_name', 'city', 'date_posted']
df = pd.DataFrame(data, columns=columns)

### This is a block of new code

# TODO: Write appropriate comment
like_cities = '|'.join(cities) + '|Jakarta'

# TODO: Write appropriate comment
df = df[df['city'].str.contains(like_cities)]

# TODO: write comment
df['city'] = df['city'].apply(lambda x: next((c for c in cities if c in x.split()), x))

# extract province information
# df['province'] = df['city'].apply(lambda x: [city_prov_dict[word] for word in x.split() if word in city_prov_dict.keys()] else x)
df['province'] = df['city'].apply(get_province)

# extract country information
df['country'] = 'Indonesia' if df['city'].str.contains(like_cities).any() else None

### This is a block of new code

# Reorder and filter DataFrame columns
cols_order = ['job_title', 'company_name', 'city', 'province', 'country', 'date_posted']
df = df[cols_order]
df = df[df['job_title'].str.contains('Data')]

# Connect to Google Sheets API and update worksheet
scope = ['https://www.googleapis.com/auth/spreadsheets',
         "https://www.googleapis.com/auth/drive.file",
         "https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_name('D:/Projects/data-science-job-analysis/client_sheetsconection.json', scope)
client = gspread.authorize(creds)
spreadsheet = client.open('jobs_data')
worksheet = spreadsheet.worksheet('main_data')

# Combine new and existing data, drop duplicates, and update worksheet
existing_data = worksheet.get_values('2:10000')
old_df = pd.DataFrame(existing_data, columns=cols_order)

df = pd.concat([old_df, df], ignore_index=True)
df = df.drop_duplicates()

new_data = [cols_order] + df.values.tolist()
worksheet.clear()
worksheet.update(new_data)