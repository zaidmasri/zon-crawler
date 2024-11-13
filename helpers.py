# Used to get the number of reviews
import re

from bs4 import BeautifulSoup
from botasaurus_driver import Wait

from server import Server


def extract_integer(s):
    # This regex pattern looks for digits, possibly separated by commas
    pattern = r"(\d{1,3}(?:,\d{3})*)"
    match = re.search(pattern, s)

    if match:
        # Remove commas and return the integer as a string
        return match.group(0).replace(",", "")
    return None


# Input string example: "2.0 out of 5 stars"
def extract_float_from_phrase(s):
    # Use regular expression to find the float value
    match = re.search(r"\d+\.\d+|\d+", s)
    if match:
        rating = float(match.group())
        return rating
    else:
        return None


async def fetch_page_with_retry(srv: Server, full_url, max_retries=10):
    """Helper function to handle CAPTCHA retry logic."""
    retry_count = 0

    while retry_count < max_retries:
        try:
            srv.driver.google_get(
                link=full_url, wait=Wait.SHORT, bypass_cloudflare=True
            )
            html = BeautifulSoup(srv.driver.page_html, "html.parser")

            # Check for CAPTCHA
            if html.find(id="captchacharacters"):
                retry_count += 1
                srv.logger.error(
                    msg=f"BOT DETECTED... retrying {retry_count}/{max_retries}",
                )
                continue  # Retry the loop if CAPTCHA is detected

            # Return HTML if no CAPTCHA
            return html

        except Exception as e:
            srv.logger.info(f"Error loading URL {full_url}: {e}")
            return None  # Exit if there's another error

    # Return None if max retries reached
    srv.logger.info(f"Max retries reached for {full_url}.")
    return None
