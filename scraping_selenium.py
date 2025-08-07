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
from dotenv import load_dotenv
load_dotenv()

# Set up Chrome options
chrome_options = Options()
#chrome_options.add_argument("--headless")  # Run in headless mode
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("start-maximized")
chrome_options.add_argument("--incognito")  # Add Incognito mode
chrome_options.add_argument("disable-infobars")
chrome_options.add_argument("--disable-extensions")

# %%
# Define the target URL
url = "https://linkedin.com/login"
username = 'stephenburggraaf5@gmail.com'
password = 'ciXgig-7huxxu-gojpuk'
search_job_name = 'Data Engineer' 
search_job_location = 'United States'
search_criteria = search_job_name + ' in ' + search_job_location
jobs_url = "https://linkedin.com/jobs"

# Path to ChromeDriver
driver_path = os.getenv("DRIVER_PATH")
driver_service = Service(driver_path)
# Initialize the WebDriver
driver = webdriver.Chrome(service=driver_service, options=chrome_options)

def login_and_search():
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

    job_name_input.send_keys(search_criteria)
    time.sleep(1)
    job_name_input.send_keys(Keys.ENTER)
    time.sleep(2)

def loop_and_save_jobs():
    #define the dataframe in which to store the job data 
    jobs_df = pd.DataFrame(
        columns=[
            "job_id", 
            "job_description", 
            "created_at",
            "search_term",
            "job_location",
            "job_title",
            "listing_details",
            "fit_level_preferences"
            ]
        )
    # %%
    for page_num in range(1, 11):  # Start from page 1
        try:
            # First, scrape job tiles on the current page
            li_elements = WebDriverWait(driver, 10).until(
                EC.presence_of_all_elements_located((By.CSS_SELECTOR, "ul.semantic-search-results-list > li"))
            )
            print(f"Page {page_num}: Found {len(li_elements)} job tiles")

            for li in li_elements:
                time.sleep(1)
                li.click()

                # get description
                try:
                    div_element = WebDriverWait(driver, 10).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, "div.jobs-box--fadein.jobs-box--full-width.jobs-box--with-cta-large.jobs-description.jobs-description--reformatted.job-details-module"))
                    )
                    div_text = div_element.get_attribute("textContent")
                except Exception as e:
                    print(f"Error retrieving job description: {e}")
                    div_text = ""

                # get job title 
                try:
                    job_title_element = WebDriverWait(driver, 10).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, "div.job-details-jobs-unified-top-card__job-title a"))
                    )
                    job_title_text = job_title_element.get_attribute("textContent")
                except Exception as e:
                    print(f"Error retrieving job title: {e}")

                # get listing details 
                try:
                    listing_details_element = WebDriverWait(driver, 10).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, "div.job-details-jobs-unified-top-card__tertiary-description-container"))
                    )
                    listing_details = listing_details_element.get_attribute("textContent")
                except Exception as e:
                    print(f"Error retrieving header text: {e}") 

                 # get fit level preferences 
                try:
                    fit_level_pref_element = WebDriverWait(driver, 10).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, "div.job-details-fit-level-preferences"))
                    )
                    fit_level_pref = fit_level_pref_element.get_attribute("textContent")
                except Exception as e:
                    print(f"Error retrieving header text: {e}")  

                current_url = driver.current_url
                parsed_url = urlparse(current_url)
                query_params = parse_qs(parsed_url.query)
                job_id = query_params.get("currentJobId", [None])[0]
                job_description = div_text.replace("\n", " ").replace("\r", " ").replace("\t", " ")
                utc_now = datetime.now(timezone.utc)

                new_row = {"job_id": job_id, "job_description": job_description, "created_at": utc_now, "search_term": search_job_name, "job_location": search_job_location, "job_title": job_title_text, "listing_details": listing_details, "fit_level_preferences": fit_level_pref}
                jobs_df = pd.concat([jobs_df, pd.DataFrame([new_row])], ignore_index=True)

        except Exception as e:
            print(f"Error scraping page {page_num}: {e}")
            break

        # Then go to next page
        try:
            next_button = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, 'button[aria-label="View next page"]'))
            )
            next_button.click()
            print(f"Clicked 'Next' to go to page {page_num + 1}")
            time.sleep(random.uniform(2, 4))  # Allow the new page to load
        except Exception as e:
            print(f"No more pages after page {page_num}: {e}")
            break

    return jobs_df

def upload_to_bq(jobs_df):
    # %%
    #write to a csv file for testing
    #jobs_df.to_csv('/Users/tannerklein/Downloads/test_jobs_output.csv', index=False)

    # %%
    #write to bigquery dwh
    credentials_path = os.getenv("CREDENTIALS_PATH")
    os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = credentials_path

    client = bigquery.Client()
    table_id = os.getenv("TABLE_ID")

    job = client.load_table_from_dataframe(jobs_df, table_id)
    job.result()
    print(f'Loaded {jobs_df.shape[0]} rows into {table_id}')


def quit_driver():
    #close the driver 
    driver.quit()



def main():
    print("Hello from main")
    login = login_and_search()
    jobs_df = loop_and_save_jobs()
    upload = upload_to_bq(jobs_df)
    quit = quit_driver()



if __name__ == "__main__":
    main()


