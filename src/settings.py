import os
from dotenv import load_dotenv

load_dotenv()

BOT_NAME = 'crawler'

SPIDER_MODULES = ['src.spiders']
NEWSPIDER_MODULE = 'src.spiders'

USER_AGENT = os.getenv('USER_AGENT', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')

ROBOTSTXT_OBEY = False

CONCURRENT_REQUESTS = int(os.getenv('CONCURRENT_REQUESTS', 16))
DOWNLOAD_DELAY = int(os.getenv('DOWNLOAD_DELAY', 1))
CONCURRENT_REQUESTS_PER_DOMAIN = 8
CONCURRENT_REQUESTS_PER_IP = 8

COOKIES_ENABLED = True

TELNETCONSOLE_ENABLED = False

DEFAULT_REQUEST_HEADERS = {
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
}

SPIDER_MIDDLEWARES = {
    'src.middlewares.SpiderMiddleware': 543,
}

DOWNLOADER_MIDDLEWARES = {
    'src.middlewares.DownloaderMiddleware': 543,
    'src.middlewares.ProxyMiddleware': 544,
    'src.middlewares.RetryMiddleware': 545,
}

ITEM_PIPELINES = {
    'src.pipelines.ValidationPipeline': 100,
    'src.pipelines.DuplicatesPipeline': 200,
    'src.pipelines.NLPPipeline': 300,
    'src.pipelines.PostgreSQLPipeline': 400,
}

AUTOTHROTTLE_ENABLED = True
AUTOTHROTTLE_START_DELAY = 1
AUTOTHROTTLE_MAX_DELAY = 10
AUTOTHROTTLE_TARGET_CONCURRENCY = 4.0
AUTOTHROTTLE_DEBUG = False

HTTPCACHE_ENABLED = True
HTTPCACHE_EXPIRATION_SECS = 3600
HTTPCACHE_DIR = 'httpcache'
HTTPCACHE_IGNORE_HTTP_CODES = [503, 504, 400, 403, 404]
HTTPCACHE_STORAGE = 'scrapy.extensions.httpcache.FilesystemCacheStorage'

RETRY_TIMES = int(os.getenv('RETRY_TIMES', 3))
RETRY_HTTP_CODES = [500, 502, 503, 504, 408, 429]

LOG_LEVEL = 'INFO'
LOG_FILE = 'logs/scrapy.log'

FEED_EXPORT_ENCODING = 'utf-8'

REQUEST_FINGERPRINTER_IMPLEMENTATION = "2.7"
TWISTED_REACTOR = "twisted.internet.asyncioreactor.AsyncioSelectorReactor"
FEED_EXPORT_ENCODING = "utf-8"