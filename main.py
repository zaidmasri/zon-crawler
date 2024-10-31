import os
import asyncio
import asyncpg
import re
from datetime import datetime
from botasaurus_driver import Driver
from bs4 import BeautifulSoup
from dotenv import load_dotenv

load_dotenv()

base_product_url = "https://www.amazon.com/dp/"
base_review_url = "https://www.amazon.com/product-reviews/"
user_agent = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:66.0) Gecko/20100101 Firefox/66.0"
)


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


async def get_products():
    conn = await asyncpg.connect(
        user=os.getenv("PG_USER"),
        password=os.getenv("PG_PASSWORD"),
        database=os.getenv("PG_DATABASE"),
        host=os.getenv("PG_HOST"),
        port=os.getenv("PG_PORT"),
    )
    values = await conn.fetch("SELECT * FROM products")
    await conn.close()
    return values


async def main():
    today_date = datetime.now()
    print("Run date: " + str(today_date))

    driver = Driver(
        # headless=True,
        user_agent,
        beep=False,
    )
    products = await get_products()
    for product in products:
        asin = product.get("asin")
        print("ASIN: " + asin)
        link = base_review_url + asin
        driver.get(link, bypass_cloudflare=True)
        # TODO: Check if our request is blocked

        html = BeautifulSoup(driver.page_html, "html.parser")

        product_name = html.find(attrs={"data-hook": "product-link"})
        print("Product Name: " + product_name.get_text())

        overall_rating = html.find(attrs={"data-hook": "rating-out-of-text"})
        print(
            "Overall Rating: "
            + str(extract_float_from_phrase(overall_rating.get_text()))
        )

        total_review_count = html.find(attrs={"data-hook": "total-review-count"})
        print("Total Review Count: " + extract_integer(total_review_count.get_text()))

        print("Starting to analyze reviews... ")

        review_list = html.find_all(attrs={"data-hook": "review"})
        for review in review_list:
            review_id = review["id"]
            print("Review ID: " + review_id)

            review_title = review.find(attrs={"data-hook": "review-title"})

            review_href = review_title["href"]
            print("Review href: " + review_href)
            print(
                "Review Rating: "
                + str(extract_float_from_phrase(review_title.contents[0].get_text()))
            )
            print("Review Title: " + review_title.contents[3].get_text())

            review_date_field = review.find(attrs={"data-hook": "review-date"})
            # Use regular expressions to extract country and date
            match = re.search(
                r"Reviewed in (.+?) on (.+)", review_date_field.get_text()
            )

            # Check if the pattern was matched and extract groups
            if match:
                country = match.group(1)
                date = match.group(2)
                print(f"Review Country: {country}")
                print(f"Review Date: {date}")
            else:
                print("Pattern not found.")

            review_body = review.find(attrs={"data-hook": "review-body"})
            print("Review Body: " + review_body.get_text())

            verified_purchase = review.find(attrs={"data-hook": "avp-badge"})
            print("Verified Purchase: " + verified_purchase.get_text())

            found_helpful = review.find(attrs={"data-hook": "helpful-vote-statement"})
            if found_helpful:
                print("Found Helpful: " + found_helpful.get_text())
            else:
                print("Found Helpful: null")

    driver.close()


asyncio.run(main())
