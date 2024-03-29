<h1 align="center">Upwork Scraper</h1>
<h2 align="center">Python + Selenium + SQLite</h2>

---

Upwork Scraper is designed to automate the process of scraping job postings from Upwork's best matches. It utilizes Selenium for web scraping and interacts with the Upwork website to extract job details, including job titles, descriptions, and proposals. The script then stores the extracted data in a SQLite database for easy access and retrieval.

Users can customize the interval between scraping jobs and the pause duration for manual login according to their preferences. The script provides a streamlined solution for users who want to efficiently search for new job opportunities on Upwork without the hassle of manually browsing through job listings.

---
## Benefits

- **Time Saving:** Automates the process of scraping job postings from Upwork, saving users time and effort.
- **Efficient Job Search:** Facilitates a more efficient job search experience by automatically collecting and organizing job details.
- **Customizable Interval:** Allows users to set the interval between scraping jobs according to their preferences.

## Key Features

- **Automated Scraping:** Automatically scrolls through job postings on Upwork and extracts relevant job details.
- **Database Integration:** Stores job details in a SQLite database for easy access and retrieval.
- **Manual Login Support:** Includes a pause option for manual login, allowing users to authenticate before scraping.


## Disclaimer

This script is designed to automate the process of scraping job postings from Upwork in order to streamline the job searching experience. It aims to save time and effort for individuals who regularly check for new job opportunities on the site.

While the script is intended to be a helpful tool, users should be aware that scraping data from Upwork may potentially violate Upwork's terms of service or other legal agreements. It is important to use this script responsibly and in accordance with all applicable laws and regulations.

The author of this script disclaims any liability for the misuse or improper use of the script. Users assume all risks associated with its use, including any legal consequences that may arise from violating Upwork's terms of service.

By using this script, you agree to use it responsibly and to comply with all applicable laws and regulations. The author encourages users to review Upwork's terms of service and other legal agreements before using this script.

Use this script at your own discretion and risk.

## Requirements

- Python 3.x
- Selenium
- Undetected Chromedriver
- SQLite3

## Tested Environment

This program has been tested and verified to work correctly in Python 3.11.

## Installation

1. **Create Virtual Environment:** It's recommended to create a virtual environment to isolate the dependencies of this project. You can create a virtual environment with Python 3.11 using the following command:

    ```bash
    python3 -m venv venv
    ```

    This command will create a virtual environment named `venv` in the current directory.

2. **Activate Virtual Environment:** After creating the virtual environment, activate it using the appropriate command for your operating system:

    - On Windows:

        ```bash
        .\venv\Scripts\activate
        ```

    - On macOS and Linux:

        ```bash
        source venv/bin/activate
        ```
      
3. **Clone the repository:**
   
    ```
    git clone https://github.com/roperi/UpworkScraper.git
    ```

4. **Navigate to the project directory:**
   
    ```
    cd UpworkScraper/
    ```

5. **Install the required dependencies:**
   
    ```
    pip install -r requirements.txt
    ```

## Usage


Run Upwork Scraper with the following command:

```bash
python scraper.py --name YOUR_NAME
```

IMPORTANT: Replace `YOUR_NAME` with the **first name** shown next to your profile picture on the right side panel. So if the name shown next to your profile pic says "John Smith" provide the script with `John`.
 Login and navigate to [best matches](https://www.upwork.com/nx/find-work/best-matches) to double check what is the first name of your full name that appears on your profile description. 

Optional arguments:
* --chrome_version, -v: Chrome version to use.
* --hours, -H: Interval in hours between scraping jobs. Default is 4 hours.  
* --pause, -P: Number of seconds to pause for manual login. Default is 180 seconds.

Examples:

```
# John will scrape his best matches every 4 hours (default) with 3 minutes (default) for manual login in Chrome version 90 (default).
python scraper.py --name "John"

# Ruby will scrape her best matches every 10 hours with 1 minute for manual login, using Chrome version 123.
python scraper.py --name "Ruby" -P 60 -H 10 -v 123
```

## Functionality
Upwork Scraper performs the following tasks:

1. Goes to the Upwork login page (you need to perform a manual login).
2. Scrapes job postings from Upwork's best matches page.
3. Parses job details and stores them in a SQLite database.
4. Refreshes the page after a specified interval and continues scraping.

## Contributing
Contributions are welcome! If you encounter any issues or have suggestions for improvements, please open an issue or submit a pull request.

## TODO
- Capture job URLs ✅


## Copyright and licenses
Copyright © 2024 roperi. 

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
