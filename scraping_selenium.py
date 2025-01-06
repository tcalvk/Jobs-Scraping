# %%
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import random
import pandas as pd 
from urllib.parse import urlparse, parse_qs
from google.cloud import bigquery
import os 
from datetime import datetime, timezone

# %%
# Set up Chrome options
chrome_options = Options()
#chrome_options.add_argument("--headless")  # Run in headless mode
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("start-maximized")
chrome_options.add_argument("--incognito")  # Add Incognito mode
chrome_options.add_argument("disable-infobars")
chrome_options.add_argument("--disable-extensions")

# Path to ChromeDriver
driver_service = Service('/Users/tannerklein/Downloads/chromedriver-mac-arm64/chromedriver')

# Initialize the WebDriver
driver = webdriver.Chrome(service=driver_service, options=chrome_options)

# %%
# Define the target URL
url = "https://linkedin.com/login"
username = 'stephenburggraaf5@gmail.com'
password = 'ciXgig-7huxxu-gojpuk'
search_job_name = 'Data Engineer' 
search_job_location = 'United States'

# %%
# Open the page
driver.get(url)
time.sleep(random.uniform(2, 5))  # Random delay to mimic human behavior

# %%
username_input = driver.find_element(By.ID, "username")
password_input = driver.find_element(By.ID, "password")
login_button = driver.find_element(By.CLASS_NAME, "btn__primary--large")

username_input.send_keys(username)
password_input.send_keys(password)
login_button.click()

# %%
time.sleep(random.uniform(2, 5))  # Random delay to mimic human behavior
jobs_url = "https://linkedin.com/jobs"
driver.get(jobs_url)

# %%
time.sleep(random.uniform(1, 3)) 

job_name_element = driver.find_element(By.CSS_SELECTOR, "[id*='jobs-search-box-keyword-id-']")
job_name_html =  job_name_element.get_attribute('outerHTML')

job_name_split_list1 = job_name_html.split("class")
job_name_split_target1 = job_name_split_list1[0]
job_name_split_list2 = job_name_split_target1.split('"') 
job_name_input_element_id = job_name_split_list2[1]

job_name_split_list3 = job_name_input_element_id.split("-")
target_ending = job_name_split_list3[5]

job_location_input_element_id = 'jobs-search-box-location-id-' + target_ending
print(job_name_input_element_id)
print(job_location_input_element_id)

job_name_input = driver.find_element(By.ID, job_name_input_element_id)
job_location_input = driver.find_element(By.ID, job_location_input_element_id)


job_name_input.send_keys(search_job_name)
time.sleep(1)
job_location_input.clear()
job_location_input.send_keys(search_job_location)
time.sleep(1)
job_location_input.send_keys(Keys.ENTER)
time.sleep(5)

# %%
#define the dataframe in which to store the job data 
jobs_df = pd.DataFrame(columns=["job_id", "job_description", "created_at"])

# %%
#loop through page 1-10
for page_num in range(1,3):
    css_selector = f'li[data-test-pagination-page-btn="{page_num}"]'
    page_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, css_selector))
        )
    page_button.click()

    #attempt to find all of the job tiles on the linkedIn page
    try:
        # Wait for the <li> elements to load (with data-occludable-job-id attribute)
        li_elements = WebDriverWait(driver, 10).until(
            EC.presence_of_all_elements_located((By.CSS_SELECTOR, "li[data-occludable-job-id]"))
        )
        print(f"Found {len(li_elements)} elements")
    except Exception as e:
        print(f"Error: {e}")

    #loop through all of the job tiles and collect the job data 
    for li in li_elements:
        time.sleep(1)
        li.click()
        try:
            # Wait for the specific <div> element to load (adjust the wait time based on your page)
            div_element = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "div.jobs-box--fadein.jobs-box--full-width.jobs-box--with-cta-large.jobs-description.jobs-description--reformatted.job-details-module"))
            )

            # Extract the text from the <p> element
            div_text = div_element.get_attribute("textContent")

            #print(f"Extracted text from <p> tag within the <div>: {div_text}")

        except Exception as e:
            print(f"Error: {e}")

        #get the job_id 
        current_url = driver.current_url
        parsed_url = urlparse(current_url)
        query_params = parse_qs(parsed_url.query)
        job_id = query_params.get("currentJobId", [None])[0]
        #print(f"Value of current_job_id: {job_id}")

        #clean the job description text 
        job_description = div_text.replace("\n", " ").replace("\r", " ").replace("\t", " ")
        #print(job_description)

        utc_now = datetime.now(timezone.utc)

        # add the relational data to the df 
        new_row = {"job_id": job_id, "job_description": job_description, "created_at": utc_now}
        new_row_df = pd.DataFrame([new_row]) 
        jobs_df = pd.concat([jobs_df, new_row_df], ignore_index=True)
        print(jobs_df) 


# %%
#write to a csv file for testing
jobs_df.to_csv('/Users/tannerklein/Downloads/test_jobs_output.csv', index=False)

# %%
#write to bigquery dwh
credentials_path = '/Users/tannerklein/Library/Mobile Documents/com~apple~CloudDocs/Projects/Jobs Scraping/python_bq_private.json'
os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = credentials_path

client = bigquery.Client()
table_id = 'projects-portfolio-446806.prod_dwh.linkedin_scraped_jobs'

job = client.load_table_from_dataframe(jobs_df, table_id)
job.result()
print(f'Loaded {jobs_df.shape[0]} rows into {table_id}')


# %%
#close the driver 
#driver.quit()


