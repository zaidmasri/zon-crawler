class AmazonReview:
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
        self.product_url = ""
        self.username = ""
        self.username_url = ""
        self.images = []
        self.videos = []

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
            "product_url": self.product_url,
            "username": self.username,
            "username_url": self.username_url,
            "images": self.images,
            "videos": self.videos,
        }
