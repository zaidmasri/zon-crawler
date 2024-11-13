# Zon Crawler

Zon Crawler is a data collection tool designed to extract product reviews from the Amazon USA store (amazon.com) for comparative analysis. This project aims to investigate the statistical significance of the Federal Trade Commission's recent ruling banning fake reviews and testimonials, and its potential impact on consumer behavior and review authenticity on Amazon.

## Project Overview

In light of the FTC's emphasis on transparency in online reviews, Zon Crawler facilitates the collection of authentic user experiences. Our goal is to analyze whether the new regulations have led to measurable changes in review patterns, sentiment, and overall consumer trust on Amazon, compared to the Amazon Canada store (amazon.ca).

# Getting Started

1. Install `pipenv` on your machine
2. Run `pipenv install` in the root directory of the project
3. Create a `.env` file. You can copy the `.env.example` file and fill in the variables for your postgres set DB.

# Running Scripts

There are two ways you can run the code. One for generating products and the other for generating reviews:

1. Generating Products

```python
   python3 ./main.py gen-products
```

2. Generating Reviews

```python
     python3 ./main.py gen-reviews
```

# Requirements:

- [ ] Start Date for reviews = Oct, 1 2024
- [ ] End Date for reviews = Nov, 2024 (Don't grab new reviews from either group)

- [x] Verified Purchase
- [x] Found Helpful
- [ ] Iterate over all review pages
  - [ ] changing the filter input
  - [ ] check if review is recorded already and within start and end date requirements
- [ ] If Pictures Exist
- [ ] If Video Exist
- [ ] Grab Links for Picture
- [ ] Grab Links for Video
- [x] Product Overall Rating
  - [x] Convert to float
- [x] Review ID
- [x] Review Link
- [x] Country of Review
  - [x] Requires splitting string with date of review
- [x] Review Date
  - [x] Requires splitting string with review date
- [x] Review Rating
  - [x] Convert to float
- [x] Review Title
- [x] Review Description
- [x] Run Date
- [ ] If initial request is blocked we must restart the script until amazon lets us through
- [ ] Using a crawler Seed database with 100,000 amazon products
  - [ ] Control Group
  - [ ] Target Group
- [ ] Build database schema
  - [ ] Error Logs
    - [ ] Created At
    - [ ] Error Message
  - [ ] Products
    - [ ] ID (internal)
    - [ ] asin
    - [ ] name
    - [ ] overall rating
    - [ ] number of ratings
    - [ ] number of reviews
  - [ ] Reviews
    - [ ] username
    - [ ] title
    - [ ] body
    - [ ] is verified
    - [ ] country
    - [ ] date
    - [ ] created at (in our system)
    - [ ] rating
    - [ ] id (from amazon)
    - [ ] url
  - [ ] Review Media
    - [ ] review id
    - [ ] url
  - [ ] Run Summary
    - [ ] Errored out?
    - [ ] Products Checked
    - [ ] Created At
    - [ ] Last Checked Product ID
- [ ] Insert reviews into database
