"""Collecting Jobs from Google Job Search"""

__author__ = "Refnhaldy Kristian"

# Importing libraries
import os
import re
import pandas as pd
import gspread

from oauth2client.service_account import ServiceAccountCredentials
from time import sleep
from datetime import datetime, timedelta
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.common.exceptions import WebDriverException
from selenium.webdriver.support import expected_conditions as EC

print('The script is running...')
# Empty list to store job results
job_results = []

# Default wait time for selenium
wait_time = 30

# List of job to search
job_searchs = ['data+analyst', 'data+scientist', 'data+engineer']

# Pre-defined final data column order
cols_order = ['date_posted', 'job_title', 'company_name', 'city', 'province', 'min_salary', 'max_salary', 'posted_via', 'job_type', 'description']

def setup_selenium():
    user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36"

    # Configure selenium
    options = webdriver.ChromeOptions()
    options.add_argument(f'user-agent={user_agent}')   # Set user agent
    options.add_argument('--no-sandbox')    # Disable the sandbox mode
    options.add_argument("--headless=new")    # Use the new headless mode after version 109
    options.add_argument('--disable-dev-shm-usage')    # Disable the dev-shm-usage
    driver = webdriver.Chrome(options=options)

    return driver

def load_all_jobs(driver, left_pane):
    # Scroll to the bottom of the list until all jobs are loaded
    all_jobs_loaded = False
    while not all_jobs_loaded:

        # Get old scroll height
        previous_scroll_height = driver.execute_script("return arguments[0].scrollHeight;", left_pane)

        # Scroll to bottom of the list (fetches more jobs)
        driver.execute_script("arguments[0].scrollTop = arguments[0].scrollHeight", left_pane)

        # Grant some time for messages to load
        sleep(1)

        # Get current scroll height
        current_scroll_height = driver.execute_script("return arguments[0].scrollHeight;", left_pane)
        # Check if all messages were loaded by comparing the scroll heights
        if current_scroll_height == previous_scroll_height:
            # Scroll back to top of the list to start collecting jobs
            driver.execute_script("arguments[0].scrollTop = 0", left_pane)
            all_jobs_loaded = True

def get_jobs(driver, left_pane):
    # Looping through jobs list
    for job in left_pane.find_elements(By.TAG_NAME, 'li'):
        # Clicking on the job
        job.click()

        # Getting job details
        # Extract details information
        job_title = job.find_element(By.CLASS_NAME, 'BjJfJf').text
        company_name = job.find_element(By.CLASS_NAME, 'vNEEBe').text
        location = job.find_element(By.CLASS_NAME, 'Qk80Jf').text
        # Extract details after via based on the value it contains
        details = job.find_element(By.CLASS_NAME, 'PwjeAc').text.split('\n')
        via = ''
        raw_date_posted = ''
        salary = ''
        job_type = ''
        for i in details:
            if 'melalui' in i:
                via = i
            elif 'yang' in i:
                raw_date_posted = i
            elif 'Rp' in i:
                salary = i
            else:
                job_type = i

        # Getting job description from right pane
        description_pane = driver.find_element(By.CLASS_NAME, 'whazf')
        # Try if description is expandable
        try:
            # Expand the description
            description_pane.find_element(By.CLASS_NAME, 'mjkhcd').click()
            WebDriverWait(driver, wait_time).until(EC.presence_of_element_located((By.CLASS_NAME, 'config-text-expandable')))
            description = description_pane.find_element(By.CLASS_NAME, 'config-text-expandable').text
        except WebDriverException:
            description = description_pane.find_element(By.CLASS_NAME, 'HBvzbc').text

        # Append to job_results
        job_results.append([job_title, company_name, location, via, raw_date_posted, salary, job_type, description])

def convert_salary(text):
    text = text.replace('Rp ', '').replace('.', '').replace(' rb', '000').replace('per bulan', '')
    if re.search(r'(\d),(\d{2}) jt', text):
        text = text.replace(' jt', '0000')
    elif re.search(r'(\d),(\d) jt', text):
        text = text.replace(' jt', '00000')
    else:
        text = text.replace(' jt', '000000')

    return int(text.replace(',', ''))

