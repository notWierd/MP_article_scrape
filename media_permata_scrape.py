import os
import csv
import aiohttp
import asyncio
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
from datetime import datetime
import time

# Setup Selenium for scrolling and loading page content
def setup_selenium():
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--incognito")
    service = Service("C:/Users/Asus/Downloads/chromedriver-win64/chromedriver-win64/chromedriver.exe")  # Replace with your path
    driver = webdriver.Chrome(service=service, options=chrome_options)
    return driver

# Function to scroll the page using Selenium
def scroll_page(driver, url):
    driver.get(url)
    time.sleep(2)  # Wait for initial load

    # Start scrolling
    last_height = driver.execute_script("return document.body.scrollHeight")

    # Scroll continuously until the page doesn't load new content
    while True:
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(2)  # Wait for new content to load

        new_height = driver.execute_script("return document.body.scrollHeight")
        if new_height == last_height:  # Stop if height hasn't changed
            break
        last_height = new_height

    # Get page HTML after scrolling
    return driver.page_source

# Extract article links after the page is fully loaded
def extract_article_links(driver, category_url):
    page_html = scroll_page(driver, category_url)
    soup = BeautifulSoup(page_html, "html.parser")
    article_links = [
        h3.find('a')['href']
        for div in soup.find_all('div', class_="td_block_wrap td_flex_block_1 tdi_104 td_with_ajax_pagination td-pb-border-top td_block_template_1 td_flex_block")
        for entry in div.find_all('div', class_='td-module-meta-info')
        for h3 in entry.find_all('h3', class_='entry-title td-module-title')
    ]
    print(f"Found {len(article_links)} articles in {category_url}.")
    return article_links

# Read existing scraped URLs or titles from the CSV
def load_scraped_data(csv_file):
    scraped_urls = set()
    if os.path.exists(csv_file):
        with open(csv_file, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                scraped_urls.add(row["URL"])  # Use "Title" instead of "URL" if checking by title
    return scraped_urls

# Function to fetch a URL using aiohttp
async def fetch(session, url):
    async with session.get(url) as response:
        return await response.text()

# Function to extract article details
# Function to extract article details with a retry mechanism for empty content
# Function to extract article details with a retry mechanism
async def extract_article_details(session, article_url, category_name, writer, scraped_urls):
    if article_url in scraped_urls:
        print(f"Skipping already scraped: {article_url}")
        return

    # Retry logic for empty content
    max_retries = 2
    for attempt in range(max_retries):
        try:
            # Use aiohttp for the first attempt, Selenium for retries
            if attempt == 0:
                article_html = await fetch(session, article_url)
            else:
                # Reinitialize Selenium driver for retries
                driver = setup_selenium()
                driver.get(article_url)
                time.sleep(3)
                article_html = driver.page_source
                driver.quit()

            # Parse the article HTML
            article_soup = BeautifulSoup(article_html, "html.parser")

            # Extract article details
            title = article_soup.find("h1", class_="tdb-title-text").get_text(strip=True) if article_soup.find("h1", class_="tdb-title-text") else "N/A"
            author = "---"
            content = ""
            
           # Extract date from the correct div structure
            date_block = article_soup.find("div", class_="td_block_wrap tdb_single_date tdi_86 td-pb-border-top time_icon td_block_template_1 tdb-post-meta")
            raw_date = date_block.find("div", class_="tdb-block-inner td-fix-index").get_text(strip=True) if date_block else "N/A"
            # Convert to DD/MM/YYYY format
            try:
                formatted_date = datetime.strptime(raw_date, "%B %d, %Y").strftime("%d/%m/%Y")
            except ValueError:
                formatted_date = raw_date  # Keep as-is if format doesn't match

            article_block = article_soup.find("div", class_="tdb_single_content")
            if article_block:
                content_block = article_block.find("div", class_="tdb-block-inner")
                if content_block:
                    paragraphs = content_block.find_all("p")
                    if paragraphs:
                        first_paragraph = paragraphs[0].get_text(strip=True)
                        if "Oleh" in first_paragraph:
                            author = first_paragraph.split("Oleh")[-1].strip()
                            content = " ".join([p.get_text(strip=True) for p in paragraphs[1:]])
                        else:
                            content = " ".join([p.get_text(strip=True) for p in paragraphs])

            # Check if content is still empty
            if not content.strip():
                print(f"Empty content for {article_url}. Retrying ({attempt + 1}/{max_retries})...")
                if attempt + 1 < max_retries:
                    continue  # Retry if attempts are left
                else:
                    # Save article details even if content is empty
                    print(f"Failed to fetch content for {article_url} after {max_retries} attempts.")
                    writer.writerow({
                        "Category": category_name,
                        "Date": formatted_date,
                        "Title": title,
                        "Author": author,
                        "Content": "N/A",  # Content is empty, set as "N/A"
                        "URL": article_url
                    })
                    return  # Skip this article

            # Write the data to the CSV if content is not empty
            writer.writerow({
                "Category": category_name,
                "Date": formatted_date,
                "Title": title,
                "Author": author,
                "Content": content,
                "URL": article_url
            })
            print(f"Scraped: {title}")
            return

        except Exception as e:
            print(f"Error scraping {article_url} on attempt {attempt + 1}: {e}")
            if attempt + 1 < max_retries:
                print(f"Retrying {article_url}...")
            else:
                # Save article details even if content is empty after retries
                writer.writerow({
                    "Category": category_name,
                    "Date": formatted_date,
                    "Title": title,
                    "Author": author,
                    "Content": "N/A",  # Content is empty, set as "N/A"
                    "URL": article_url
                })
                print(f"Skipping {article_url} after {max_retries} failed attempts.")



# Main scraping function
async def scrape_media_permata():
    url = "https://mediapermata.com.bn/"
    driver = setup_selenium()

    category_links = ["https://mediapermata.com.bn/category/asean/"]
    output_file = "asean_scraped_articles.csv"
    scraped_urls = load_scraped_data(output_file)
    record_count = 0
    file_limit = 2500
    file_index = 1

    if not os.path.exists(output_file):
        with open(output_file, "w", newline="", encoding="utf-8") as f:
            fieldnames = ["Category", "Date", "Title", "Author", "Content", "URL"]
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()

    async with aiohttp.ClientSession() as session:
        with open(output_file, "a", newline="", encoding="utf-8") as f:
            fieldnames = ["Category", "Date", "Title", "Author", "Content", "URL"]
            writer = csv.DictWriter(f, fieldnames=fieldnames)

            for category_url in category_links:
                print(f"Extracting links from {category_url}")
                article_links = extract_article_links(driver, category_url)
                for article_url in article_links:
                    await extract_article_details(session, article_url, category_url.split("/")[-2].capitalize(), writer, scraped_urls)
    driver.quit()

# Run the script
asyncio.run(scrape_media_permata())
