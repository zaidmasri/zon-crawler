import asyncio
import time
import pandas as pd
from amazon_scraper import AmazonScraper, ScrapingConfig

chunk_size = 5
max_pages = 10
max_workers = 10
request_timeout = 60
retry_attempts = 3


# Function to split DataFrame into chunks
def split_dataframe(df: pd.DataFrame, chunk_size: int) -> list[pd.DataFrame]:
    return [df.iloc[i : i + chunk_size] for i in range(0, len(df), chunk_size)]


def mark_complete(df: pd.DataFrame):
    # Save updated DataFrame to a file (e.g., a checkpoint)
    df.to_pickle("./data/pfw/04_extract_reviews.pkl")
    df.to_csv("./data/pfw/04_extract_reviews.csv")
    print("Marked as complete and saved to disk.")


async def main():

    df = pd.read_pickle("./data/pfw/04_extract_reviews.pkl")

    if not isinstance(df, pd.DataFrame):
        raise Exception("df is not a pd.DataFrame", type(df))
    # Filter for rows that have not been scraped yet
    if "review_complete" not in df.columns:
        raise Exception("df does not contain a column called review_complete")

    filtered_df = df[df["review_complete"] != 1]

    if filtered_df.empty:
        print("All ASINs have been scraped.")
        return

    config = ScrapingConfig(
        max_pages=max_pages,
        max_workers=max_workers,
        max_concurrent_requests=50,
        request_timeout=request_timeout,
        retry_attempts=retry_attempts,
    )
    # Split the DataFrame into chunks
    chunks = split_dataframe(filtered_df, chunk_size)

    for chunk in chunks[:1]:
        # asins = chunks[0]["asin"]
        start_time = time.time()

        async with AmazonScraper(config) as scraper:
            results = await scraper.scrape_asins(chunk["asin"])
            for product in results:
                # Update the `review_complete` column for the current chunk
                asin_index = df.index[df["asin"] == product["asin"]]
                df.loc[asin_index, "review_complete"] = 1
        mark_complete(df)
        end_time = time.time()
        elapsed_time = end_time - start_time

        print(f"time elapsed {elapsed_time}")


asyncio.run(main())
