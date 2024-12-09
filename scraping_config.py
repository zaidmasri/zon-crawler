from dataclasses import dataclass


@dataclass
class ScrapingConfig:
    max_pages: int = 10
    max_workers: int = 5
    # max_concurrent_requests: int = 3
    request_timeout: int = 30
    retry_attempts: int = 3
    retry_delay: int = 1

