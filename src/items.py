import scrapy
from datetime import datetime


class ArticleItem(scrapy.Item):
    url = scrapy.Field()
    title = scrapy.Field()
    content = scrapy.Field()
    author = scrapy.Field()
    publish_date = scrapy.Field()
    source = scrapy.Field()
    source_domain = scrapy.Field()
    
    raw_html = scrapy.Field()
    
    category = scrapy.Field()
    tags = scrapy.Field()
    level = scrapy.Field()
    sentiment = scrapy.Field()
    keywords = scrapy.Field()
    summary = scrapy.Field()
    
    crawl_time = scrapy.Field()
    update_time = scrapy.Field()
    
    metadata = scrapy.Field()