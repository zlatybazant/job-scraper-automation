from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager
import os


def get_driver():
    """
    Retrieves a WebDriver instance for Chrome browser.

    Returns:
        webdriver.Chrome: WebDriver instance for Chrome browser.
    """
    try:

        driver_path = '/home/simonohm/.wdm/drivers/chromedriver/linux64/133.0.6943.53/chromedriver-linux64/chromedriver'
        if not os.path.isfile(driver_path):
            raise FileNotFoundError(f"ChromeDriver not found at {driver_path}")
        return webdriver.Chrome(service=ChromeService(driver_path))
    except Exception as e:
        print(f"An error occured while initializing the ChromeDriver: {e}")
