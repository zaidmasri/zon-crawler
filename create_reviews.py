import json
import time
from amazon_scraper import AmazonScraper

start_time = time.time()
# asins = ["0596514522", "0609806483", "0071455531", "0764120964", "1853672831"] # concurrent
# asins = ["B0CT3Y5LL9"] # image test
asins = ["B084TM4XKG"]  # video test
az = AmazonScraper()
rtn = az.scrape_asins_concurrently(asins)
print(json.dumps(rtn, indent=4))

# Write the results to a JSON file
with open("sample_4.json", "w") as json_file:
    json.dump(rtn, json_file, indent=4)

print("Scraped data has been written to sample_4.json")
end_time = time.time()

print(f"time elapsed: {end_time - start_time}")
