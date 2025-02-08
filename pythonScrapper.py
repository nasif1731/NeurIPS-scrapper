import aiohttp
import asyncio
from bs4 import BeautifulSoup
import os
import re
import csv
import json

TIMEOUT = aiohttp.ClientTimeout(total=300)

def save_to_csv(metadata, year):
    root_folder = "D:/scraped-pdfs"
    os.makedirs(root_folder, exist_ok=True)  
    file_path = os.path.join(root_folder, f"metadata_{year}.csv")
    file_exists = os.path.isfile(file_path)
    
    with open(file_path, mode='a', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=['year', 'title', 'authors', 'abstract', 'pdf_url'])
        if not file_exists:
            writer.writeheader()  
        writer.writerow(metadata)
    print(f"[INFO] Metadata saved to CSV: {file_path}")

def save_to_json(metadata, year):
    root_folder = "D:/scraped-pdfs"
    os.makedirs(root_folder, exist_ok=True) 

    file_path = os.path.join(root_folder, f"metadata_{year}.json")
    if os.path.exists(file_path):
        with open(file_path, 'r+', encoding='utf-8') as f:
            data = json.load(f)
            data.append(metadata)
            f.seek(0)
            json.dump(data, f, indent=4)
    else:
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump([metadata], f, indent=4)
    print(f"[INFO] Metadata saved to JSON: {file_path}")

def sanitize_filename(filename):
    """ Remove invalid characters and limit filename length """
    filename = re.sub(r'[\/\\:\*\?"<>\|]', '', filename)  
    return filename[:200]

def load_processed_papers(year):
    """ Load already processed papers from JSON to avoid duplicates """
    file_path = f"D:/scraped-pdfs/metadata_{year}.json"
    if os.path.exists(file_path):
        with open(file_path, "r", encoding="utf-8") as f:
            try:
                return {paper["title"] for paper in json.load(f)}
            except json.JSONDecodeError:
                return set()
    return set()

async def process_paper(session, paper_url, year, processed_papers):
    print(f"[INFO] Processing paper: {paper_url}")  

    pdf_url = None  

    async with session.get(paper_url) as response:
        html = await response.text()
        soup = BeautifulSoup(html, 'html.parser')

        title = soup.select_one('title')
        if title:
            sanitized_title = sanitize_filename(title.get_text().strip())
        else:
            print(f"[WARNING] No title found for {paper_url}")
            return

        
        if sanitized_title in processed_papers:
            print(f"[INFO] Skipping already processed paper: {sanitized_title}")
            return  

        if year <= 2021:
            pdf_link = soup.select_one('a.btn.btn-light.btn-spacer[href*="Paper.pdf"]')
        else:
            pdf_link = soup.select_one('a.btn.btn-primary.btn-spacer[href*="Paper-Conference.pdf"]')

        if pdf_link:
            pdf_url = f"https://papers.nips.cc{pdf_link['href']}"
            print(f"[INFO] Found PDF for: {sanitized_title} -> {pdf_url}")
            await download_pdf(session, pdf_url, sanitized_title, year) 
        else:
            print(f"[WARNING] No PDF found for {sanitized_title}")

        authors = soup.select_one('h4:contains("Authors") + p i')
        authors_list = authors.get_text(strip=True) if authors else "No authors listed"

        abstract = soup.select_one('h4:contains("Abstract") + p')
        abstract_text = abstract.get_text(strip=True) if abstract else "No abstract available"

        metadata = {
            'year': year,
            'title': sanitized_title,
            'authors': authors_list,
            'abstract': abstract_text,
            'pdf_url': pdf_url if pdf_url else "No PDF found"
        }

        save_to_json(metadata, year)

async def download_pdf(session, pdf_url, file_name, year, retries=3):
    print(f"[INFO] Downloading PDF: {pdf_url}")

    year_folder = f"D:/scraped-pdfs/{year}"
    os.makedirs(year_folder, exist_ok=True)
    file_path = os.path.join(year_folder, f"{file_name}.pdf")

   
    if os.path.exists(file_path):
        print(f"[INFO] PDF already exists: {file_path}, skipping download.")
        return

    for attempt in range(retries):
        try:
            async with session.get(pdf_url, timeout=TIMEOUT) as response:
                if response.status == 200:
                    with open(file_path, 'wb') as f:
                        while True:
                            chunk = await response.content.read(1024 * 1024)  # Read 1MB at a time
                            if not chunk:
                                break
                            f.write(chunk)

                    print(f"[SUCCESS] Saved PDF: {file_path}")
                    return  
                else:
                    print(f"[WARNING] Failed to download {pdf_url} (HTTP {response.status})")

        except asyncio.TimeoutError:
            print(f"[ERROR] Timeout on attempt {attempt + 1} for {pdf_url}")
        except Exception as e:
            print(f"[ERROR] Failed to download {pdf_url} on attempt {attempt + 1}: {e}")

        if attempt < retries - 1:
            print(f"[INFO] Retrying download ({attempt + 1}/{retries})...")
            await asyncio.sleep(5) 

    print(f"[ERROR] Giving up on {pdf_url} after {retries} attempts")

async def fetch(session, url, retries=3):
    print(f"[INFO] Fetching URL: {url}") 
    for attempt in range(retries):
        try:
            async with session.get(url, timeout=TIMEOUT) as response:
                if response.status == 200:
                    html = await response.text()
                    print(f"[INFO] Successfully fetched: {url}")
                    return html
                else:
                    print(f"[WARNING] Failed to fetch {url} (HTTP {response.status})")

        except asyncio.TimeoutError:
            print(f"[ERROR] Timeout while fetching {url}, attempt {attempt + 1}/{retries}")
        except Exception as e:
            print(f"[ERROR] Network error: {e}, attempt {attempt + 1}/{retries}")

        if attempt < retries - 1:
            print(f"[INFO] Retrying fetch ({attempt + 1}/{retries})...")
            await asyncio.sleep(5)

    print(f"[ERROR] Giving up on {url} after {retries} attempts")
    return None

async def scrape(year):
    url = f"https://papers.nips.cc/paper_files/paper/{year}"
    print(f"[INFO] Scraping year: {year}") 

    async with aiohttp.ClientSession() as session:
        html = await fetch(session, url)
        if not html:
            print(f"[ERROR] Failed to load year {year}, skipping...")
            return
        
        soup = BeautifulSoup(html, 'html.parser')
        paper_list = soup.select("ul.paper-list")

        if not paper_list:
            print(f"[WARNING] No paper list found for year {year}")
            return

        print(f"[INFO] Found {len(paper_list)} paper lists for year {year}")

       
        processed_papers = load_processed_papers(year)

        if year <= 2021:
            papers = soup.select("ul.paper-list li a[href*='-Abstract.html']")
        else:
            papers = soup.select("ul.paper-list li a[href*='-Abstract-Conference.html']")

        print(f"[INFO] Found {len(papers)} papers for year {year}")

        for paper in papers:
            paper_title = paper.get_text(strip=True)
            paper_url = f"https://papers.nips.cc{paper['href']}"

            if paper_title in processed_papers:
                print(f"[INFO] Skipping already processed paper: {paper_title}")
                continue

            print(f"[INFO] Found paper: {paper_title} -> {paper_url}")
            await process_paper(session, paper_url, year, processed_papers)

async def main():
    year_range = range(2017, 2024) 
    print("[INFO] Starting scraping process...")

    async with aiohttp.ClientSession() as session:
        for year in year_range: 
            await scrape(year)
            await asyncio.sleep(5)  

    print("[INFO] Scraping completed!")

if __name__ == '__main__':
    asyncio.run(main())