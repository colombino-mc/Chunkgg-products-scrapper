import re
import scrapy
from urllib.parse import urljoin
from chunkgg.items import ProductItem

PRODUCT_PATH_RE = re.compile(r"^/@[a-z0-9-]+/[^/]+$", re.I)

class ChunkProductsSpider(scrapy.Spider):
    name = "chunk_products"
    allowed_domains = ["chunk.gg"]
    start_urls = [
        "https://chunk.gg/arrivals",
        "https://chunk.gg/trendy",
        "https://chunk.gg/popular",
        "https://chunk.gg/addons",
        "https://chunk.gg/worlds",
        "https://chunk.gg/mashups",
        "https://chunk.gg/textures",
        "https://chunk.gg/skins",
    ]

    custom_settings = {
        "ROBOTSTXT_OBEY": True,
        "DOWNLOAD_DELAY": 0.75,    # be polite
        "AUTOTHROTTLE_ENABLED": True,
        "DEFAULT_REQUEST_HEADERS": {
            "User-Agent": "Mozilla/5.0 (compatible; ChunkResearchBot/1.0; +your_email@example.com)"
        },
    }

    def parse(self, response):
        # 1) Find product links on listing pages
        # Links on chunk.gg point to things like /@giggle-block-studios/soul-seekers (see example page)
        for a in response.css('a[href]::attr(href)').getall():
            if PRODUCT_PATH_RE.match(a):
                yield response.follow(a, callback=self.parse_product)

        # 2) (Optional) discover more listing pages if pagination exists
        # If the site exposes more pages via standard <a> links, follow them here.
        # Example: for safety, also follow category links you haven't listed
        for cat in response.css('a[href^="/"]:not([href^="/@"])::attr(href)').getall():
            url = urljoin(response.url, cat)
            # keep it within domain and avoid loops
            if any(url.endswith(path) for path in ("/arrivals","/trendy","/popular","/addons","/worlds","/mashups","/textures","/skins")):
                yield response.follow(url, callback=self.parse)

    def parse_product(self, response):
        item = ProductItem()
        item["url"] = response.url

        # Title (H1 heading like `# Soul Seekers`)
        title = response.css("h1::text, h1 *::text").get()
        item["title"] = title.strip() if title else None

        # Creator (near title, often clickable creator link)
        creator = response.css('a[href*="@"]::text').get()
        item["creator"] = creator.strip() if creator else None

        # Category label (e.g., "Minecraft Addon Add-On") appears near price/category badges
        category = response.xpath('//*[contains(text(),"Minecraft") and contains(text(),"Add-On") or contains(text(),"World") or contains(text(),"Mash-Up") or contains(text(),"Skins") or contains(text(),"Texture")]/text()').get()
        item["category"] = category.strip() if category else None

        # Price in Minecoins (e.g., "830 Minecraft Marketplace Minecoins")
        price_line = response.xpath('//*[contains(text(),"Minecoins")]/text()').get()
        if price_line:
            m = re.search(r'(\d+)\s+Minecraft\s+Marketplace\s+Minecoins', price_line)
            item["price_minecoins"] = int(m.group(1)) if m else None

        # Ratings (block shows "Total of X Ratings" and average)
        rating_count = response.xpath('//*[contains(text(),"Total of") and contains(text(),"Ratings")]/text()').re_first(r'Total of\s+([\d,]+)\s+Ratings')
        item["rating_count"] = int(rating_count.replace(',', '')) if rating_count else None

        rating_value = response.xpath('//*[contains(.,"/5")]/text()').re_first(r'(\d+(?:\.\d+)?)/5')
        item["rating_value"] = float(rating_value) if rating_value else None

        # Launched / Last Updated / Minimum Version
        launched = response.xpath('//*[contains(text(),"Launched:")]/following-sibling::text()[1]').get()
        last_updated = response.xpath('//*[contains(text(),"Last Updated:")]/following-sibling::text()[1]').get()
        min_version = response.xpath('//*[contains(text(),"Minimum Version:")]/following-sibling::text()[1]').get()
        item["launched"] = launched.strip() if launched else None
        item["last_updated"] = last_updated.strip() if last_updated else None
        item["min_version"] = min_version.strip() if min_version else None

        # Marketplace UID (appears in "Product Metadata")
        uid = response.xpath('//*[contains(text(),"UID")]/following::a/text() | //*[contains(text(),"UID")]/following::text()[1]').re_first(r'[0-9a-f-]{36}')
        item["uid"] = uid

        # Tags section (list of tags below description)
        tags = [t.strip() for t in response.css('a[href*="tags"]::text, li::text').getall() if t.strip()]
        # fallback: explicit tag container seen on product pages
        if not tags:
            tags = [t.strip() for t in response.xpath('//*[contains(.,"Product Tags")]/following::*//text()').getall() if t.strip()]
        item["tags"] = tags or None

        yield item
