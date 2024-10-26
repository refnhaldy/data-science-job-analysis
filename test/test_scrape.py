"""Collecting Jobs from Google Job Search"""

__author__ = "Refnhaldy Kristian"
__version__ = "2.0.0"

import os
import re
from time import sleep
from datetime import date, datetime, timedelta

import pandas as pd
import sqlalchemy as db
from dotenv import load_dotenv
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.support import expected_conditions as EC

def get_state():
    # Get Indonesia geographical data from Wikipedia
    url = "https://id.wikipedia.org/wiki/Provinsi_di_Indonesia"

    try:
        df_city = pd.read_html(url)[2]
    except Exception as e:
        print(f"Error retrieving data from {url}: {e}")
        exit()
        
    states = df_city["Provinsi"].values.tolist()
    states = [state[0] for state in states]

    return states

def setup_selenium():
    user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36"

    # Configure selenium
    options = webdriver.ChromeOptions()
    options.add_argument(f"user-agent={user_agent}")   # Set user agent
    options.add_argument("--no-sandbox")    # Disable the sandbox mode
    options.add_argument("--headless=new")    # Use the new headless mode after version 109
    options.add_argument("--disable-dev-shm-usage")    # Disable the dev-shm-usage
    driver = webdriver.Chrome(options=options)

    return driver

def load_page(driver):
    # Scroll to the bottom of the list until all jobs are loaded
    all_jobs_loaded = False
    while not all_jobs_loaded:

        # Get old scroll height
        old_height = driver.execute_script("return document.body.scrollHeight")

        # Scroll to bottom of the list (fetches more jobs)
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")

        # Grant some time for listing to load
        sleep(1)

        # Get current scroll height
        new_height = driver.execute_script("return document.body.scrollHeight")

        # Check if all list were loaded by comparing the scroll heights
        if new_height == old_height:
            # Scroll back to top of the list to start collecting jobs
            driver.execute_script("window.scrollTo(0, 0);")
            all_jobs_loaded = True

