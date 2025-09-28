# Copyright (c) 2024 roperi

import os
import sys
import time
from datetime import datetime
import logging
import random
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from utils.job_helpers import parse_job_details
from utils.database import create_db, connect_to_db
from settings import config


# LOGGING

# Create logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
# Get paths
scriptdir = os.path.dirname(os.path.abspath(__file__))
logdir = os.path.join(scriptdir, 'log')
if not os.path.exists(logdir):
    os.makedirs(logdir)
mypath = os.path.join(logdir, 'upwork_best_matches_scraper.log')
# Create file handler which logs even DEBUG messages
fh = logging.FileHandler(mypath)
fh.setLevel(logging.DEBUG)
# Create console handler
ch = logging.StreamHandler(sys.stdout)
ch.setLevel(logging.DEBUG)
# create formatter and add it to the handlers
formatter = logging.Formatter('[%(levelname)s. %(name)s, (line #%(lineno)d) - %(asctime)s] %(message)s')
fh.setFormatter(formatter)
ch.setFormatter(formatter)
# add handlers to logger
logger.addHandler(fh)
logger.addHandler(ch)


# FUNCTIONS

def get_driver_with_retry(chrome_versions, max_attempts=3, headless=True):
    """
    Simplified driver creation based on working test configuration
    """
    logger.info("Creating Chrome driver...")
    
    for attempt in range(max_attempts):
        try:
            logger.info(f'Attempt #{attempt+1}/{max_attempts}')
            options = uc.ChromeOptions()
            
            # Use the same minimal options that worked in the test
            options.add_argument('--no-sandbox')
            options.add_argument('--disable-dev-shm-usage')
            
            # Use a different port to avoid conflicts with existing Chrome instances
            debug_port = random.randint(9000, 9999)
            options.add_argument(f'--remote-debugging-port={debug_port}')
            
            if headless:
                options.add_argument('--headless')
                options.add_argument('--disable-gpu')
                options.add_argument('--window-size=1920,1080')
            
            # Disable some features that might cause issues
            options.add_argument('--disable-extensions')
            options.add_argument('--disable-plugins')
            options.add_argument('--disable-web-security')
            
            logger.info(f"Using debug port: {debug_port}")
            
            # Let undetected_chromedriver auto-detect the version
            driver = uc.Chrome(options=options)
            
            logger.info(f"Successfully launched Chrome driver (version: {driver.capabilities.get('browserVersion', 'Unknown')})")
            return driver
            
        except Exception as e:
            error_msg = str(e)
            logger.error(f"Attempt {attempt+1} failed: {error_msg[:200]}...")
            
            # If it's a port conflict, try a different approach
            if "cannot connect to chrome" in error_msg.lower():
                logger.warning("Port conflict detected, trying different port...")
            
            if attempt < max_attempts - 1:
                logger.info("Retrying in 3 seconds...")
                time.sleep(3)
            continue
                
    logger.error("All attempts failed. Unable to launch Chrome driver.")
    return None


def check_environment():
    """
    Check if running in an EC2/headless environment and log system information.
    """
    import platform
    logger.info(f"System: {platform.system()} {platform.release()}")
    logger.info(f"Python version: {platform.python_version()}")
    
    # Check if display is available
    display_available = os.environ.get('DISPLAY') is not None
    logger.info(f"Display available: {display_available}")
    
    # Check if running in EC2
    try:
        import requests
        response = requests.get('http://169.254.169.254/latest/meta-data/instance-id', timeout=2)
        if response.status_code == 200:
            logger.info("Running on AWS EC2 instance")
            return True
    except:
        pass
    
    logger.info("Not running on AWS EC2 or EC2 metadata service unavailable")
    return False


