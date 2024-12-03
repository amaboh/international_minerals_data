from scrapy import Item, Field

class MineralsFileItem(Item):
    file_urls = Field()
    files = Field()
    country = Field()
    year = Field()