def get_listing(driver: webdriver.Chrome):
    list_data = []
    today = datetime.today()

    # Check wheter class v3jTId is exist in the dom
    try:
        driver.find_element(By.CLASS_NAME, "v3jTId")
        print("No job listing found")
        return pd.DataFrame()
    except:
        pass
        
    # Looping through jobs list
    for job in driver.find_elements(By.CLASS_NAME, "EimVGf"):
        # Get job details
        primary: list[str] = job.find_element(By.CLASS_NAME, "u9g6vf").text.split("\n")
        secondary: list[str] = job.find_element(By.CLASS_NAME, "ApHyTb").text.split("\n")
        job_title: str = primary[0]
        company_name: str = primary[1]
        index_2: list[str] = primary[2].split("•")
        via: str = index_2[-1].replace("melalui", "")
        contract: str | None = secondary[-1] if secondary[-1] in ["Kontraktor", "Pekerjaan tetap", "Paruh waktu", "Magang"] else None

        # Initialize variables
        location: str = ""
        city: str = ""
        mapped_city: str = ""
        salary_range: str = ""
        posted_at: str = ""
        date_posted: date | None = None
        min_monthly_salary: float = 0.00
        max_monthly_salary: float = 0.00
        min_daily_salary: float = 0.00
        max_daily_salary: float = 0.00
        min_hourly_salary: float = 0.00
        max_hourly_salary: float = 0.00

        # Uncertain index_2 data
        if len(index_2) > 1:
            location = index_2[0]

        # Uncertain location data
        if len(location) > 1:
            location_list = location.split(",")
            if len(location_list) > 1:
                city = location_list[-2]

        # Uncertain secondary data
        if len(secondary) > 2:
            posted_at = secondary[0]
            salary_range = secondary[1]
        elif len(secondary) > 1:
            if "jt" in secondary[0]:
                salary_range = secondary[0]
            elif "hari" in secondary[0] or "jam" in secondary[0]:
                posted_at = secondary[0]

        # Handle posted_at
        if "hari yang lalu" in posted_at:
            offset = int(posted_at[0])
            date_posted = (today - timedelta(days=offset)).date()
        elif "jam yang lalu" in posted_at:
            offset = int(posted_at[0])
            date_posted = (today - timedelta(hours=offset)).date()

        # Handle salary_range
        if "jt per bulan" in salary_range:
            salary_range = salary_range.replace(",", ".")
            min_monthly_salary = float(re.findall(r"\d+(?:.\d+)?", salary_range)[0]) * 1_000_000
            max_monthly_salary = float(re.findall(r"\d+(?:.\d+)?", salary_range)[-1]) * 1_000_000
            min_daily_salary = min_monthly_salary / 22
            max_daily_salary = max_monthly_salary / 22
            min_hourly_salary = min_daily_salary / 8
            max_hourly_salary = max_daily_salary / 8
        elif "jt per hari" in salary_range:
            salary_range = salary_range.replace(",", ".")
            min_daily_salary = float(re.findall(r"\d+(?:.\d+)?", salary_range)[0]) * 1_000_000
            max_daily_salary = float(re.findall(r"\d+(?:.\d+)?", salary_range)[-1]) * 1_000_000
            min_monthly_salary = min_daily_salary * 22
            max_monthly_salary = max_daily_salary * 22
            min_hourly_salary = min_daily_salary / 8
            max_hourly_salary = max_daily_salary / 8

        # Handle location
        if "Kota " in city or "Kabupaten " in city:
            mapped_city = city.replace("Kota ", "").replace("Kabupaten ", "")
        else:
            mapped_city = city

        data = {
            "index_2": index_2,
            "date_collected": today.date(),
            "date_posted": date_posted,
            "search_category": "",
            "job_title": job_title.strip(),
            "company_name": company_name.strip(),
            "location": location.strip(),
            "city": city.strip(),
            "mapped_city": mapped_city.strip(),
            "via": via.strip(),
            "contract": contract,
            "salary_range": salary_range.strip(),
            "min_monthly_salary": min_monthly_salary,
            "max_monthly_salary": max_monthly_salary,
            "min_daily_salary": min_daily_salary,
            "max_daily_salary": max_daily_salary,
            "min_hourly_salary": min_hourly_salary,
            "max_hourly_salary": max_hourly_salary
        }
        
        # Append data to list
        list_data.append(data)
    
    df_listing = pd.DataFrame(list_data)

    return df_listing

def update_data(df_final: pd.DataFrame):
    # Set up the database connection
    load_dotenv()
    DB_USER = os.getenv("DB_USER")
    DB_PASS = os.getenv("DB_PASS")
    DB_HOST = os.getenv("DB_HOST")
    DB_PORT = os.getenv("DB_PORT")

    # Create the connection
    engine = db.create_engine(f"postgresql://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/postgres")

    # Get previous data from database
    df_old = pd.read_sql("SELECT job_title, company_name, mapped_city, via FROM public.job_listing", engine)

    # Remove rows from df_final that are already in df_old
    df_final = pd.merge(df_final, df_old, on=["job_title", "company_name", "mapped_city", "via"], how="left", indicator=True)
    df_final = df_final[df_final["_merge"] == "left_only"].drop(columns=["_merge"])

    # Save the data to the database
    df_final.drop_duplicates(subset=["job_title", "company_name", "mapped_city", "via"], inplace=True)
    df_final.to_sql("job_listing", engine, if_exists="append", index=False)
    
    print(f"{len(df_final)} data has been succesfully added!")


# Main Script
def main():
    searchs = ["Data+Analyst", "Data+Engineer", "Data+Scientist"]
    driver = setup_selenium()
    df_final = pd.DataFrame()

    for search in searchs:
        driver.get(f"https://www.google.com/search?q={search}+Indonesia&ibp=htl;jobs#htivrt=jobs&fpstate=tldetail&htilrad=-1.0&htidocid")

        try:
            WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.CLASS_NAME, "EimVGf")))
            load_page(driver)
            df_listing = get_listing(driver)
            df_listing["search_category"] = search.replace("+", " ")
            df_final = pd.concat([df_final, df_listing], ignore_index=True)
            print(f"Succesfully get {search} data")
        except TimeoutException:
            print(f"Request time out while waiting {search} to load")

    # Close the browser
    driver.quit()
    
    # Update the data
    update_data(df_final)