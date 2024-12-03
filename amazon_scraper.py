import os
import ssl
from bs4 import BeautifulSoup
import asyncio
import aiohttp
from typing import Optional, Dict, List
from dataclasses import dataclass
from helpers import (
    AmazonFilterFormatType,
    AmazonFilterMediaType,
    AmazonFilterSortBy,
    AmazonFilterStarRating,
    extract_float_from_phrase,
    extract_integer,
    parse_review_date_and_country,
)
from amazon_product import AmazonProduct
from amazon_review import AmazonReview


@dataclass
class ScrapingConfig:
    max_pages: int = 10
    max_workers: int = 5
    max_concurrent_requests: int = 3
    request_timeout: int = 30
    retry_attempts: int = 3
    retry_delay: int = 1


class AmazonScraper:
    def __init__(self, config: Optional[ScrapingConfig] = None):
        self.config = config or ScrapingConfig()
        ssl_context = ssl.create_default_context()
        ssl_context.check_hostname = False
        ssl_context.verify_mode = ssl.CERT_NONE
        self.session = aiohttp.ClientSession(
            connector=aiohttp.TCPConnector(ssl=ssl_context)
        )
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36",
        }
        self.cookies = {
            "session-id": os.getenv("AMAZON_SESSION_ID"),
            "session-token": os.getenv("AMAZON_TOKEN"),
            "i18n-prefs": "USD",
            "skin": "noskin",
            "ubid-main": "132-8139505-0179230",
            "lc-main": "en_US",
            "av-timezone": "America/Indianapolis",
            "at-main": "Atza|IwEBIKwUfNTXyLhyUtWDwLm-OhLSMEFWVqf5ZJ-9zWNgUDAG1Cy3vsUsBNftXekacwztgitKcEMAZ9OgVMifQyuDBq8dOSinK8NDQfC5Z6KJnDtTMERcHujfQf2WDEogJy7Pq8c57tEn6fH_RA7GvDWcbM_jzguokpTuv4uMq_lnDw5HYGXPbm6GeuwgXHFZ_jtU1X2SIeGGqbHxHkl2qIQdjZ__KNanE26HyU5AK6nqX6_xA5wJKLiEntqX3-qPOF-QQZQ",
            "sess-at-main": '"liFtyHKrXtJyyOs0gYL3So4t7TlyUlC6vEaEmeITiQM="',
            "sst-main": "Sst1|PQFwQGHFc_NTcqmeWoTc_H52CRf7n7_SHNX4FjJX9Erboq8CVVlx0Vz50qLGqk_uTTWL7VdF3yZAVIYjv0UMnaCP1EvI2Vuh0oWesOyAgPxUkAxJZ8Rg6hI2NcLy5wam4GZWLKHb8-ls8i3tuHySA9N9UUcbEO_QiHNjmM7CgekGHBK5bckNP5TmSz_LSXW6QfrlmD9Q1be1nP_zJJNc9B5e_ZRCeYyfhT9IxSvpqFXNve1M-CCSvgWPnIPLNL0nAi_mLcaV3-EsKF1zobNtdd9QemtvvrS3TK4j4ksO97e6CCU",
            "session-id-time": "2082787201l",
            "x-main": "8wVqNxiOZwbL6bxOoTFJI@d9o@B4gPuL5a3Ru7QDH4FHIVAkKl7t9mEkUhZq8EJL",
            "appstore-devportal-locale": "en_US",
            "_mkto_trk": "id:365-EFI-026&token:_mch-amazon.com-de91e154c048b644782603e76c4486b2",
            "at_check": "true",
            "s_plt": "2.47",
            "s_pltp": "undefined",
            "AMCVS_4A8581745834114C0A495E2B%40AdobeOrg": "1",
            "s_ips": "1134",
            "s_cc": "true",
            "AMCV_4A8581745834114C0A495E2B%40AdobeOrg": "179643557%7CMCIDTS%7C20049%7CMCMID%7C80552200343015942363501208162927885838%7CMCAAMLH-1732807500%7C9%7CMCAAMB-1732807500%7CRKhpRz8krg2tLO6pguXWp5olkAcUniQYPHaMWWgdJ3xzPWQmdj0y%7CMCOPTOUT-1732209901s%7CNONE%7CMCAID%7CNONE%7CvVersion%7C5.5.0",
        }
        self._review_cache = {}

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.session.close()

    def _parse_review(self, review_element: BeautifulSoup) -> Optional[AmazonReview]:
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
                    if spans and len(spans) > 3:
                        review.title = spans[3].get_text().strip()
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
                review.found_helpful = extract_integer(helpful_element.get_text()) or 0

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

    async def _fetch_page(self, url: str) -> Optional[str]:
        """Fetch a single page with retry logic and rate limiting"""
        for attempt in range(self.config.retry_attempts):
            try:
                async with self.session.get(
                    url,
                    headers=self.headers,
                    cookies=self.cookies,
                    timeout=self.config.request_timeout,
                ) as response:
                    if response.status == 200:
                        return await response.text()
                    elif response.status == 429:
                        await asyncio.sleep(self.config.retry_delay * (attempt + 1))
                        continue
                    else:
                        print(f"Failed to fetch {url}: Status {response.status}")
                        return None
            except Exception as e:
                print(f"Error fetching {url}: {e}")
                if attempt < self.config.retry_attempts - 1:
                    await asyncio.sleep(self.config.retry_delay * (attempt + 1))
                    continue
        return None

    async def _scrape_product_reviews(self, asin: str) -> AmazonProduct:
        product = AmazonProduct()
        product.asin = asin

        tasks = []
        urls = []  # List to track URLs

        for sort_by in AmazonFilterSortBy:
            for star_rating in AmazonFilterStarRating:
                for format_type in AmazonFilterFormatType:
                    for media_type in AmazonFilterMediaType:
                        for page_number in range(1, self.config.max_pages + 1):
                            url = f"https://www.amazon.com/product-reviews/{asin}?sortBy={sort_by.value}&pageNumber={page_number}&filterByStar={star_rating.value}&formatType={format_type.value}&mediaType={media_type.value}"
                            urls.append(url)
                            tasks.append(self._fetch_page(url))

        pages = await asyncio.gather(*tasks)

        for url, page_content in zip(urls, pages):
            if page_content:
                soup = BeautifulSoup(page_content, "html.parser")

                # Update product info if not already set
                if not product.name:
                    product_element = soup.find("a", {"data-hook": "product-link"})
                    if product_element:
                        product.name = product_element.get_text().strip()

                if not product.overall_rating:
                    rating_element = soup.find(
                        "span", {"data-hook": "rating-out-of-text"}
                    )
                    if rating_element:
                        product.overall_rating = extract_float_from_phrase(
                            rating_element.get_text()
                        )

                if not product.total_review_count:
                    review_count_element = soup.find(
                        "div", {"data-hook": "total-review-count"}
                    )
                    if review_count_element:
                        product.total_review_count = extract_integer(
                            review_count_element.get_text()
                        )

                # Parse reviews
                review_elements = soup.find_all("div", {"data-hook": "review"})
                for review_element in review_elements:
                    review = self._parse_review(review_element)
                    if review:
                        # Add the current URL to found_under
                        review.found_under.append(url)

                        # Check if this review ID already exists
                        existing_review = next(
                            (r for r in product.review_list if r.id == review.id), None
                        )

                        if existing_review:
                            # Add new URL to existing review's found_under if not already present
                            # if url not in existing_review.found_under:
                            existing_review.found_under.append(url)
                        else:
                            # Add new review to the list
                            product.review_list.append(review)

        print(f"Found {len(product.review_list)} unique reviews for ASIN {asin}")
        return product

    async def scrape_asins(self, asins: List[str]) -> List[Dict]:
        tasks = [self._scrape_product_reviews(asin) for asin in asins]
        products = await asyncio.gather(*tasks)
        return [product.to_dict() for product in products if product]

    def scrape_asins_concurrently(self, asins: List[str]) -> List[Dict]:
        """Synchronous wrapper for backwards compatibility"""
        return asyncio.run(self.scrape_asins(asins))
