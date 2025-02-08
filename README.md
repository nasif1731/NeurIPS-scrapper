# NeurIPS Paper Scraper

## Overview
This repository contains Python and Java-based web scrapers for extracting research paper metadata from the NeurIPS website. The scrapers collect information such as paper titles, authors, abstracts, and PDF links, saving them in structured formats like CSV and JSON.

## Features
- **Python Scraper**: Uses `aiohttp` and `BeautifulSoup` for asynchronous web scraping.
- **Java Scraper**: Uses `Jsoup` and `Apache HttpClient` with multi-threading for efficient scraping.
- **Handles Pagination**: Extracts data across multiple pages.
- **Error Handling**: Exception handling for CSS selector variations and request timeouts.
- **Data Storage**: Saves extracted metadata in CSV and JSON formats.

## Installation
### Prerequisites
- Python 3.7+
- Java 11+


## Usage
### Running the Python Scraper
```bash
python pythonScrapper.py
```
### Running the Java Scraper
```bash
java PDFScraper
```

## Output
The scraped data is stored in the `D:/scraped-pdfs/` directory with:
- `metadata_<year>.csv`
- `metadata_<year>.json`

## Challenges Faced
- **CSS Selector Changes**: Handled different structures for pre/post-2021 papers.
- **Rate Limiting**: Introduced request delays to prevent server blocks.
- **Slow Downloads**: Implemented timeout mechanisms and retry logic.

## Ethical Considerations
- The scraper respects the `robots.txt` policy.
- Rate limiting is used to avoid overwhelming the website.
- Extracted data should be credited to NeurIPS when used.

## Author
- **Nehal Asif** – *Data Science for Software Engineers Student*

## Contributions
Feel free to submit issues or pull requests to improve the scraper!

