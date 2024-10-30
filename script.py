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


async def fetch_data():
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
    products = await fetch_data()
    for product in products:

        # link = base_product_url + product.get("asin")
        # # driver.prompt()
        link = base_review_url + product.get("asin")
        driver.get(link, bypass_cloudflare=True)
        html = BeautifulSoup(driver.page_html, "html.parser")

        product_name = html.find(attrs={"data-hook": "product-link"})
        print("Product Name: " + product_name.get_text())

        star_rating = html.find(attrs={"data-hook": "rating-out-of-text"})
        print("Star Rating: " + star_rating.get_text())

        total_review_count = html.find(attrs={"data-hook": "total-review-count"})
        print("Total Review Count: " + extract_integer(total_review_count.get_text()))

        print("Starting to analyze reviews... ")

        review_list = html.find_all(attrs={"data-hook": "review"})
        # print(review_list)
        # for review in review_list:
        # print(review)
        # user_name = review.find(attrs={"data-hook": "genome-widget"})
        # print("Username: " + user_name)

        # review_list = driver.get_text("#cm_cr-review_list")
        # review_list = driver.get_text("[data-hook='review']:not(.cr-vote-action-bar)")
        # p = pq(driver.page_html)
        # print(
        #     p("[data-hook='review']")
        #     # .each()
        #     # .not_("[data-reftag='cm_cr_getr_d_cmt_opn']")
        #     # .text()
        # )

    driver.close()


asyncio.run(main())


#
