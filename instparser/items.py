# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy


class InstparserItem(scrapy.Item):
    # define the fields for your item here like:
    # name = scrapy.Field()
    user = scrapy.Field()
    subject = scrapy.Field()
    subject_id = scrapy.Field()
    photo = scrapy.Field()
    collection = scrapy.Field()
