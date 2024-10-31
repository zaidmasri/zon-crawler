import os
from botasaurus_driver import Driver
import asyncio
import asyncpg
import re
from bs4 import BeautifulSoup
from dotenv import load_dotenv

# from pyquery import PyQuery as pq
load_dotenv()


base_product_url = "https://www.amazon.com/dp/"
base_review_url = "https://www.amazon.com/product-reviews/"


def extract_integer(s):
    # This regex pattern looks for digits, possibly separated by commas
    pattern = r"(\d{1,3}(?:,\d{3})*)"
    match = re.search(pattern, s)

    if match:
        # Remove commas and return the integer as a string
        return match.group(0).replace(",", "")
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
    driver = Driver(
        # headless=True,
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:66.0) Gecko/20100101 Firefox/66.0",
        beep=False,
    )
    products = await get_products()
    for product in products:
        asin = product.get("asin")
        print("ASIN: " + asin)
        link = base_review_url + asin
        driver.get(link, bypass_cloudflare=True)
        html = BeautifulSoup(driver.page_html, "html.parser")

        product_name = html.find(attrs={"data-hook": "product-link"})
        print("Product Name: " + product_name.get_text())

        overall_rating = html.find(attrs={"data-hook": "rating-out-of-text"})
        print("Overall Rating: " + overall_rating.get_text())

        total_review_count = html.find(attrs={"data-hook": "total-review-count"})
        print("Total Review Count: " + extract_integer(total_review_count.get_text()))

        print("Starting to analyze reviews... ")

        review_list = html.find_all(attrs={"data-hook": "review"})
        for review in review_list:
            review_id = review["id"]
            print("Review ID: " + review_id)

            review_title = review.find(attrs={"data-hook": "review-title"})
            print("Review Rating: " + review_title.contents[0].get_text())
            print("Review Title: " + review_title.contents[3].get_text())

            review_href = review_title["href"]
            print("Review href: " + review_href)

            review_body = review.find(attrs={"data-hook": "review-body"})
            print("Review Body: " + review_body.get_text())

    driver.close()


asyncio.run(main())


#