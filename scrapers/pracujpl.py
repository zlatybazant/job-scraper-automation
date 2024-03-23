from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager

from .abc.scraper_strategy import ScraperStrategy


class PracujPL(ScraperStrategy):

    @staticmethod
    def parse_data(content: str) -> None:
        soup = BeautifulSoup(content, "html.parser")
        offers = soup.find_all("div", class_="be8lukl")
        for offer in offers:
            title = offer.find("h2")
            url = offer.find("a", class_="core_n194fgoq")
            if title and url:
                print(title.text, url.get("href"))

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

    def scrape(self, url: str) -> None:
        driver = webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()))

        base_url = url
        driver.get(base_url)
        page_content = driver.page_source
        self.parse_data(page_content)
        max_page = self.get_max_page_number(page_content)

        for page in range(2, max_page + 1):
            url = f"{base_url}&pn={page}"
            driver.get(url)
            page_content = driver.page_source
            self.parse_data(page_content)
