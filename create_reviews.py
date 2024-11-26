import json
from amazon_scraper import AmazonScraper

# asins = ["0596514522", "0609806483", "0071455531", "0764120964", "1853672831"]
asins = ["0596514522"]
az = AmazonScraper()
rtn = az.scrape_asins_concurrently(asins)
print(json.dumps(rtn, indent=4))

# Write the results to a JSON file
with open("sample_2.json", "w") as json_file:
    json.dump(rtn, json_file, indent=4)

print("Scraped data has been written to sample_2.json")