from typing import Optional, List

from bs4 import BeautifulSoup

from schemas.offer_schema import OfferInput
from utils.get_driver import get_driver
from .abc.scraper_strategy import ScraperStrategy
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


class PracujPL(ScraperStrategy):

    @staticmethod
    def parse_data(content: str) -> List[Optional[OfferInput]]:
        parsed_offers = []
        soup = BeautifulSoup(content, "html.parser")
        offers = soup.find_all("div", class_="tiles_c1m5bwec")
        print(f"Found {len(offers)} offers")

        for offer in offers:
            title = offer.find("h2")
            url = offer.find("a", class_="core_n194fgoq")
            print(title.text, url.get("href"))
            if title and url:
                parsed_offers.append(OfferInput(title=title.text, url=url.get("href")))

        print(f"Parsed {len(parsed_offers)} offers")
        return parsed_offers

    @staticmethod
    def get_max_page_number(content: str) -> int:
        try:
            soup = BeautifulSoup(content, "html.parser")
            max_page_element = soup.find(
                "span", {"data-test": "top-pagination-max-page-number"}
            )
            if max_page_element:
                return int(max_page_element.text)
        except Exception as e:
            print(e)

        return 1

    @staticmethod
    def close_modal(driver) -> None:
        try:
            modal = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CLASS_NAME, "core_ig18o8w"))
            )
            modal.click()
        except Exception as e:
            print(e)

    def scrape(self, url: str) -> List[Optional[OfferInput]]:
        print("Run PracujPL scraper")
        offers = []
        base_url = url

        driver = get_driver()
        driver.get(base_url)
        self.close_modal(driver)

        page_content = driver.page_source
        parsed_offers = self.parse_data(page_content)

        offers.extend(parsed_offers)

        max_page = self.get_max_page_number(page_content)
        print(f"pracuj.pl max page: {max_page}")

        for page in range(2, max_page + 1):
            url = f"{base_url}&pn={page}"
            driver.get(url)
            page_content = driver.page_source
            parsed_offers = self.parse_data(page_content)
            offers.extend(parsed_offers)

        print(f"Scraped {len(offers)} offers")
        return offers
