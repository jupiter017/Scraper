import hashlib
import json
from datetime import datetime, timedelta
import re


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
    """
    Calculate the datetime when a job was posted based on the given timestamp.

    Parameters:
    - timestamp (str): The timestamp indicating when the job was posted, such as 'yesterday', '3 hours ago', etc.

    Returns:
    - datetime.datetime: The calculated datetime representing when the job was posted.
    """
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
    if 'freelancers' in r[-2]:
        job_proposals = r[-2].replace('Proposals: ', '').split(' Nu')[0]
    else:
        job_proposals = r[-2].replace('Proposals: ', '').replace('Load More Jobs', '')
    d = {
        'posted_date': calculate_posted_datetime(r[0]),
        'job_title': r[1],
        'job_description': r[5],
        'job_proposals': job_proposals
    }
    skills = r[6:-6]
    if 'more' in skills:
        skills.remove('more')
        skills.pop(0)
    if 'Next skills. Update list' in skills:
        skills.remove('Next skills. Update list')
    if 'Skip skills' in skills:
        skills.remove('Skip skills')
    if "  Payment verified" in skills:
        skills.remove("  Payment verified")
    if "  Payment unverified" in skills:
        skills.remove("  Payment unverified")
    d['job_tags'] = json.dumps(skills)
    d['job_id'] = generate_job_id(r[1])
    return d
