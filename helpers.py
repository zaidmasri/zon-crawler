import re
from enum import Enum


def extract_integer(s):
    # This regex pattern looks for digits, possibly separated by commas
    pattern = r"(\d{1,3}(?:,\d{3})*)"
    match = re.search(pattern, s)

    if match:
        # Remove commas and return the integer as a string
        return int(match.group(0).replace(",", ""))
    return None


def extract_float_from_phrase(s):
    # Use regular expression to find the float value
    match = re.search(r"\d+\.\d+|\d+", s)
    if match:
        rating = float(match.group())
        return rating
    else:
        return None


class Review:
    def __init__(self):
        self.id = ""
        self.rating = 0
        self.title = ""
        self.href = ""
        self.country = ""
        self.date = None
        self.body = ""
        self.verified_purchase = False
        self.found_helpful = 0
        self.url = ""

    def to_dict(self):
        return {
            "id": self.id,
            "rating": self.rating,
            "title": self.title,
            "href": self.href,
            "country": self.country,
            "date": (
                str(self.date) if self.date else None
            ),  # Ensure date is serialized as string
            "body": self.body,
            "verified_purchase": self.verified_purchase,
            "found_helpful": self.found_helpful,
            "url": self.url,
        }


class Product:
    def __init__(self):
        self.asin = ""
        self.name = ""
        self.overall_rating = 0.0
        self.total_review_count = 0
        self.review_list = []

    def __setitem__(self, key, value):
        setattr(self, key, value)

    def __getitem__(self, key):
        return getattr(self, key)

    def to_dict(self):
        return {
            "asin": self.asin,
            "name": self.name,
            "overall_rating": self.overall_rating,
            "total_review_count": self.total_review_count,
            "review_list": [
                review.to_dict() for review in self.review_list
            ],  # Convert reviews to dicts
        }


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
