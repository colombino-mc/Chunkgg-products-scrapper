# ScrapyGIT

A Scrapy project that crawls [chunk.gg](https://chunk.gg) for Minecraft Marketplace product data and exports rich CSV snapshots. A Streamlit dashboard (`app.py`) is included for quick analysis of the collected dataset.

## How the Crawler Works
1. **Category scheduling:** By default the spider visits Mashups ? Add-Ons ? Worlds ? Textures ? Skins. You can override the order or select a subset with `-a categories=mashups,skins`.
2. **Listing crawl:** For each category, it paginates using chunk.gg’s query parameters (`?page=`) and queues every product card (`/@creator/product`). Pagination stops when the specified `max_pages` is reached or no new product URLs are discovered.
3. **Product parsing:** Each product page is parsed for:
   - visible badges (skin counts, player ranges)
   - JSON-LD and rating cards for price/rating metadata
   - Product Details card for minimum version & launch dates
   - Changelog and raw HTML sections for UUID, gallery, tags
   - Trailer widgets and YouTube stats when present

## Repository Structure
- `chunkgg/`
  - `chunkgg/spiders/marketplace.py` – spider logic and helpers
  - `chunkgg/items.py` – item schema consumed by the feed exporters
  - `products.csv` / `products_all.csv` / `products_all.jl` – exported data files (regenerated on crawl)
- `app.py` – Streamlit dashboard that consumes `products.csv`
- `requirements.txt` – Scrapy dependency pin (2.13.3)

## Setup
```bash
python -m venv venv
venv\Scripts\activate            # Windows PowerShell
pip install -r requirements.txt
```

## Running the Spider
```bash
cd chunkgg
# Full crawl (all categories) with default ordering
..\venv\Scripts\python -m scrapy crawl chunk_marketplace -O products.csv

# Limit to specific categories and first 10 pages in each
..\venv\Scripts\python -m scrapy crawl chunk_marketplace \
    -a categories=mashups,addons \
    -a max_pages=10 \
    -O chunkgg_mashups_addons.csv
```
The `-O` option overwrites the target CSV with UTF-8 encoded output. Scrapy will also emit a JSON Lines file (`products_all.jl`) if configured in `settings.py`.

## Output Fields
Every row in `products.csv` contains:
- Identity: `product_url`, `slug`, `category`, `creator`, `uuid`
- Description: summary text, tag list, gallery URLs, changelog (if published)
- Pricing: Minecoins, USD, EUR conversions, free flag
- Ratings: `rating_value`, `rating_count`, `rating_out_of`, `rating_breakdown` (JSON list of per-star stats)
- Timeline: launch date/time, last update date/time, minimum supported game version
- Extras: badge-derived `skin_count`, `player_range`, trailer presence + YouTube views/likes

## Streamlit Dashboard
After crawling, launch the dashboard to explore the dataset interactively:
```bash
streamlit run app.py
```
The app reads `chunkgg/products.csv`, normalises columns, and exposes filters by creator, tags, and currency selection.

## Notes
- chunk.gg does not expose download counts in static HTML; the scraper leaves `downloads` empty.
- Respect chunk.gg’s robots.txt and throttle guidelines; the spider defaults to 0.4s delay and obeys robots.txt.
- Regenerate the CSV (and rerun Streamlit) whenever you need fresh Marketplace data.
