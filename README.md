# MP Article Scraper

This project scrapes articles from Media Permata.

## Installation

### 1. Clone the Repository
```sh
git clone https://github.com/your-username/MP_article_scrape.git
cd MP_article_scrape
```

### 2. Install Dependencies
Make sure you have Python installed, then run:
```sh
pip install -r requirements.txt
```

### 3. Install ChromeDriver
Download the latest ChromeDriver from [here](https://developer.chrome.com/docs/chromedriver/downloads) that matches your Chrome version.

- Extract the downloaded file.
- Note the path where you extracted the `chromedriver` executable.

### 4. Update the ChromeDriver Path
Open the scraper script (e.g., `media_permata.py`) and update the ChromeDriver path:
```python
from selenium import webdriver

service = Service("your/path/to/chromedriver")
```

## Usage
Open the script and modify the following:

1. Category Links: Update the category_links list with the categories you want to scrape. Please do note that the following categories has been scraped(hiburan, surat_pembaca and borneo)

2. Output File Names: Change the CSV file names accordingly to store the scraped data.
Run the scraper with:
```sh
python media_permata_scrape.py
```

## Notes
- Ensure that Chrome and ChromeDriver versions match to avoid compatibility issues.
- If you encounter permission errors, try running with `sudo` (Linux/macOS) or as Administrator (Windows).

