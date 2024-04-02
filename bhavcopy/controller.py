from typing import Optional, Tuple
from scrape import get_company, fetch_html_for_company, extract_company_name, extract_nse_script


def process_company(code: int) -> Tuple[int, Optional[str], Optional[str]]:
    company = get_company(code)
    html_content = fetch_html_for_company(company)
    company_name = extract_company_name(html_content)
    script = extract_nse_script(html_content)

    return code, company_name, script
