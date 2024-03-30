# Copyright © 2024 roperi

import argparse
import time
import sqlite3
import hashlib
import json
from datetime import datetime, timedelta
import re
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys


def generate_job_id(job_title):
    """
    Generate a unique job ID based on the given job title.

    Parameters:
    - job_title (str): The title of the job.

    Returns:
    - str: The generated job ID.
    """
    # Convert the job title to lowercase and encode it as UTF-8
    job_title_bytes = job_title.lower().encode('utf-8')
    # Generate an MD5 hash of the job title
    return hashlib.md5(job_title_bytes).hexdigest()


def calculate_posted_datetime(timestamp):
    now = datetime.now()
    if 'yesterday' in timestamp:
        posted_datetime = now - timedelta(days=1)
    elif 'hour' in timestamp:
        hours_ago = int(re.findall(r'\d+', timestamp)[0])
        posted_datetime = now - timedelta(hours=hours_ago)
    elif 'day' in timestamp:
        days_ago = int(re.findall(r'\d+', timestamp)[0])
        posted_datetime = now - timedelta(days=days_ago)
    else:
        # Handle other cases if needed
        posted_datetime = now
    return posted_datetime


def parse_job_details(r):
    """
    Parse job details from a given row of data.

    Parameters:
    - r (list): A list containing job details.

    Returns:
    - dict: A dictionary containing parsed job details.
    """
    d = {
        'posted_date': calculate_posted_datetime(r[0]),
        'job_title': r[1],
        'job_description': r[5],
        'job_proposals': r[-2].replace('Proposals: ', '')
    }
    skills = r[6:-6]
    if 'more' in skills:
        skills.remove('more')
        skills.pop(0)
    if 'Next skills. Update list' in skills:
        skills.remove('Next skills. Update list')
    if 'Skip skills' in skills:
        skills.remove('Skip skills')
    d['job_tags'] = json.dumps(skills)
    d['job_id'] = generate_job_id(r[1])
    return d


def connect_to_db(database_name='upwork_jobs.db'):
    # Connect to database
    conn = sqlite3.connect(database_name)
    cursor = conn.cursor()
    return conn, cursor


def create_db(conn, cursor):
    # Create the `jobs` table (if it doesn't exist)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS jobs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            job_id TEXT NOT NULL,
            job_url TEXT,
            job_title TEXT NOT NULL,
            posted_date DATETIME,
            job_description TEXT NOT NULL,
            job_tags TEXT,
            job_proposals TEXT,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()


