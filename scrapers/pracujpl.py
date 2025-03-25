from typing import Optional, List
import concurrent.futures
import requests
from bs4 import BeautifulSoup
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from schemas.offer import Offer
from .pracujpl_base import PracujPlBase


class PracujPL(PracujPlBase):
    """
    A class implementing the scraping strategy for PracujPL website.
    """

    def __init__(self):
        super().__init__()
        print("PracujPL instance created")

    def parse_data(self, content: str) -> List[Optional[Offer]]:
        """
        Parse job offer data from HTML content.
        Args:
            content (str): The HTML content to parse.
        Returns:
            List[Optional[Offer]]: A list of parsed offer inputs.
        """
        parsed_offers = []
        soup = BeautifulSoup(content, "html.parser")
        # Find all links with data-test="link-offer"
        offer_links = soup.find_all("a", attrs={"data-test": "link-offer"})
        print(f"Found {len(offer_links)} offers")
        links = [
            (link.get("title"), link.get("href"))
            for link in offer_links if link.get("title") and link.get("href")
        ]
        # Process links concurrently
        with concurrent.futures.ThreadPoolExecutor() as executor:
            future_to_offer = {
                executor.submit(self.process_job_link, title, url): (title, url) for title, url in links
            }
        for future in concurrent.futures.as_completed(future_to_offer):
            try:
                offer = future.result()
                parsed_offers.append(offer)
            except Exception as e:
                print(f"Error processing job link: {e}")

        print(f"Parsed {len(parsed_offers)} offers")
        return parsed_offers

    def process_job_link(self, title, url):
        # Remove 'Zobacz oferte' from title if present
        clean_title = title.replace("Zobacz ofertę ", "")
        job_page_content = self.get_job_page_content(url)

        # Extract additional details from job_page_content
        soup = BeautifulSoup(job_page_content, "html.parser")

        # Find the contract type
        contract_type_element = soup.find(
            "li", attrs={"data-test": "sections-benefit-contracts"})
        contract_type = None
        if contract_type_element:
            contract_type_div = contract_type_element.find(
                "div", attrs={"data-test": "offer-badge-title"})
            if contract_type_div:
                contract_type = contract_type_div.get_text(strip=True)

        # Find the job requirements
        requirements_section = soup.find(
            "section", attrs={"data-test": "section-requirements", "data-scroll-id": "requirements-1"})
        job_requirements = []
        if requirements_section:
            job_requirements = [li.get_text(strip=True)
                                for li in requirements_section.find_all("li", class_=lambda x: x and ("tkzmjn3" in x or "t6laip8" in x))]

        processed_url = self.remove_search_id(url)
        return Offer(title=clean_title, url=processed_url, contract_type=contract_type, requirements=job_requirements)

    def get_page_content(self, driver, base_url: str) -> Optional[str]:
        driver.get(base_url)
        page_content = driver.page_source
        if not page_content:
            return None

        print(f"Successfully visited: {base_url}")
        return page_content

    def get_job_page_content(self, url: str) -> Optional[str]:
        """
        Fetches the HTML content of a job page given its URL.

        Args:
            url (str): The URL of the job page.

        Returns:
            Optional[str]: The HTML content of the page, or None if the request fails.
        """
        try:
            response = requests.get(url)
            response.raise_for_status()  # Raise an error for bad responses
            return response.text
        except requests.RequestException as e:
            print(f"Error fetching job page content from {url}: {e}")
            return None
