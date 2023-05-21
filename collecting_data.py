import os
import pandas as pd
import requests
import gspread

from indodata import *
from myfunction import *
from bs4 import BeautifulSoup
from oauth2client.service_account import ServiceAccountCredentials

def scrape_linkedin(terms):
    # Initialize variables to store data
    linkedin_data = []

    # Loop through all possible combinations of terms and provinces on Linkedin
    for term in terms:
        term = term.replace(' ', '%2B')
        linkedin_url = f'https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search?keywords={term}&location=Indonesia&geoId=&trk=public_jobs_jobs-search-bar_search-submit&start=0'
        # Set headers to get LinkedIn page in Bahasa Indonesia
        headers = {'Accept-Language': 'id-ID,id;q=0.9,en-US;q=0.8,en;q=0.7'}
        
        page = 0

        while True:
            try:
                response = requests.get(linkedin_url, headers=headers)
                response.raise_for_status()
                soup = BeautifulSoup(response.text, 'html.parser')
                jobs = soup.find_all('li')
            except (requests.exceptions.HTTPError, ValueError):
                break  # Break the loop if there is an error

            # Get job information
            for job in jobs:
                job_title = job.find('h3', 'base-search-card__title').text.strip()
                company_name = job.find('h4', 'base-search-card__subtitle').text.strip()
                city = job.find('span', 'job-search-card__location').text.strip()

                date_posted = job.find('time', 'job-search-card__listdate')
                salary_element = job.find('span', 'job-search-card__salary-info')

                description = None

                via = 'LinkedIn'
                salary = salary_element.text.strip() if salary_element else None
                salary = salary.replace('\n            -\n            IDR', ' - ') if salary else None
                date_posted = date_posted.get('datetime') if date_posted else None

                # Add job information to data list
                linkedin_data.append([job_title, company_name, city, salary, description, via, date_posted])
                
            # Break the loop if there are less than 25 jobs in the page or the page reaches 975
            if len(jobs) < 25 or page == 975:
                break

            page += 25
            linkedin_url = f'https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search?keywords={term}&location=Indonesia&geoId=&trk=public_jobs_jobs-search-bar_search-submit&start={page}'

    print(len(linkedin_data), 'data from LinkedIn has been successfully retrieved!')
    return linkedin_data

def scrape_jobstreet(terms):
    # Initialize variables to store data
    jobstreet_data = []

    # Loop through all possible combinations of terms and provinces on Jobsteet
    for term in terms:
        term = term.replace(' ', '-')
        jobstreet_url = f'https://www.jobstreet.co.id/id/job-search/{term}-jobs/'
        
        page = 1

        while True:
            try:
                response = requests.get(jobstreet_url)
                response.raise_for_status()
                soup = BeautifulSoup(response.text, 'html.parser')
                jobs = soup.find_all('article')

            except (requests.exceptions.HTTPError, ValueError):
                break # Break the loop if there is an error
            
            for job in jobs:
                job_title = job.find('h1').get_text()
                company_name = job.find('span', 'y44q7i1').get_text()

                double_element = job.find_all('span', 'y44q7i3')
                description_element = job.find_all('li')
                date_element = job.find('time')
                
                city = double_element[0].get_text()
                salary = double_element[1].text.strip() if len(double_element) > 1 else None
                salary = salary.replace('M', '.000.000') if salary else None
                description = ', '.join(e.text.strip() for e in description_element)
                via = 'Jobstreet'
                date_posted = date_element.get('datetime').split('T')[0] if date_element else None

                # Add job information to data list
                jobstreet_data.append([job_title, company_name, city, salary, description, via, date_posted])

            # Break the loop if there are less than 30 jobs in the page
            if len(jobs) < 30:
                break

            page += 1
            jobstreet_url = f'https://www.jobstreet.co.id/id/job-search/{term}-jobs/{page}/'

    print(len(jobstreet_data), 'data from JobStreet has been successfully retrieved!')
    return jobstreet_data

# Set search terms
terms = ['data engineer', 'data scientist', 'data analyst']

# Get the data from multiple website and combined the data
linkedin_data = scrape_linkedin(terms)
jobstreet_data = scrape_jobstreet(terms)
all_data = linkedin_data + jobstreet_data
print('The data from multiple websites has been succesfully combined!')

# Into the dataframe
columns = ['job_title', 'company_name', 'city', 'monthly_salary', 'description', 'via', 'date_posted']
df = pd.DataFrame(all_data, columns=columns)

# Filter and clean data
like_cities = '|'.join(city_list) + '|Jakarta'
df = df[df['job_title'].str.contains('Data')]
df = df[df['city'].str.contains(like_cities)]
df['city'] = df['city'].apply(map_city)
print('The data has been succesfully filtered!')

# Remove unwanted characters and extract the desired substring
df['monthly_salary'] = df['monthly_salary'].str.replace('  per bulan', '')
df['monthly_salary'] = df['monthly_salary'].str.replace(',00', '')
df['monthly_salary'] = df['monthly_salary'].str.replace('IDR', '')
df['monthly_salary'] = df['monthly_salary'].str.replace('.5.0', '.5')
df['monthly_salary'] = df['monthly_salary'].str.strip()
print('The data has been succesfully standardized!')

# Create new columns and assign value based on the city column
df['province'] = df['city'].apply(get_province)
df['country'] = df['province'].apply(get_country)
print('Province & Country has been succesfully added to the data!')

# Reorder and filter DataFrame columns
cols_order = ['job_title', 'company_name', 'city', 'province', 'country', 'monthly_salary', 'description', 'via', 'date_posted']
df = df[cols_order]
print('The data has been succesfully reodered!')

# Connect to Google Sheets API and update worksheet
scope = ['https://www.googleapis.com/auth/spreadsheets',
         "https://www.googleapis.com/auth/drive.file",
         "https://www.googleapis.com/auth/drive"]

# Get the directory path of credentials.json
current_dir = os.path.dirname(__file__)
keyfile_path = current_dir + '\credentials.json'
creds = ServiceAccountCredentials.from_json_keyfile_name(keyfile_path, scope)

client = gspread.authorize(creds)
spreadsheet = client.open('jobs_data')
worksheet = spreadsheet.worksheet('main_data')
print('Google worksheets has been succesfully connected!')

# Combine new and existing data, drop duplicates & reorder
existing_data = worksheet.get_all_values()
old_df = pd.DataFrame(existing_data[1:], columns=existing_data[0])
combined_df = pd.concat([old_df, df]).drop_duplicates(subset=['job_title', 'company_name', 'city'])
combined_df = combined_df.sort_values(by='date_posted', ascending=False, ignore_index=True)
print('Combined dataframe has been succesfully created!')

# Update data in worksheet
new_data = [cols_order] + combined_df.values.tolist()
worksheet.clear()
worksheet.update(new_data)
new_calc_data = len(combined_df) - len(old_df)
print(f'Success to add {new_calc_data} data to google sheets!')