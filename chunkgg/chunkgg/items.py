# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy


import scrapy

class ProductItem(scrapy.Item):
    url = scrapy.Field()
    title = scrapy.Field()
    creator = scrapy.Field()
    category = scrapy.Field()
    price_minecoins = scrapy.Field()
    rating_value = scrapy.Field()
    rating_count = scrapy.Field()
    launched = scrapy.Field()
    last_updated = scrapy.Field()
    min_version = scrapy.Field()
    uid = scrapy.Field()
    tags = scrapy.Field()
