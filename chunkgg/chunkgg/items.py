import scrapy

class MarketplaceItem(scrapy.Item):
    """Normalized product record emitted by the chunk.gg crawler."""

    # Identity
    product_url = scrapy.Field()
    slug = scrapy.Field()
    product_slug = scrapy.Field()
    uuid = scrapy.Field()
    category = scrapy.Field()

    # Creator
    creator = scrapy.Field()
    creator_slug = scrapy.Field()
    creator_url = scrapy.Field()

    # Listing content
    title = scrapy.Field()
    description = scrapy.Field()
    tags = scrapy.Field()
    badge_labels = scrapy.Field()
    badge_modifiers = scrapy.Field()
    skin_count = scrapy.Field()
    player_range = scrapy.Field()
    supports_singleplayer = scrapy.Field()
    supports_multiplayer = scrapy.Field()

    # Media
    gallery = scrapy.Field()

    # Pricing
    price_minecoins = scrapy.Field()
    price_usd = scrapy.Field()
    price_eur = scrapy.Field()
    is_free = scrapy.Field()

    # Ratings
    rating_value = scrapy.Field()
    rating_out_of = scrapy.Field()
    rating_count = scrapy.Field()
    rating_5_count = scrapy.Field()
    rating_5_percent = scrapy.Field()
    rating_4_count = scrapy.Field()
    rating_4_percent = scrapy.Field()
    rating_3_count = scrapy.Field()
    rating_3_percent = scrapy.Field()
    rating_2_count = scrapy.Field()
    rating_2_percent = scrapy.Field()
    rating_1_count = scrapy.Field()
    rating_1_percent = scrapy.Field()
    rating_breakdown = scrapy.Field()

    # Usage
    downloads = scrapy.Field()

    # Timeline
    min_version = scrapy.Field()
    launched = scrapy.Field()
    launched_iso = scrapy.Field()
    last_updated = scrapy.Field()
    last_updated_iso = scrapy.Field()
    changelog = scrapy.Field()

    # Trailer / video
    has_trailer = scrapy.Field()
    trailer_url = scrapy.Field()
    trailer_views = scrapy.Field()
    trailer_likes = scrapy.Field()
