from typing import Optional, List

from bs4 import BeautifulSoup

from schemas.offer import Offer
from .pracujpl_base import PracujPlBase


class ITPracujPL(PracujPlBase):
    """
    A class implementing the scraping strategy for ITPracujPL website.
    """

    def parse_data(self, content: str) -> List[Optional[Offer]]:
        """
        Parses job offer data from the HTML content.

        Args:
            content (str): The HTML content to parse.

        Returns:
            List[Optional[Offer]]: A list of parsed offer inputs.
        """
        parsed_offers = []

        soup = BeautifulSoup(content, "html.parser")
        offer_links = soup.find_all("a", attrs={"data-test": "link-offer"})
        print(f"Found {len(offer_links)} offers")

        for link in offer_links:
            title = link.get("title")
            # Get title from the 'title' attribute
            url = link.get("href")
            if title and url:
                processed_url = self.remove_search_id(url)
                parsed_offers.append(
                    Offer(title=title, url=processed_url)
                )

        print(f"Parsed {len(parsed_offers)} offers")
        return parsed_offers

    def get_page_content(self, driver, base_url: str) -> Optional[str]:
        driver.get(base_url)
        page_content = driver.page_source
        if not page_content:
            return None

        print(f"Successfully visited: {base_url}")
        return page_content
