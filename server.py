from datetime import datetime
import re
import string
from typing import Coroutine
from botasaurus_driver import Driver, Wait
from bs4 import BeautifulSoup
from helpers import extract_float_from_phrase, extract_integer
from main import base_amazon_url, base_review_url

banned_asin = ["B0D5BTBHBK", "B0DHRXRJ9X"]


class Server:
    driver: Driver
    conn: Coroutine

    def __init__(self, driver: Driver, db: Coroutine):
        self.driver = driver
        self.conn = db

    async def get_products(self):
        values = await self.conn.fetch("SELECT * FROM products")
        await self.conn.close()
        return values

    async def create_product(self, asin: string, name: string):
        await self.conn.execute(
            """
                INSERT INTO products (asin, name) 
                VALUES ($1, $2)
                ON CONFLICT (asin) DO NOTHING
            """,
            asin,
            name,
        )

    async def run_scrapper(self):
        """
        Uses get_products()
        Then scrapes every product by asin
        """
        today_date = datetime.now()
        print("Run date: " + str(today_date))
        products = await self.get_products()
        for product in products:
            asin = product.get("asin")
            self.__scrape_review_page(asin, self)

        self.driver.close()

    def get_product_urls(
        self, url: string, max: int, product_urls: list[str], index: int
    ):
        if len(product_urls) >= max:
            # driver.close()
            return product_urls

        self.driver.get(url, wait=Wait.LONG)
        html = BeautifulSoup(self.driver.page_html, "html.parser")

        urls = html.find_all("a", href=re.compile(r"/(dp)/"))
        for link in urls:
            asin = link["href"].split("/dp/")[1].split("/")[0]
            # Skip banned ASINs
            if asin in banned_asin:
                print(f"Skipping banned ASIN in URL collection: {asin}")
                continue
            product_urls.append(link["href"])

        return self.get_product_urls(
            self,
            url=base_amazon_url + product_urls[index],
            max=max,
            product_urls=product_urls,
            index=index + 1,
        )

    def __scrape_review_page(self, asin: string):
        print("ASIN: " + asin)
        link = base_review_url + asin
        self.driver.get(link, bypass_cloudflare=True)
        # TODO: Check if our request is blocked

        html = BeautifulSoup(self.driver.page_html, "html.parser")

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
