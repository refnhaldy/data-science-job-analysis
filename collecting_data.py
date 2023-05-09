import pandas as pd
import itertools
import requests
import gspread

from indodata import *
from myfunction import *
from bs4 import BeautifulSoup
from oauth2client.service_account import ServiceAccountCredentials

# Set search terms
terms = ['Data Engineer', 'Data Scientist', 'Data Analyst']

def scrape_linkedin(terms, provinces):
    # Initialize variables to store data
    linkedin_data = []

    # Loop through all possible combinations of terms and provinces on Linkedin
    for term, province in itertools.product(terms, provinces):
        term = term.replace(' ', '%20')
        province = province.replace(' ', '%20')
        linkedin_url = f'https://www.linkedin.com/jobs/search?keywords={term}&location={province}&locationId=&geoId=&f_TPR=&position=1&pageNum=0'
        # Set headers to get LinkedIn page in Bahasa Indonesia
        headers = {'Accept-Language': 'id-ID,id;q=0.9,en-US;q=0.8,en;q=0.7'}
        
        try:
            response = requests.get(linkedin_url, headers=headers)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')
            jobs_container = soup.find('ul', 'jobs-search__results-list')
            jobs = jobs_container.find_all('li')
        except (requests.exceptions.HTTPError, ValueError):
            continue
            
        if jobs_container is None:
            continue
        
        # Get job information
        for job in jobs:
            job_title = job.find('h3', 'base-search-card__title').text.strip()
            company_name = job.find('h4', 'base-search-card__subtitle').text.strip()
            city = job.find('span', 'job-search-card__location').text.strip()
            date_posted = job.find('time', 'job-search-card__listdate')

            date_posted = date_posted.get('datetime') if date_posted else None

            salary = None
            description = None

            # Add job information to data list
            linkedin_data.append([job_title, company_name, city, salary, description, date_posted])

    return linkedin_data

def scrape_jobstreet(terms):
    # Initialize variables to store data
    jobstreet_data = []

    # Loop through all possible combinations of terms and provinces on Jobsteet
    for term in terms:
        term = term.replace(' ', '-').lower()
        jobstreet_url = f'https://www.jobstreet.co.id/id/job-search/{term}-jobs/'
        
        page = 1

        while True:
            try:
                response = requests.get(jobstreet_url)
                response.raise_for_status()
                soup = BeautifulSoup(response.text, 'html.parser')
                jobs = soup.find_all('article')

            except (requests.exceptions.HTTPError, ValueError):
                continue # Go to the next loop if bad response
            
            for job in jobs:
                job_title = job.find('h1').get_text()
                company_name = job.find('span', 'y44q7i1').get_text()
                city = job.find('span', 'y44q7i3').get_text()

                salary_element = job.find_all('span', 'y44q7i3')
                description_element = job.find_all('li')
                date_element = job.find('time')
                
                salary = salary_element[1].text.strip() if len(salary_element) > 1 else None
                description = ', '.join(e.text.strip() for e in description_element)
                date_posted = date_element.get('datetime') if date_element else None

                # Add job information to data list
                jobstreet_data.append([job_title, company_name, city, salary, description, date_posted])

            if len(jobs) < 30:
                break

            page += 1
            jobstreet_url = f'https://www.jobstreet.co.id/id/job-search/{term}-jobs/{page}/'

    return jobstreet_data

# Get the data from multiple website and combined the data
linkedin_data = scrape_linkedin(terms, provinces)
jobstreet_data = scrape_jobstreet(terms)
all_data = linkedin_data + jobstreet_data

# Into the dataframe
columns = ['job_title', 'company_name', 'city', 'monthly_salary', 'description', 'date_posted']
df = pd.DataFrame(all_data, columns=columns)

# Filter and clean data
like_cities = '|'.join(city_list) + '|Jakarta'
df = df[df['city'].str.contains(like_cities)]
df['city'] = df['city'].apply(map_city)
# Remove extra info from date_posted
df['date_posted'] = df['date_posted'].str.split('T').str[0]
# Remove unwanted characters and extract the desired substring
df['monthly_salary'] = df['monthly_salary'].str.replace('M', '.000.000')
df['monthly_salary'] = df['monthly_salary'].str.replace('  per bulan', '')

# Create new columns and assign value based on the city column
df['province'] = df['city'].apply(get_province)
df['country'] = df['province'].apply(get_country)

# Reorder and filter DataFrame columns
cols_order = ['job_title', 'company_name', 'city', 'province', 'country', 'monthly_salary', 'description', 'date_posted']
df = df[cols_order]
df = df[df['job_title'].str.contains('Data')]

# Connect to Google Sheets API and update worksheet
scope = ['https://www.googleapis.com/auth/spreadsheets',
         "https://www.googleapis.com/auth/drive.file",
         "https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_name('credentials.json', scope)
client = gspread.authorize(creds)
spreadsheet = client.open('jobs_data')
worksheet = spreadsheet.worksheet('main_data')

# Combine new and existing data, drop duplicates & reorder
existing_data = worksheet.get_all_values()
old_df = pd.DataFrame(existing_data[1:], columns=existing_data[0])
combined_df = pd.concat([old_df, df]).drop_duplicates(subset=['job_title', 'company_name', 'city'])
combined_df = combined_df.sort_values(by='date_posted', ascending=False, ignore_index=True)

# Update data in worksheet
new_data = [cols_order] + df.values.tolist()
worksheet.clear()
worksheet.update(new_data)