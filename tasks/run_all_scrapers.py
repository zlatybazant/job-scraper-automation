import time
from typing import List, Optional, Dict
import requests
from config.database import get_db
from export.googlesheet import GoogleSheet
from scrapers.abc.scraper import Scraper
from utils.map_url_to_scraper import url_to_scraper
from utils.urls_to_skip import get_urls_to_skip
from utils.validate_title_keywords import check_title
from export.excel import ExcelWriter
from service.offer_service import OfferService


def run_all_scraper(
        websites: List[Optional[Dict[str, str]]],
        worksheet_url: str,
        export_type: str = "excel",  # or 'googlesheet' or 'db'
        max_offer_duration_days: Optional[int] = None,
        keywords_to_pass: List[Optional[str]] = None,
) -> None:
    """
    Runs all scrapers for the given list of websites and adds scraped data to the specified Google Sheet.

    Args:
        websites (List[Optional[str]]): A list of website URLs to scrape.
        worksheet_url (str) The worksheet url.
        export_type (str)
        max_offer_duration_days
        keywords_to_pass (List[Optional[str]])
    Returns:
        None
    """
    urls_to_skip = get_urls_to_skip()

    if not websites:
        print("No websites to scrape")
        return

    all_offers = []

    for data in websites:
        url = data.get("url")
        tag = data.get("tag")

        offer_service = None
        if export_type == "db":
            offer_service = OfferService(next(get_db()))

        scraper_class, website = url_to_scraper(url)
        print(f"ras: {scraper_class} {website}")
        if not scraper_class:
            print("Invalid URL or website is not supported")
            continue

        scraped_offers = Scraper(scraper_class).scrape(
            url, max_offer_duration_days)
        for offer in scraped_offers:
            if offer.url in urls_to_skip:
                print("Offer skipped")
                continue

            if check_title(offer.title, keywords_to_pass):
                print(f"Offer skipped: {offer.title}")
                continue

            all_offers.append({**offer.dict(), "tag": tag,
                              "contract_type": offer.contract_type})

            # Save data to .xlsx file
            if export_type == "excel":
                ew = ExcelWriter()

                if ew.data_exists(url=offer.url):
                    print("Offer exists in excel")
                    continue

                ew.add_data(data=offer, website=website, tag=tag)
                ew.save()

            # Save data to Google Sheet
            # This option is the slowest because of API rate limit
            elif export_type == "googlesheet":
                gs = GoogleSheet(worksheet_url)

                if gs.data_exists(2, offer.url):
                    print("Offer exists in google sheet")
                    # Rate limit Google Sheet API (60 requests per minute)
                    time.sleep(2)
                    continue

                # Rate limit Google Sheet API (60 requests per minute)
                time.sleep(2)

                gs.add_data(data=offer, website=website, tag=tag)

            # Save data to SQLite database
            # Then you are able to run local server based on FastAPI and Jinja Template
            elif export_type == "db" and offer_service:
                offer_service.create(data=offer, website=website, tag=tag)

            else:
                raise ValueError("Invalid export type")

    # Send aggregated data to the webhook
    json_payload = [
        offer for offer in all_offers if offer["url"] not in urls_to_skip]
    print(f"JSON: {json_payload}")
    if not json_payload:
        print("No new offers to send to the webhook.")
        return

    try:
        response = requests.post(
            "https://hook.eu2.make.com/z7gdth8t1fes8piaq7r46mcsmattmj8f",
            json=json_payload
        )
        response.raise_for_status()
        print("Data successfully sent to webhook")
    except requests.exceptions.RequestException as e:
        print(f"Failed to send data to webhook: {e}")

    # Append newly found offer URLs to urls_to_skip.txt
    with open("urls_to_skip.txt", "a", encoding="utf-8") as file:
        for offer in all_offers:
            file.write(f"{offer['url']}\n")
