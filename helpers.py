from datetime import datetime
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


def parse_review_date_and_country(date_text):
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

def parse_reviews_count(phrase: str) -> int:
    """
    Parses the number of reviews from a given phrase.

    Args:
        phrase (str): The input phrase, e.g., "1,473 total ratings, 520 with reviews".

    Returns:
        int: The number of reviews, or 0 if not found.
    """
    match = re.search(r'(\d[\d,]*) with reviews', phrase)
    if match:
        # Remove commas and convert to integer
        return int(match.group(1).replace(',', ''))
    return 0

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