def main():
    """
    Main function for scraping job postings from Upwork.

    Returns:
        bool: True if the scraping process completed successfully, False otherwise.

    This function connects to the database, configures the web driver, logs into site, and then starts an infinite loop
    to continuously scrape job postings. It scrolls down the page to load more job postings, extracts job details, and
    stores them in the database. It refreshes the browser after each scraping cycle and pauses for the specified number
    of hours before continuing to the next cycle. If an error occurs during the scraping process, it prints the error
    message and returns False.
    """
    try:
        # Check environment
        is_ec2 = check_environment()
        # Connect to database
        conn, cursor = connect_to_db()

        # Create table (if it does not exist)
        create_db(conn, cursor)

        # Configure the undetected_chromedriver options
        logger.info('Launching driver')
        driver = get_driver_with_retry(
            chrome_versions=config.CHROME_VERSIONS, 
            max_attempts=config.MAX_ATTEMPTS,
            headless=True  # Use headless mode to avoid conflicts with existing Chrome
        )

        if driver:
            # Login
            user_login_page = 'https://www.upwork.com/ab/account-security/login'
            logger.info(f'Navigating to `{user_login_page}`')
            driver.get(user_login_page)
            logger.info('Pausing for windows to fully load')
            time.sleep(25)

            logger.info('Switching to main window')
            all_windows = driver.window_handles
            driver.switch_to.window(all_windows[-1])

            logger.info('Submitting username')
            username_input = WebDriverWait(driver, 30).until(
                EC.visibility_of_element_located(
                    (By.XPATH,
                     "/html/body/div[4]/div/div/div/main/div/div/div[2]/div[2]/form/div/div/div[1]/div[3]/div/div/div/"
                     "div/input")
                )
            )
            username_input.send_keys(config.UPWORK_USERNAME)

            username_field = WebDriverWait(driver, 30).until(
                EC.visibility_of_element_located(
                    (By.XPATH,
                     "/html/body/div[4]/div/div/div/main/div/div/div[2]/div[2]/form/div/div/div[1]/div[3]/div/div/div/"
                     "div/input")
                )
            )
            username_field.send_keys(Keys.ENTER)

            logger.info('Submitting password')
            password_input = WebDriverWait(driver, 30).until(
                EC.visibility_of_element_located(
                    (By.XPATH,
                     "/html/body/div[4]/div/div/div/main/div/div/div[2]/div[2]/div/form/div/div/div[1]/div[3]/div/div/div"
                     "/input")
                )

            )
            password_input.send_keys(config.UPWORK_PASSWORD)

            password_field = WebDriverWait(driver, 30).until(
                EC.visibility_of_element_located(
                    (By.XPATH,
                     "/html/body/div[4]/div/div/div/main/div/div/div[2]/div[2]/div/form/div/div/div[1]/div[3]/div/div/div"
                     "/input")
                )

            )
            password_field.send_keys(Keys.ENTER)

            logger.info(f'Pausing for {config.VERIFICATION_PAUSE} seconds for credentials verification')
            time.sleep(config.VERIFICATION_PAUSE)

            # Go to target url
            logger.info("Redirecting to Best Matches")
            driver.get('https://www.upwork.com/nx/find-work/best-matches')
            time.sleep(10)

            # Scroll down using keyboard actions
            logger.info('Scrolling down page')
            body = driver.find_elements('xpath', "/html/body")
            for i in range(0, 12):  # Just an arbitrary number of page downs
                body[-1].send_keys(Keys.PAGE_DOWN)
                time.sleep(2)
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            timeout_wait = 300

            # Wait for element to load
            logger.info(f'Waiting for element to load (max timeout set to {timeout_wait} seconds)...')
            wait = WebDriverWait(driver, timeout_wait)
            wait.until(EC.element_to_be_clickable((By.XPATH, f'/html/body/div[4]/div/div/div/main/div[3]/div[4]')))

            # Get all text as a wall of text (including user's mini bio on the top-right panel)
            text = driver.find_elements('xpath', f'/html/body/div[4]/div/div/div/main/div[3]/div[4]')[-1].text
            # Get rid of the right panel
            text_1 = text.split(config.UPWORK_USER_NAME)[0]
            # Get rid of the top panel
            text_2 = text_1.split('Ordered by most relevant.')[-1]
            # Get all job posts
            job_posts = text_2.split('Posted')[1:]

            # Get urls
            job_links = driver.find_elements("xpath", "//a[contains(@href, '/jobs/')]")
            job_urls = [link.get_attribute("href") for link in job_links
                        if 'ontology_skill_uid' not in link.get_attribute("href")
                        and 'search/saved' not in link.get_attribute("href")
                        and 'search/jobs/saved' not in link.get_attribute("href")
                        ]

            # Scrape jobs
            print('Scraping jobs...')
            counter = 0
            for j in job_posts:
                job_details = parse_job_details(j.split('\n'))
                # Check if the job ID already exists in the database
                job_id = job_details.get('job_id')
                job_url = job_urls[counter].split('/?')[0]
                cursor.execute('SELECT COUNT(*) FROM jobs WHERE job_id = ?', (job_id,))
                count = cursor.fetchone()[0]
                if count > 0:
                    logger.info(f'    Job ID #{job_id} already exists. Updating job proposals...')
                    updated_proposals = job_details.get('job_proposals')
                    # Update the job_proposals column
                    cursor.execute('UPDATE jobs SET job_proposals = ?, updated_at = ? WHERE job_id = ?', (
                        updated_proposals, datetime.now(), job_id))
                else:
                    posted_date = job_details.get('posted_date')
                    job_title = job_details.get('job_title')
                    job_description = job_details.get('job_description')
                    job_tags = job_details.get('job_tags')
                    job_proposals = job_details.get('job_proposals')
                    logger.info(f'Storing `{job_details.get("job_title")}` job in database')
                    cursor.execute(
                        'INSERT INTO jobs (job_id, job_url, job_title, posted_date, job_description, job_tags, '
                        'job_proposals) VALUES (?, ?, ?, ?, ?, ?, ?)',
                        (job_id, job_url, job_title, posted_date, job_description, job_tags, job_proposals))
                conn.commit()
                counter += 1

            # Close the browser
            logger.info('Closing browser...')
            driver.quit()

        else:
            logger.error("Couldn't load driver. Possible causes:")
            logger.error("1. Chrome is not installed on this system")
            logger.error("2. Chrome version mismatch with undetected-chromedriver")
            logger.error("3. Display/X11 issues in headless environment")
            logger.error("4. Insufficient permissions to run Chrome")
            logger.error("Solution suggestions:")
            logger.error("- Install Google Chrome: sudo apt-get update && sudo apt-get install -y google-chrome-stable")
            logger.error("- Try different Chrome versions in config.py")
            logger.error("- Check Chrome installation: google-chrome --version")
            return False

    except Exception as e:
        logger.error(f"Unexpected error occurred: {str(e)}")
        logger.error("Stack trace:", exc_info=True)
        return False

    finally:
        logger.info('Closing connection to database')
        cursor.close()
        conn.close()


if __name__ == '__main__':
    main()
