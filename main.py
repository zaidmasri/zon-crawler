import os
import asyncio
import sys
import asyncpg
from botasaurus_driver import Driver, Wait
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from server import Server
from constants import BASE_PRODUCT_URL

load_dotenv()


# Headers rotation
user_agents = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:66.0) Gecko/20100101 Firefox/66.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/84.0.4147.135 Safari/537.36",
    # add more user agents
]


async def main():
    if len(sys.argv) < 2:
        print("Usage: main.py <command> [options]")
        return

    conn = await asyncpg.connect(
        user=os.getenv("PG_USER"),
        password=os.getenv("PG_PASSWORD"),
        database=os.getenv("PG_DATABASE"),
        host=os.getenv("PG_HOST"),
        port=os.getenv("PG_PORT"),
    )
    driver = Driver(user_agent=user_agents[0], headless=True, beep=True)
    srv = Server(db=conn, driver=driver)

    command = sys.argv[1]
    if command == "gen-reviews":
        await srv.run_scrapper()
    elif command == "gen-products":
        urls = srv.get_product_urls(BASE_PRODUCT_URL, 10, [], 0)
        print(str(len(urls)))

        for url in urls:
            full_url = BASE_PRODUCT_URL + url
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
            await srv.create_product(
                asin["value"],
                product_name.get_text(),
            )
            print("ASIN: " + asin["value"] + " added to db.")
    else:
        print("Unknown command:", command)


asyncio.run(main())
