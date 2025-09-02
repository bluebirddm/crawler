from scrapy import signals
from scrapy.exceptions import NotConfigured
import random
import time
from loguru import logger


class SpiderMiddleware:
    @classmethod
    def from_crawler(cls, crawler):
        s = cls()
        crawler.signals.connect(s.spider_opened, signal=signals.spider_opened)
        return s

    def process_spider_input(self, response, spider):
        return None

    def process_spider_output(self, response, result, spider):
        for i in result:
            yield i

    async def process_spider_output_async(self, response, result, spider):
        # 异步处理spider输出，支持异步迭代器
        async for item_or_request in result:
            yield item_or_request

    def process_spider_exception(self, response, exception, spider):
        logger.error(f"Spider exception: {exception}")

    def process_start_requests(self, start_requests, spider):
        # 使用传统的process_start_requests方法
        for r in start_requests:
            yield r

    def spider_opened(self, spider):
        logger.info(f'Spider opened: {spider.name}')


class DownloaderMiddleware:
    @classmethod
    def from_crawler(cls, crawler):
        s = cls()
        crawler.signals.connect(s.spider_opened, signal=signals.spider_opened)
        return s

    def process_request(self, request, spider):
        request.headers['User-Agent'] = self._get_random_user_agent()
        return None

    def process_response(self, request, response, spider):
        if response.status in [200, 201]:
            logger.debug(f"Successfully fetched: {request.url}")
        return response

    def process_exception(self, request, exception, spider):
        logger.error(f"Download exception for {request.url}: {exception}")

    def spider_opened(self, spider):
        logger.info(f'Spider opened: {spider.name}')
    
    def _get_random_user_agent(self):
        user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36'
        ]
        return random.choice(user_agents)


class ProxyMiddleware:
    def __init__(self):
        self.proxies = []
    
    def process_request(self, request, spider):
        if self.proxies:
            proxy = random.choice(self.proxies)
            request.meta['proxy'] = proxy
            logger.debug(f"Using proxy: {proxy}")


class RetryMiddleware:
    def __init__(self):
        self.max_retry_times = 3
        self.retry_delay = 2
    
    def process_response(self, request, response, spider):
        if response.status in [500, 502, 503, 504, 429]:
            retry_times = request.meta.get('retry_times', 0)
            if retry_times < self.max_retry_times:
                time.sleep(self.retry_delay * (retry_times + 1))
                request.meta['retry_times'] = retry_times + 1
                logger.warning(f"Retrying {request.url} (attempt {retry_times + 1})")
                return request
        return response