import sqlite3


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

