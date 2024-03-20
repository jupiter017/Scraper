import time
import sqlite3
import hashlib
import json
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys


def generate_job_id(job_title):
    # Convert the job title to lowercase and encode it as UTF-8
    job_title_bytes = job_title.lower().encode('utf-8')
    # Generate an MD5 hash of the job title
    return hashlib.md5(job_title_bytes).hexdigest()


def parse_job_details(r):
    d = {'job_title': r[1], 'job_description': r[5], 'job_proposals': r[-2].replace('Proposals: ', '')}
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


def main(n_hours):

    # Connect to database
    conn = sqlite3.connect('upwork_jobs.db')
    cursor = conn.cursor()

    # Create the articles table if it doesn't exist
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS jobs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            job_id TEXT NOT NULL,
            job_url TEXT,
            job_title TEXT NOT NULL,
            job_description TEXT NOT NULL,
            job_tags TEXT,
            job_proposals TEXT,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    conn.commit()

    # Add the driver options
    options = uc.ChromeOptions()
    options.headless = False

    # Configure the undetected_chromedriver options
    driver = uc.Chrome(options=options, version_main=90)

    # Go to url
    url = 'https://www.upwork.com/ab/account-security/login?redir=%2Fnx%2Ffind-work%2Fbest-matches'
    driver.get(url)

    # Manually Login
    time.sleep(180)

    # Define the refresh interval in seconds
    refresh_interval = n_hours * 60 * 60

    # Start an infinite loop
    while True:
        try:
            # Scroll down using keyboard actions
            print('Scrolling down page')
            body = driver.find_elements('xpath', "/html/body")
            for i in range(0,15):
                body[-1].send_keys(Keys.PAGE_DOWN)
                time.sleep(2)
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            timeout_wait = 300
            print(f'Waiting for element to load (max timeout set to {timeout_wait} seconds)...')
            wait = WebDriverWait(driver, timeout_wait)
            element = wait.until(EC.element_to_be_clickable((By.XPATH,
                                                             f'/html/body/div[4]/div/div/div/main/div[2]/div[4]')))
            text = driver.find_elements('xpath', f'/html/body/div[4]/div/div/div/main/div[2]/div[4]')[-1].text
            # Get rid of the right panel
            text_1 = text.split('Rodolfo')[0]
            # Get rid of the top panel
            text_2 = text_1.split('Ordered by most relevant.')[-1]
            job_posts = text_2.split('Posted')
            # Scrape jobs
            print('Scraping jobs...')
            for j in job_posts[1:]:
                job_details = parse_job_details(j.split('\n'))
                # Check if the job ID already exists in the database
                job_id = job_details.get('job_id')
                cursor.execute('SELECT COUNT(*) FROM jobs WHERE job_id = ?', (job_id,))
                count = cursor.fetchone()[0]
                if count > 0:
                    print(f'Job ID #{job_id} already exists. Skipping this job')
                    continue
                job_id = job_details.get('job_id')
                job_title = job_details.get('job_title')
                job_description = job_details.get('job_description')
                job_tags = job_details.get('job_tags')
                job_proposals = job_details.get('job_proposals')
                print(job_details.get('job_id'))
                print(job_details.get('job_title'))
                print( job_details.get('job_description'))
                print(job_details.get('job_tags'))
                print(job_details.get('job_proposals'))
                # Write to db
                cursor.execute('INSERT INTO jobs (job_id, job_title, job_description, job_tags, job_proposals) '
                               'VALUES (?, ?, ?, ?, ?)',
                 (job_id, job_title, job_description, job_tags, job_proposals))
                conn.commit()
        except Exception as e:
            print(e)
        print('Refreshing browser')
        driver.refresh()
        print(f'Pausing for {num_hours} hour(s) before continuing')
        # Sleep for the refresh interval before the next iteration
        time.sleep(refresh_interval)


# MAIN

if __name__ == '__main__':
    num_hours = 4
    main(num_hours)