def prepare_clean_df(job_results):
    # Create dataframe
    df = pd.DataFrame(job_results, columns=['job_title', 'company_name', 'location', 'via', 'raw_date_posted', 'salary', 'job_type', 'description'])
    df = df.drop_duplicates(subset=['job_title', 'company_name', 'location', 'via', 'salary'])

    # Clean and Standardize Data
    # Convert raw_date_posted to correct dd/mm/yyyy format
    df['date_posted'] = pd.to_datetime(df['raw_date_posted'].apply(lambda x: datetime.today().date() - timedelta(days=int(x.split(' ')[0])) if 'hari' in x else datetime.today().date() if 'jam' in x else '' if 'bulan' in x else x))
    # Remove 'melalu' from via column
    df['posted_via'] = df['via'].str.replace('melalui', '')
    # Remove '(+n lainnya)' from location column using regex
    df['location'] = df['location'].apply(lambda x: re.sub(r' \(\+\d+ lainnya\)', '', x))
    # Get the city from location column
    df['city'] = df['location'].apply(lambda x: x.split(',')[0] if x != '' else x)
    df['city'] = df['city'].str.replace('Kota ', '').str.replace('Kab. ', '').str.replace('Kabupaten ', '')
    # Get the province from location column
    df['province'] = df['location'].apply(lambda x: x.split(',')[-1].strip() if x != '' else x)
    # Clean Salary
    # Drop row if salary contain 'per hari' or 'per tahun'
    df = df[~df['salary'].str.contains('per hari|per tahun')]
    # Split salary into min_salary & max_salary
    df['min_salary'] = df['salary'].apply(lambda x: convert_salary(x.split('–')[0]) if '–' in x else convert_salary(x) if x !='' else x)
    df['max_salary'] = df['salary'].apply(lambda x: convert_salary(x.split('–')[1]) if '–' in x else convert_salary(x) if x !='' else x)

    # Reorder the data
    df = df[cols_order].sort_values(by=['date_posted'], ascending=False).astype(str).replace('NaT', '')

    return df

def update_worksheet(final_df):
    # Connect to Google Sheets API and update worksheet
    scope = ['https://www.googleapis.com/auth/spreadsheets',
            "https://www.googleapis.com/auth/drive.file",
            "https://www.googleapis.com/auth/drive"]
    keyfile_path = os.path.join(os.getcwd(), 'credentials.json')
    creds = ServiceAccountCredentials.from_json_keyfile_name(keyfile_path, scope)
    client = gspread.authorize(creds)
    spreadsheet = client.open('jobs_data')
    worksheet = spreadsheet.worksheet('selenium_data')

    # Combine new and existing data, drop duplicates & reorder
    existing_data = worksheet.get_all_values()
    existing_df = pd.DataFrame(existing_data[1:], columns=existing_data[0])
    combined_df = pd.concat([existing_df, final_df]).drop_duplicates(subset=['job_title', 'company_name', 'city'])
    combined_df = combined_df.sort_values(by='date_posted', ascending=False, ignore_index=True)

    # Update data in worksheet
    new_data = [cols_order] + final_df.values.tolist()
    worksheet.clear()
    worksheet.update(range_name='A1', values=new_data, value_input_option='USER_ENTERED')

# Main Script
def main():
    # Start the script
    driver = setup_selenium()

    # Loop Through Job Search
    for job in job_searchs:
        driver.get(f'https://www.google.com/search?q={job}&ibp=htl;jobs#htivrt=jobs&fpstate=tldetail&htilrad=-1.0&htidocid')

        # Wait for the page to load
        WebDriverWait(driver, wait_time).until(EC.presence_of_element_located((By.TAG_NAME, 'li')))
        left_pane = driver.find_element(By.CLASS_NAME, 'zxU94d')
        load_all_jobs(driver, left_pane)
        get_jobs(driver, left_pane)
        print(f'The data for {job} has been succesfully collected!')

    # Close the browser
    driver.quit()

    print('Preparing the data...')
    # Prepare the dataframe
    final_df = prepare_clean_df(job_results)
    print('Update the data to Google Sheets...')
    update_worksheet(final_df)

    print('The data has been succesfully updated!')

if __name__ == "__main__":
    main()