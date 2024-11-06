from datetime import datetime
import re
import string
from typing import Coroutine
from botasaurus_driver import Driver, Wait
from bs4 import BeautifulSoup
from helpers import extract_float_from_phrase, extract_integer
from constants import BASE_AMAZON_URL, BASE_REVIEW_URL

banned_asin = ["B0D5BTBHBK", "B0DHRXRJ9X", "B0DG2MSMD2", "B0CW1LC1SP"]


class Server:
    driver: Driver
    conn: Coroutine

    def __init__(self, driver: Driver, db: Coroutine):
        self.driver = driver
        self.conn = db

    async def gen_products(self):
        try:
            urls = await self.__get_product_urls(
                max=200,
                product_urls=[],
                index=0,
                url="https://www.amazon.com/dp/B0BQHBWPYX/",
            )
            print(str(len(urls)))
        except Exception as e:
            print(f"Error getting product URLs: {e}")
            urls = []

        for url in urls:
            full_url = BASE_AMAZON_URL + url
            print("Navigating to URL:")
            print(full_url)

            # Use the helper function to get the HTML content with retries
            html = await self.__fetch_page_with_retry(full_url)
            if not html:
                print(f"Skipping URL {full_url} due to repeated errors.")
                continue

            # Parsing data off page.
            asin = html.find("input", id="ASIN", attrs={"type": "hidden"})
            if asin:
                print("ASIN: " + asin["value"])
            else:
                print("ASIN not found on page.")

            product_name = html.find("span", {"id": "productTitle"})
            if product_name:
                print(f"Product Name: {product_name.get_text()}")
            else:
                print("Product name not found on page.")

            # Adding to DB if both ASIN and product name are found
            print("Adding to DB")
            if asin and product_name:
                try:
                    await self.__db_create_product(
                        asin["value"],
                        product_name.get_text(),
                    )
                    print(f"ASIN: {asin["value"]} added to db.")
                except Exception as e:
                    print(f"Error adding product to database: {e}")

    async def gen_reviews(self):
        """
        Uses __db_get_products().
        Then scrapes every product by asin
        """
        today_date = datetime.now()
        print("Run date: " + str(today_date))
        try:
            products = await self.__db_get_products()
            for product in products or []:
                asin = product.get("asin")
                self.__scrape_review_page(asin)
        except Exception as e:
            print(f"Error in gen_reviews: {e}")
        finally:
            self.driver.close()

    async def __get_product_urls(
        self, max: int, product_urls: list[str], index: int, url=BASE_AMAZON_URL
    ):
        """
        Will return an array of urls of amazon products
        """
        try:
            if len(product_urls) >= max:
                return product_urls

            print(f"Searching for products on the following page: {url}")
            html = await self.__fetch_page_with_retry(url)
            urls = html.find_all("a", href=re.compile(r"/(dp)/"))
            for url in urls:
                asin = url["href"].split("/dp/")[1].split("/")[0]
                if asin in banned_asin:
                    print(f"Skipping banned ASIN in URL collection: {asin}")
                    continue
                product_urls.append(url["href"])
            print(f"Product URLS: {str(len(product_urls))}")
            return await self.__get_product_urls(
                url=BASE_AMAZON_URL + product_urls[index],
                max=max,
                product_urls=product_urls,
                index=index + 1,
            )
        except Exception as e:
            print(f"Error in __get_product_urls: {e}")
            return product_urls

    def __scrape_review_page(self, asin: string):
        print("ASIN: " + asin)
        try:
            link = BASE_REVIEW_URL + asin
            html = self.__fetch_page_with_retry(link)
            product_name = html.find(attrs={"data-hook": "product-link"})
            print(
                "Product Name: " + (product_name.get_text() if product_name else "N/A")
            )

            overall_rating = html.find(attrs={"data-hook": "rating-out-of-text"})
            print(
                "Overall Rating: "
                + str(
                    extract_float_from_phrase(overall_rating.get_text())
                    if overall_rating
                    else "N/A"
                )
            )

            total_review_count = html.find(attrs={"data-hook": "total-review-count"})
            print(
                "Total Review Count: "
                + (
                    extract_integer(total_review_count.get_text())
                    if total_review_count
                    else "N/A"
                )
            )

            print("Starting to analyze reviews... ")

            review_list = html.find_all(attrs={"data-hook": "review"})
            for review in review_list:
                review_id = review.get("id", "N/A")
                print("Review ID: " + review_id)

                review_title = review.find(attrs={"data-hook": "review-title"})
                if review_title:
                    review_href = review_title.get("href", "N/A")
                    print("Review href: " + review_href)
                    print(
                        "Review Rating: "
                        + str(
                            extract_float_from_phrase(
                                review_title.contents[0].get_text()
                            )
                        )
                    )
                    print("Review Title: " + review_title.contents[3].get_text())
                else:
                    print("Review title not found.")

                review_date_field = review.find(attrs={"data-hook": "review-date"})
                match = (
                    re.search(
                        r"Reviewed in (.+?) on (.+)", review_date_field.get_text()
                    )
                    if review_date_field
                    else None
                )
                if match:
                    country = match.group(1)
                    date = match.group(2)
                    print(f"Review Country: {country}")
                    print(f"Review Date: {date}")
                else:
                    print("Pattern not found for review date.")

                review_body = review.find(attrs={"data-hook": "review-body"})
                print(
                    "Review Body: " + (review_body.get_text() if review_body else "N/A")
                )

                verified_purchase = review.find(attrs={"data-hook": "avp-badge"})
                print(
                    "Verified Purchase: "
                    + (verified_purchase.get_text() if verified_purchase else "N/A")
                )

                found_helpful = review.find(
                    attrs={"data-hook": "helpful-vote-statement"}
                )
                print(
                    "Found Helpful: "
                    + (found_helpful.get_text() if found_helpful else "null")
                )

        except Exception as e:
            print(f"Error scraping review page for ASIN {asin}: {e}")

    async def __db_create_product(self, asin: string, name: string):
        try:
            await self.conn.execute(
                """
                    INSERT INTO products (asin, name) 
                    VALUES ($1, $2)
                """,
                asin,
                name,
            )
        except Exception as e:
            print(f"Error creating product with ASIN {asin}: {e}")

    async def __db_get_products(self):
        try:
            values = await self.conn.fetch("SELECT * FROM products")
            await self.conn.close()
            return values
        except Exception as e:
            print(f"Error fetching products: {e}")

    async def __fetch_page_with_retry(self, full_url, max_retries=5):
        """Helper function to handle CAPTCHA retry logic."""
        retry_count = 0

        while retry_count < max_retries:
            try:
                self.driver.google_get(
                    link=full_url, wait=Wait.SHORT, bypass_cloudflare=True
                )
                html = BeautifulSoup(self.driver.page_html, "html.parser")

                # Check for CAPTCHA
                if html.find(id="captchacharacters"):
                    retry_count += 1
                    print(f"BOT DETECTED... retrying {retry_count}/{max_retries}")
                    continue  # Retry the loop if CAPTCHA is detected

                # Return HTML if no CAPTCHA
                return html

            except Exception as e:
                print(f"Error loading URL {full_url}: {e}")
                return None  # Exit if there's another error

        # Return None if max retries reached
        print(f"Max retries reached for {full_url}.")
        return None
