import re
import os
import requests
from enum import Enum
from bs4 import BeautifulSoup
from datetime import datetime
from helpers import Product, Review, extract_float_from_phrase, extract_integer


class AmazonFilterMediaType(Enum):
    MEDIA_REVIEWS_ONLY = "media_reviews_only"
    ALL_CONTENTS = "all_contents"


class AmazonFilterSortBy(Enum):
    RECENT = "recent"
    HELPFUL = "helpful"


class AmazonFilterStarRating(Enum):
    ALL_STAR = "all_star"
    FIVE_STAR = "five_star"
    FOUR_STAR = "four_star"
    THREE_STAR = "three_star"
    TWO_STAR = "two_star"
    ONE_STAR = "one_star"
    POSITIVE = "positive"
    CRITICAL = "critical"


class AmazonFilterFormatType(Enum):
    ALL_FORMATS = "all_formats"
    CURRENT_FORMAT = "current_format"


class AmazonScraper:
    def __init__(self):
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36",
        }
        self.cookies = {
            "session-id": os.getenv("AMAZON_SESSION_ID"),
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
            "session-token": os.getenv("AMAZON_TOKEN"),
        }

    def parse_review_date(self, date_text):
        if not date_text:
            return None
        try:
            # First try the standard format
            match = re.search(r"Reviewed in (.+?) on (.+)", date_text)
            if match:
                date_str = match.group(2)
                return {
                    "country": match.group(1),
                    "date": datetime.strptime(date_str, "%B %d, %Y"),
                }

            # Try alternate format if standard fails
            match = re.search(r"Reviewed on (.+)", date_text)
            if match:
                date_str = match.group(1)
                return {
                    "country": "Unknown",
                    "date": datetime.strptime(date_str, "%B %d, %Y"),
                }
        except ValueError as e:
            print(f"Date parsing error: {e} for text: {date_text}")
        return None

    def parse_review(self, review_element):
        review = Review()

        try:
            review.id = review_element.get("id", "N/A")

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

            title_element = review_element.find("a", {"data-hook": "review-title"})
            if not title_element:
                title_element = review_element.find(
                    "span", {"data-hook": "review-title"}
                )

            if title_element:
                review.title = title_element.contents[3].get_text().strip()
                review.href = title_element.get("href", "N/A")

            # Get review date and country
            date_element = review_element.find("span", {"data-hook": "review-date"})
            if date_element:
                date_info = self.parse_review_date(date_element.get_text())
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
                helpful_text = helpful_element.get_text()
                review.found_helpful = extract_integer(helpful_text) or 0

            return review

        except Exception as e:
            print(f"Error parsing review: {e}")
            return review

    def scrape_review_page(self, page_content):
        product = Product()

        try:
            html = BeautifulSoup(page_content, "html.parser")

            # Debug print
            print("HTML length:", len(page_content))

            # Get product name
            product_element = html.find("a", {"data-hook": "product-link"})
            if product_element:
                product.name = product_element.get_text().strip()
            else:
                print("Product name element not found")

            # Get overall rating
            rating_element = html.find("span", {"data-hook": "rating-out-of-text"})
            if rating_element:
                product.overall_rating = extract_float_from_phrase(
                    rating_element.get_text()
                )
            else:
                print("Rating element not found")

            # Get total review count
            review_count_element = html.find("div", {"data-hook": "total-review-count"})
            if review_count_element:
                product.total_review_count = extract_integer(
                    review_count_element.get_text()
                )
            else:
                print("Review count element not found")

            # Parse each review
            review_elements = html.find_all("div", {"data-hook": "review"})
            print(f"Found {len(review_elements)} review elements")

            for review_element in review_elements:
                review = self.parse_review(review_element)
                if review:
                    product.review_list.append(review)

            return product

        except Exception as e:
            print(f"Error scraping review page: {e}")
            return None

    def scrape_product_reviews(self, asin, max_pages=1):
        product = Product()  # Create a Product object to store all details
        for sort_by in AmazonFilterSortBy:
            for star_rating in AmazonFilterStarRating:
                for format_type in AmazonFilterFormatType:
                    for media_type in AmazonFilterMediaType:
                        print(f"Scraping reviews sorted by: {sort_by.value}")
                        for page_number in range(1, max_pages + 1):
                            print(
                                f"Scraping page {page_number} for sort by {sort_by.value} and star rating {star_rating.value} and format type {format_type.value}"
                            )
                            url = f"https://www.amazon.com/product-reviews/{asin}?sortBy={sort_by.value}&pageNumber={page_number}&filterByStar={star_rating.value}&formatType={format_type.value}&mediaType={media_type.value}"
                            print(f"URL: {url}")
                            try:
                                response = requests.get(
                                    url,
                                    headers=self.headers,
                                    cookies=self.cookies,
                                )

                                if response.status_code == 200:
                                    print(f"Page {page_number} scraped successfully")
                                    page_product = self.scrape_review_page(
                                        response.text
                                    )

                                    if page_product:
                                        if not product.name:
                                            product.name = page_product.name
                                        if not product.asin:
                                            product.asin = asin
                                        if not product.overall_rating:
                                            product.overall_rating = (
                                                page_product.overall_rating
                                            )
                                        if not product.total_review_count:
                                            product.total_review_count = (
                                                page_product.total_review_count
                                            )

                                        # Add reviews from the current page
                                        product.review_list.extend(
                                            page_product.review_list
                                        )
                                    else:
                                        print(f"No reviews found on page {page_number}")
                                else:
                                    print(
                                        f"Failed to fetch page {page_number}: Status code {response.status_code}"
                                    )
                                    break  # Exit loop if there's an issue with the page

                            except requests.exceptions.RequestException as e:
                                print(f"Request failed on page {page_number}: {e}")
                                break  # Exit loop on request failure

        print(f"Total reviews scraped: {len(product.review_list)}")
        return product  # Return the Product object with all reviews
