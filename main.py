import os
import asyncio
import string
import asyncpg
import re
from datetime import datetime
from botasaurus_driver import Driver, Wait
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from helpers import extract_float_from_phrase, extract_integer
from server import Server

load_dotenv()

base_amazon_url = "https://www.amazon.com/"
base_product_url = base_amazon_url + "dp/"
base_review_url = base_amazon_url + "product-reviews/"
# Headers rotation
user_agents = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:66.0) Gecko/20100101 Firefox/66.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/84.0.4147.135 Safari/537.36",
    # add more user agents
]

banned_asin = ["B0D5BTBHBK", "B0DHRXRJ9X"]


def scrape_review_page(asin: string, server: Server):
    print("ASIN: " + asin)
    link = base_review_url + asin
    server.driver.get(link, bypass_cloudflare=True)
    # TODO: Check if our request is blocked

    html = BeautifulSoup(server.driver.page_html, "html.parser")

    product_name = html.find(attrs={"data-hook": "product-link"})
    print("Product Name: " + product_name.get_text())

    overall_rating = html.find(attrs={"data-hook": "rating-out-of-text"})
    print(
        "Overall Rating: " + str(extract_float_from_phrase(overall_rating.get_text()))
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
        match = re.search(r"Reviewed in (.+?) on (.+)", review_date_field.get_text())

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


# Uses get_products
# Then scrapes every product by asin
async def run_scrapper(server: Server):
    today_date = datetime.now()
    print("Run date: " + str(today_date))
    products = await server.get_products()
    for product in products:
        asin = product.get("asin")
        scrape_review_page(asin, server)

    server.driver.close()


def get_product_urls(
    url: string, max: int, product_urls: list[str], server: Server, index: int
):
    if len(product_urls) >= max:
        # driver.close()
        return product_urls

    server.driver.get(url, wait=Wait.LONG)
    html = BeautifulSoup(server.driver.page_html, "html.parser")

    urls = html.find_all("a", href=re.compile(r"/(dp)/"))
    for link in urls:
        asin = link["href"].split("/dp/")[1].split("/")[0]
        # Skip banned ASINs
        if asin in banned_asin:
            print(f"Skipping banned ASIN in URL collection: {asin}")
            continue
        product_urls.append(link["href"])

    return get_product_urls(
        url=base_amazon_url + product_urls[index],
        max=max,
        product_urls=product_urls,
        server=server,
        index=index + 1,
    )


async def main():
    conn = await asyncpg.connect(
        user=os.getenv("PG_USER"),
        password=os.getenv("PG_PASSWORD"),
        database=os.getenv("PG_DATABASE"),
        host=os.getenv("PG_HOST"),
        port=os.getenv("PG_PORT"),
    )
    driver = Driver(user_agent=user_agents[0], headless=False, beep=True)
    srv = Server(db=conn, driver=driver)

    # await run_scrapper(driver)
    urls = get_product_urls(base_amazon_url, 10, [], srv, 1)
    print(str(len(urls)))

    for url in urls:
        full_url = base_amazon_url + url
        print("Navigating to URL:")
        print(full_url)
        driver.get(full_url, wait=Wait.LONG)
        html = BeautifulSoup(driver.page_html, "html.parser")

        # Parsing data off page.
        asin = html.find("input", id="ASIN", attrs={"type": "hidden"})
        print("ASIN: " + asin["value"])

        product_name = html.find("span", {"id": "productTitle"})
        print("Product Name: " + product_name.get_text())

        print("Adding to DB")
        await conn.execute(
            """
                INSERT INTO products (asin, name) 
                VALUES ($1, $2)
                ON CONFLICT (asin) DO NOTHING
            """,
            asin["value"],
            product_name.get_text(),
        )
        print("ASIN: " + asin["value"] + " added to db.")


asyncio.run(main())
