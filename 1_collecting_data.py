__version__ = "0.1.0"

import pandas as pd
import itertools
import requests
import gspread

from bs4 import BeautifulSoup
from oauth2client.service_account import ServiceAccountCredentials

def map_province(prov):
    for p in provinces_en:
        if p in prov:
            return provinces_dict.get(p, prov)
    return prov

# Get list of cities in indonesian from Wikipedia
url = 'https://id.wikipedia.org/wiki/Daftar_kota_di_Indonesia_menurut_jumlah_penduduk'
table = pd.read_html(url)[0]
provinces = list(table['Provinsi'].unique())

# Get list of cities in english from Wikipedia
url_en = 'https://en.wikipedia.org/wiki/List_of_Indonesian_cities_by_population'
table_en = pd.read_html(url_en)[1]
provinces_en = list(table_en['Province'].unique())

# Set search terms
terms = ['Data%20Engineer', 'Data%20Scientist', 'Data%20Analyst']

# Initialize variables
data = []

# Loop through all possible combinations of terms and cities
for term, province in itertools.product(terms, provinces):
    province = province.replace(' ', '%20')
    url = f'https://www.linkedin.com/jobs/search?keywords={term}&location={province}&locationId=&geoId=&f_TPR=&position=1&pageNum=0'

    try:
        response = requests.get(url)
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
        job_location = job.find('span', 'job-search-card__location').text.strip()
        date_posted = job.find('time', 'job-search-card__listdate')

        date_posted = date_posted.get('datetime') if date_posted else None

        # Add job information to data list
        data.append([job_title, company_name, job_location, date_posted])

# Create pandas DataFrame from data list
columns = ['job_title', 'company_name', 'job_location', 'date_posted']
df = pd.DataFrame(data, columns=columns)

# Split job location into city, province, and country
df['job_location'] = df['job_location'].str.replace(', ', ',')
df[['city', 'province', 'country']] = df['job_location'].str.split(',', expand=True)

# Reorder and filter DataFrame columns
cols_order = ['job_title', 'company_name', 'city', 'province', 'country', 'date_posted']
df = df[cols_order]
df = df[df['job_title'].str.contains('Data')]

# Create custom cities list for mapping values
provinces_dict = {}
for key, val in zip(provinces_en, provinces):
    if key == 'Special Capital Region of Jakarta':
        new_key = 'Jakarta'
    elif key == 'Special Region of Yogyakarta':
        new_key = 'Yogyakarta'
    else:
        new_key = key
    
    if val == 'Daerah Khusus Ibukota Jakarta':
        new_val = 'Jakarta'
    elif val == 'Daerah Istimewa Yogyakarta':
        new_val = 'Yogyakarta'
    else:
        new_val = val
    
    provinces_dict[new_key] = new_val

# Map province names to Indonesian
df['province'] = df['province'].apply(map_province)

# Connect to Google Sheets API and update worksheet
scope = ['https://www.googleapis.com/auth/spreadsheets',
         "https://www.googleapis.com/auth/drive.file",
         "https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_name('D:/Projects/analysis-jobs-listing/client_sheetsconection.json', scope)
client = gspread.authorize(creds)
spreadsheet = client.open('jobs_data_test')
worksheet = spreadsheet.worksheet('Sheet1')

# Combine new and existing data, drop duplicates, and update worksheet
existing_data = worksheet.get_values('2:10000')
old_df = pd.DataFrame(existing_data, columns=cols_order)
df = pd.concat([old_df, df], ignore_index=True)
df = df.drop_duplicates()
new_data = [cols_order] + df.values.tolist()
worksheet.clear()
worksheet.update(new_data)