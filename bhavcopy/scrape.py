from bs4 import BeautifulSoup
import requests
from typing import Optional


def search_company(query: str) -> Optional[dict]:
    url = "https://www.screener.in/api/company/search/"
    params = {"q": query, "v": "3", "fts": "1"}
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException:
        return None


def get_company(query: str) -> Optional[dict]:
    companies = search_company(query)
    return companies[0] if companies else None


def fetch_html_for_company(company: Optional[dict]) -> Optional[str]:
    if not company:
        return None
    url = f"https://www.screener.in{company['url']}"
    try:
        response = requests.get(url)
        response.raise_for_status()
        return response.text
    except requests.exceptions.RequestException:
        return None


def extract_company_name(html_content: str) -> Optional[str]:
    if not html_content:
        return None
    soup = BeautifulSoup(html_content, "html.parser")
    h1_tag = soup.find("h1", class_="margin-0 show-from-tablet-landscape")
    if h1_tag:
        return h1_tag.text.strip()
    else:
        return None


def extract_nse_script(html_content: str) -> Optional[str]:
    if not html_content:
        return None
    try:
        soup = BeautifulSoup(html_content, "html.parser")
        a_tag = soup.find(
            lambda tag: tag.name == "a" and tag.get("href", "").startswith("https://www.nseindia.com/get-quotes/"),
            target="_blank",
            rel="noopener noreferrer",
        )
        if a_tag:
            span_text = a_tag.find("span").get_text().strip()
            return span_text.split(" ")[-1]
    except Exception as e:
        print(f"Error occurred while extracting NSE script: {e}")
        return None
