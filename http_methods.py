import asyncio
import base64
import os
import ssl
from typing import Optional
from urllib.parse import urlparse
import aiohttp
from scraping_config import ScrapingConfig


class HttpMethods:
    def __init__(self, config: Optional[ScrapingConfig] = None):
        self.config = config or ScrapingConfig()
        ssl_context = ssl.create_default_context()
        ssl_context.check_hostname = False
        ssl_context.verify_mode = ssl.CERT_NONE
        self.session = aiohttp.ClientSession(
            connector=aiohttp.TCPConnector(ssl=ssl_context)
        )
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.1.1 Safari/605.1.15",
        }
        self.cookies = {
            "session-id": os.getenv("AMAZON_SESSION_ID"),
            "session-token": os.getenv("AMAZON_TOKEN"),
            "session-id-time": "2082787201l",
            "csm-hit": "tb:s-XVTZMTMC0MQH2SD94GZA|1733432567463&t:1733432567569&adb:adblk_no",
            "i18n-prefs": "USD",
            "skin": "noskin",
            "ubid-main": "131-6582877-3983161",
            "lc-main": "en_US",
            "av-timezone": "America/Indianapolis",
            "at-main": "Atza|IwEBIERBQGDbtCI4CISTCd_PlCPnF-jh1YCtVujmzYCjvnI5WAhC7TnL8oOBJxhp74YfI1nEK9a0C3xQPnI9eeMWLSOxcfB6m-TvmzKy_4x4FwqGrYvQfEvXL4jPCDO1-7Yd9UZA0VZQUyA-Fn-lMpKEk0QXF_etLXiqcrLicKZWbbIZAvGxSdzyK66t6hfNwiJM2CTIW0_HnHszhc0o5G3qkItt2gGtXP4w3Odmh8CgruRMow",
            "sess-at-main": "+HAoKMGLZpO3/l0tEjT1paPvintgrxNOdDHhJqr4aQ4=",
            "sst-main": "Sst1|PQFwQGHFc_NTcqmeWoTc_H52CRf7n7_SHNX4FjJX9Erboq8CVVlx0Vz50qLGqk_uTTWL7VdF3yZAVIYjv0UMnaCP1EvI2Vuh0oWesOyAgPxUkAxJZ8Rg6hI2NcLy5wam4GZWLKHb8-ls8i3tuHySA9N9UUcbEO_QiHNjmM7CgekGHBK5bckNP5TmSz_LSXW6QfrlmD9Q1be1nP_zJJNc9B5e_ZRCeYyfhT9IxSvpqFXNve1M-CCSvgWPnIPLNL0nAi_mLcaV3-EsKF1zobNtdd9QemtvvrS3TK4j4ksO97e6CCU",
            "x-main": "gaQQ0V1@oiy5t2KAY4?1bQ5pi2@Jzh8z1f3JEwD0jGv0djSvhGxmNhGQ5mCQNAvY",
            "appstore-devportal-locale": "en_US",
            "_mkto_trk": "id:365-EFI-026&token:_mch-amazon.com-de91e154c048b644782603e76c4486b2",
            "at_check": "true",
            "s_plt": "2.47",
            "s_pltp": "undefined",
            "AMCVS_4A8581745834114C0A495E2B%40AdobeOrg": "1",
            "s_ips": "1134",
            "s_cc": "true",
            "AMCV_4A8581745834114C0A495E2B%40AdobeOrg": "179643557%7CMCIDTS%7C20049%7CMCMID%7C80552200343015942363501208162927885838%7CMCAAMLH-1732807500%7C9%7CMCAAMB-1732807500%7CRKhpRz8krg2tLO6pguXWp5olkAcUniQYPHaMWWgdJ3xzPWQmdj0y%7CMCOPTOUT-1732209901s%7CNONE%7CMCAID%7CNONE%7CvVersion%7C5.5.0",
            "x-amz-captcha-1": "1733459969656325",
            "x-amz-captcha-2": "fv2oLzT5IJ5lmHWdTfz4lw==",
        }

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.session.close()

    def encode_url_to_base64_filename(self, url: str) -> str:
        # Encode the URL to Base64
        base64_encoded = base64.urlsafe_b64encode(url.encode()).decode()
        # Truncate or adjust to avoid overly long filenames
        return base64_encoded[:255]

    async def get_and_download_url(self, url: str) -> Optional[str]:
        """
        Given a url it'll check if we've already downloaded the url.
        if so return without requesting a new page. Else download and return page from request.
        """

        # Validate URL format
        try:
            result = urlparse(url)
            if not all([result.scheme, result.netloc]):
                print(f"Invalid URL format: {url}")
                return None
        except Exception as e:
            print(f"URL parsing error: {repr(e)}")
            return None

        path = "./data/pfw/pages/"
        encoded_url = self.encode_url_to_base64_filename(url)
        files = os.listdir(path)

        if encoded_url in files:
            print("found in directory")
            with open(path + str(encoded_url)) as file:
                return file.read()

        for attempt in range(self.config.retry_attempts):
            try:
                async with self.session.get(
                    url=url,
                    headers=self.headers,
                    cookies=self.cookies,
                    timeout=self.config.request_timeout,
                ) as response:
                    if response.status == 200:
                        filename = self.encode_url_to_base64_filename(url)
                        with open(path + filename, "w+") as file:
                            resp = await response.text()
                            file.write(resp)
                            return resp
                    elif response.status == 404:
                        print(f"Page not found (404): {url}")
                        return None  # Don't retry on 404
                    elif response.status in [500, 502, 503, 504]:
                        if attempt < self.config.retry_attempts - 1:
                            wait_time = self.config.retry_delay * (attempt + 1)
                            print(
                                f"Server error {response.status}, retrying in {wait_time}s..."
                            )
                            await asyncio.sleep(wait_time)
                            continue
                    else:
                        print(f"HTTP {response.status} error while fetching {url}")
                        if attempt < self.config.retry_attempts - 1:
                            await asyncio.sleep(self.config.retry_delay * (attempt + 1))
                            continue
                        return None

            except aiohttp.ClientError as e:
                print(f"Network error: {repr(e)}")
                if attempt < self.config.retry_attempts - 1:
                    await asyncio.sleep(self.config.retry_delay * (attempt + 1))
                    continue
            except asyncio.TimeoutError:
                print(f"Request timed out for {url}")
                if attempt < self.config.retry_attempts - 1:
                    await asyncio.sleep(self.config.retry_delay * (attempt + 1))
                    continue
            except Exception as e:
                print(f"Unexpected error: {repr(e)}")
                return None
        return None
