import asyncio
import json
import os
import time
from amazon_scraper import AmazonScraper, ScrapingConfig


async def main():
    start_time = time.time()

    config = ScrapingConfig(
        max_pages=10,
        max_workers=5,
        # max_concurrent_requests=3,
        request_timeout=30,
        retry_attempts=3,
    )

    asins = ["B0CT3Y5LL9", "B0CRDCXRK2"]
    # asins = ["B0CRDCXRK2"]
    async with AmazonScraper(config) as scraper:
        results = await scraper.scrape_asins(asins)
        for product in results:
            # Ensure the directory exists
            output_dir = "./data/pfw/results/"
            os.makedirs(output_dir, exist_ok=True)

            # Write product data to a JSON file
            file_path = os.path.join(output_dir, f"{product['asin']}.json")
            with open(file_path, "w") as json_file:
                json.dump(product, json_file, indent=4)

            print(f"File successfully created: {file_path}")

    end_time = time.time()
    elapsed_time = end_time - start_time

    print(f"Elapsed time: {elapsed_time} seconds")
    return results


if __name__ == "__main__":
    # This runs the main() coroutine until completion
    results = asyncio.run(main())
    print(f"Scraped {len(results)} products")

# For synchronous usage
# scraper = AmazonScraper()
# results = scraper.scrape_asins_concurrently(asins)
