class AmazonProduct:
    def __init__(self, asin: str):
        self.asin = asin
        self.name = ""
        self.overall_rating = 0.0
        self.total_rating_count = 0
        self.total_reviews_count = 0
        self.review_list = []
        self.failed_urls = []

    def __setitem__(self, key, value):
        setattr(self, key, value)

    def __getitem__(self, key):
        return getattr(self, key)

    def to_dict(self):
        return {
            "asin": self.asin,
            "name": self.name,
            "overall_rating": self.overall_rating,
            "total_rating_count": self.total_rating_count,
            "total_reviews_count": self.total_reviews_count,
            "review_list": [
                review.to_dict() for review in self.review_list
            ],  # Convert reviews to dicts
            "failed_urls": self.failed_urls,
        }
