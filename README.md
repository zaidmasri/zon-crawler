# Zon Crawler

# Getting Started

1. Install `pipenv` on your machine
2. Run `pipenv install` in the root directory of the project
3. Create a `.env` file. You can copy the `.env.example` file and fill in the variables for your postgres set DB.
4. Run the script via `python3 ./script.py`

Requirements:

- [ ] Start Date for reviews = Jan, 2022
- [ ] End Date for reviews = Nov, 2024 (Don't grab new reviews from either group)

- [ ] Verified Purchase
- [ ] Found Helpful
- [ ] If Pictures Exist
- [ ] If Video Exist
- [ ] Grab Links for Picture
- [ ] Grab Links for Video
- [x] Product Overall Rating
  - [ ] Convert to integer
- [x] Review ID
- [x] Review Link
- [ ] Country of Review
- [x] Review Rating
  - [ ] Convert to integer
- [x] Review Title
- [x] Review Description
- [ ] Run Date
- [ ] If initial request is blocked we must restart the script until amazon lets us through
