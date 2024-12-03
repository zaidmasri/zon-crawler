import asyncio
import json
from amazon_scraper import AmazonScraper, ScrapingConfig


async def main():
    config = ScrapingConfig(
        max_pages=10,
        max_workers=5,
        max_concurrent_requests=3,
        request_timeout=30,
        retry_attempts=3,
    )

    # asins = ["B0CT3Y5LL9", "B0CRDCXRK2"]
    asins = ["B0CRDCXRK2"]
    async with AmazonScraper(config) as scraper:
        results = await scraper.scrape_asins(asins)
        with open("sample_5.json", "w") as json_file:
            json.dump(results, json_file, indent=4)
    return results


if __name__ == "__main__":
    # This runs the main() coroutine until completion
    results = asyncio.run(main())
    print(f"Scraped {len(results)} products")  # For synchronous usage
# scraper = AmazonScraper()
# results = scraper.scrape_asins_concurrently(asins)