def main(chrome_version, user_name, num_hours, pause_to_login):
    """
    Main function for scraping job postings from Upwork.

    Parameters:
    - chrome_version (int): Chrome version.
    - user_name (str): The user name in Upwork (case sensitive).
    - num_hours (int): Number of hours between scraping jobs.
    - pause_to_login (int): Seconds to pause for manual login.

    Returns:
        bool: True if the scraping process completed successfully, False otherwise.

    This function connects to the database, configures the web driver, logs into site, and then starts an infinite loop
    to continuously scrape job postings. It scrolls down the page to load more job postings, extracts job details, and
    stores them in the database. It refreshes the browser after each scraping cycle and pauses for the specified number
    of hours before continuing to the next cycle. If an error occurs during the scraping process, it prints the error
    message and returns False.
    """
    try:
        # Connect to database
        conn, cursor = connect_to_db()

        # Create table (if it does not exist)
        create_db(conn, cursor)

        # Add the driver options
        options = uc.ChromeOptions()
        options.headless = False

        # Configure the undetected_chromedriver options
        driver = uc.Chrome(options=options, version_main=chrome_version)

        # Go to url
        url = 'https://www.upwork.com/ab/account-security/login?redir=%2Fnx%2Ffind-work%2Fbest-matches'
        driver.get(url)

        # Manually Login
        print(f'You have {pause_to_login} seconds to manually login to Upwork')
        time.sleep(pause_to_login)

        # Force driver to go to best matches
        print("If after-login redirection fails, I'll take you to Best Matches anyway")
        driver.get('https://www.upwork.com/nx/find-work/best-matches')
        time.sleep(30)

        # Define the refresh interval in seconds
        refresh_interval = num_hours * 60 * 60

        # Start an infinite loop
        while True:
            # Scroll down using keyboard actions
            print('Scrolling down page')
            body = driver.find_elements('xpath', "/html/body")
            for i in range(0, 12):  # Just an arbitrary number of page downs
                body[-1].send_keys(Keys.PAGE_DOWN)
                time.sleep(2)
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            timeout_wait = 300

            # Wait for element to load
            print(f'Waiting for element to load (max timeout set to {timeout_wait} seconds)...')
            wait = WebDriverWait(driver, timeout_wait)
            wait.until(EC.element_to_be_clickable((By.XPATH, f'/html/body/div[4]/div/div/div/main/div[2]/div[4]')))

            # Get text element
            text = driver.find_elements('xpath', f'/html/body/div[4]/div/div/div/main/div[2]/div[4]')[-1].text

            # Get rid of the right panel
            text_1 = text.split(user_name)[0]
            # Get rid of the top panel
            text_2 = text_1.split('Ordered by most relevant.')[-1]
            job_posts = text_2.split('Posted')[1:]

            # Get urls
            job_links = driver.find_elements("xpath", "//a[contains(@href, '/jobs/')]")
            job_urls = [link.get_attribute("href") for link in job_links
                        if 'ontology_skill_uid' not in link.get_attribute("href")
                        and 'search/saved' not in link.get_attribute("href")]

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
                    print(f'    Job ID #{job_id} already exists. Updating job proposals...')
                    updated_proposals = job_details.get('job_proposals')
                    # Update the job_proposals column
                    cursor.execute('UPDATE jobs SET job_proposals = ?, job_url = ? WHERE job_id = ?', (
                        updated_proposals, job_url, job_id))
                else:
                    posted_date = job_details.get('posted_date')
                    job_title = job_details.get('job_title')
                    job_description = job_details.get('job_description')
                    job_tags = job_details.get('job_tags')
                    job_proposals = job_details.get('job_proposals')
                    print(f'Storing `{job_details.get("job_title")}` job in database')
                    cursor.execute(
                        'INSERT INTO jobs (job_id, job_url, job_title, posted_date, job_description, job_tags, '
                        'job_proposals) VALUES (?, ?, ?, ?, ?, ?, ?)',
                        (job_id, job_url, job_title, posted_date, job_description, job_tags, job_proposals))
                conn.commit()
                counter += 1

            # Close connection to db
            print('Closing connection to database')
            cursor.close()
            conn.close()

            # Calculate the new datetime by adding n hours to the current datetime
            formatted_datetime = (
                    datetime.now() + timedelta(hours=num_hours)
            ).strftime("%d %b %Y %I:%M%p")
            print(f"Scraping again at {formatted_datetime}")

            # Sleep for the refresh interval before the next iteration
            time.sleep(refresh_interval)

            # Refresh page
            print('Refreshing page')
            driver.refresh()

            # Reconnecting to database
            print('Reconnecting to database')
            conn, cursor = connect_to_db()

        return True  # This is unreachable but I'm putting it here anyway

    except Exception as e:
        print(e)
        return False

    finally:
        cursor.close()
        conn.close()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Scrape jobs from Upwork's best matches.")
    parser.add_argument('--chrome_version', '-v', type=int, default=90, help='Chrome version to use.')
    parser.add_argument('--hours', '-H', type=int, default=4,
                        help='Interval in hours between scraping jobs. Default is 4 hours.')
    parser.add_argument('--pause', '-P', type=int, default=180,
                        help='Number of seconds to pause for manual login. Default is 180 seconds.')
    parser.add_argument('--name', '-n', required=True,
                        help='Your Upwork username (case-sensitive). This argument is required.')

    args = parser.parse_args()

    name = args.name
    hours = args.hours
    pause = args.pause
    version = args.chrome_version

    main(version, name, hours, pause)
