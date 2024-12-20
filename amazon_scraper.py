import json
import os
from bs4 import BeautifulSoup
import asyncio
from typing import Optional, Dict, List

import pandas as pd
from helpers import (
    AmazonFilterFormatType,
    AmazonFilterMediaType,
    AmazonFilterSortBy,
    AmazonFilterStarRating,
    extract_float_from_phrase,
    extract_integer,
    parse_review_date_and_country,
    parse_reviews_count,
)
from amazon_product import AmazonProduct
from amazon_review import AmazonReview
from scraping_config import ScrapingConfig
from http_methods import HttpMethods
from tqdm import tqdm


class AmazonScraper:
    def __init__(self, config: Optional[ScrapingConfig] = None):
        self.config = config or ScrapingConfig()
        self.http_methods = HttpMethods(config=self.config)

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.http_methods:
            await self.http_methods.session.close()

    def __parse_review(self, review_element: BeautifulSoup) -> Optional[AmazonReview]:
        """Parse a single review"""
        try:
            review = AmazonReview()

            # Get review ID
            review.id = review_element.get("id")
            if not review.id:
                return None

            # Get review title and rating
            rating_element = review_element.find(
                "i", {"data-hook": "review-star-rating"}
            )
            if not rating_element:
                rating_element = review_element.find(
                    "i", {"data-hook": "cmps-review-star-rating"}
                )
            if rating_element:
                review.rating = extract_float_from_phrase(rating_element.get_text())

            # Get title
            title_element = review_element.find("a", {"data-hook": "review-title"})
            if not title_element:
                title_element = review_element.find(
                    "span", {"data-hook": "review-title"}
                )
            if title_element:
                review.href = title_element.get("href")
                if review.href:
                    spans = title_element.find_all("span")
                    if spans and len(spans) >= 3:
                        review.title = spans[2].get_text().strip()
                else:
                    review.title = title_element.get_text().strip()

            # Get review date and country
            date_element = review_element.find("span", {"data-hook": "review-date"})
            if date_element:
                date_info = parse_review_date_and_country(date_element.get_text())
                if date_info:
                    review.country = date_info["country"]
                    review.date = date_info["date"]

            # Get review body
            body_element = review_element.find("span", {"data-hook": "review-body"})
            if body_element:
                review.body = body_element.get_text().strip()

            # Check if verified purchase
            verified_element = review_element.find("span", {"data-hook": "avp-badge"})
            review.verified_purchase = bool(verified_element)

            # Get helpful votes
            helpful_element = review_element.find(
                "span", {"data-hook": "helpful-vote-statement"}
            )
            if helpful_element:
                text = helpful_element.get_text()
                if "One" in text:
                    review.found_helpful = 1
                else:
                    review.found_helpful = (
                        extract_integer(helpful_element.get_text()) or 0
                    )

            # Get username
            username_element = review_element.find("span", {"class": "a-profile-name"})
            if username_element:
                review.username = username_element.get_text()
                username_url = username_element.find_parent("a")
                if username_url:
                    review.username_url = username_url.get("href")

            # Get images
            image_elements = review_element.find_all(
                "img", {"data-hook": "review-image-tile"}
            )
            if image_elements:
                for element in image_elements:
                    src = element.get("src")
                    if src:
                        review.images.append(src)

            other_countries_images_elements = review_element.find_all(
                "img", {"data-hook": "cmps-review-image-tile"}
            )
            if other_countries_images_elements:
                for element in other_countries_images_elements:
                    src = element.get("src")
                    if src:
                        review.images.append(src)

            # Get videos
            if body_element:
                video_elements = body_element.find_all(
                    "div", {"data-review-id": review.id}
                )
                if video_elements:
                    for element in video_elements:
                        src = element.get("data-video-url")
                        if src:
                            review.videos.append(src)

            return review

        except Exception as e:
            print(f"Error parsing review: {e}")
            return None

    async def __process_page(
        self, url: str, asin: str, semaphore: asyncio.Semaphore
    ) -> tuple[str, Optional[str]]:
        """Process a single page with semaphore control"""
        async with semaphore:
            content = await self.http_methods.get_and_download_url(url)
            return url, content

    async def __scrape_product_reviews(
        self,
        asin: str,
        semaphore: asyncio.Semaphore,
        target_df: pd.DataFrame,
        progress_bar: Optional[tqdm] = None,
    ) -> AmazonProduct:
        tasks = []

        # Generate all URLs first
        for sort_by in AmazonFilterSortBy:
            for star_rating in AmazonFilterStarRating:
                for format_type in AmazonFilterFormatType:
                    for media_type in AmazonFilterMediaType:
                        for page_number in range(1, self.config.max_pages + 1):
                            url = f"https://www.amazon.com/product-reviews/{asin}?sortBy={sort_by.value}&pageNumber={page_number}&filterByStar={star_rating.value}&formatType={format_type.value}&mediaType={media_type.value}"
                            tasks.append(self.__process_page(url, asin, semaphore))

        # Process all pages concurrently
        results = await asyncio.gather(*tasks)

        product = AmazonProduct(asin=asin)

        # Process results
        for url, page_content in results:
            if progress_bar:
                progress_bar.update(1)

            if not page_content:
                product.failed_urls.append(url)
                continue

            soup = BeautifulSoup(page_content, "html.parser")

            # Update product info if not already set
            if product.name == "":
                product_element = soup.find("a", {"data-hook": "product-link"})
                if product_element:
                    product.name = product_element.get_text().strip()

            if product.overall_rating == 0:
                rating_element = soup.find("span", {"data-hook": "rating-out-of-text"})
                if rating_element:
                    product.overall_rating = extract_float_from_phrase(
                        rating_element.get_text()
                    )

            rating_count_element = soup.find("div", {"data-hook": "total-review-count"})
            if rating_count_element:
                count = extract_integer(rating_count_element.get_text())
                if count > product.total_rating_count:
                    product.total_rating_count = count

            total_reviews_count_element = soup.find(
                "div", {"data-hook": "cr-filter-info-review-rating-count"}
            )
            if total_reviews_count_element:
                count = parse_reviews_count(total_reviews_count_element.get_text())
                if count > product.total_reviews_count:
                    product.total_reviews_count = count

            # Parse reviews
            review_elements = soup.find_all("div", {"data-hook": "review"})
            for review_element in review_elements:
                review = self.__parse_review(review_element)
                if review:
                    review.found_under.append(url)
                    existing_review = next(
                        (r for r in product.review_list if r.id == review.id), None
                    )
                    if existing_review:
                        if url not in existing_review.found_under:
                            existing_review.found_under.append(url)
                    else:
                        product.review_list.append(review)

        self.__mark_complete(df=target_df, product=product)
        return product

    def __mark_complete(self, df: pd.DataFrame, product: AmazonProduct):
        print(
            f"Found {len(product.review_list)} unique reviews for ASIN {product.asin}"
        )
        # Ensure the directory exists
        output_dir = "./data/pfw/results/"
        os.makedirs(output_dir, exist_ok=True)

        # Write product data to a JSON file
        file_path = os.path.join(output_dir, f"{product['asin']}.json")
        with open(file_path, "w") as json_file:
            json.dump(product.to_dict(), json_file, indent=4)
            print(f"File successfully created: {file_path}")

        if len(product.review_list) == 0:
            print(f"no reviews found for: {product.asin}")
            return

        # Update the `review_complete` column for the current chunk
        asin_index = df.index[df["asin"] == product.asin]
        df.loc[asin_index, "review_complete"] = 1

        # Save updated DataFrame to a file (e.g., a checkpoint)
        df.to_pickle("./data/pfw/04_extract_reviews.pkl")
        df.to_csv("./data/pfw/04_extract_reviews.csv")
        print("Marked as complete and saved to disk.")

    async def scrape_asins(self, asins: List[str], target_df: pd.DataFrame):
        # Calculate total pages across all ASINs
        pages_per_asin = (
            len(AmazonFilterSortBy)
            * len(AmazonFilterStarRating)
            * len(AmazonFilterFormatType)
            * len(AmazonFilterMediaType)
            * self.config.max_pages
        )
        total_pages = len(asins) * pages_per_asin

        # Create progress bar
        progress_bar = tqdm(
            total=total_pages, desc="Scraping Progress", position=0, leave=True
        )

        # Create semaphore for controlling concurrent requests
        semaphore = asyncio.Semaphore(self.config.max_concurrent_requests)

        # Process all ASINs concurrently
        tasks = [
            self.__scrape_product_reviews(asin, semaphore, target_df, progress_bar)
            for asin in asins
        ]
        # products = await asyncio.gather(*tasks)
        await asyncio.gather(*tasks)

        progress_bar.close()
        # return [product.to_dict() for product in products if product]

    def scrape_asins_concurrently(self, asins: List[str]) -> List[Dict]:
        """Synchronous wrapper for backwards compatibility"""
        return asyncio.run(self.scrape_asins(asins))
