import scrapy
from scrapy.http import Response
from datetime import datetime
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup
from loguru import logger

from ..items import ArticleItem


class GeneralSpider(scrapy.Spider):
    name = 'general'

    def __init__(self, start_url=None, start_urls=None, *args, **kwargs):
        """支持 -a start_url=... 与 -a start_urls=... 两种传参形式。

        start_urls 可为：
        - 逗号/空白/分号分隔的字符串
        - JSON 字符串（单个字符串或字符串数组）
        """
        super(GeneralSpider, self).__init__(*args, **kwargs)

        urls = []
        if start_url:
            urls.append(start_url)
        if start_urls:
            urls.extend(self._parse_urls_arg(start_urls))

        # 去重并保序
        seen = set()
        deduped = []
        for u in urls:
            if u and u not in seen:
                seen.add(u)
                deduped.append(u)
        self.start_urls = deduped

        if not self.start_urls:
            logger.warning(
                "未提供有效的起始 URL。请使用 -a start_url=... 或 -a start_urls=..."
            )

    def _parse_urls_arg(self, value):
        # 允许 list/tuple 直接传入
        if isinstance(value, (list, tuple)):
            return [str(v) for v in value if v]

        # 优先尝试 JSON 解析
        try:
            import json

            data = json.loads(value)
            if isinstance(data, str):
                return [data]
            if isinstance(data, (list, tuple)):
                return [str(v) for v in data if v]
        except Exception:
            pass

        # 回退为分隔符拆分
        import re

        return [u.strip() for u in re.split(r"[\s,;]+", str(value)) if u.strip()]
    
    async def start(self):
        """新的异步启动方法，兼容Scrapy 2.13+"""
        for url in self.start_urls:
            yield scrapy.Request(
                url,
                callback=self.parse,
                errback=self.error_callback,
                meta={'original_url': url}
            )
    
    def start_requests(self):
        """保留向后兼容性，兼容Scrapy < 2.13"""
        for url in self.start_urls:
            yield scrapy.Request(
                url,
                callback=self.parse,
                errback=self.error_callback,
                meta={'original_url': url}
            )
    
    def parse(self, response: Response):
        try:
            item = ArticleItem()
            
            item['url'] = response.url
            item['raw_html'] = response.text
            
            soup = BeautifulSoup(response.text, 'lxml')
            
            item['title'] = self._extract_title(soup, response)
            
            item['content'] = self._extract_content(soup)
            
            item['author'] = self._extract_author(soup)
            
            item['publish_date'] = self._extract_date(soup)
            
            item['source'] = self._extract_source(soup, response)
            
            # 转换headers为可序列化的格式（字节键值转为字符串）
            headers_dict = {}
            for key, value in response.headers.items():
                # 将字节类型的键和值转换为字符串
                str_key = key.decode('utf-8') if isinstance(key, bytes) else key
                if isinstance(value, list):
                    str_value = [v.decode('utf-8') if isinstance(v, bytes) else v for v in value]
                else:
                    str_value = value.decode('utf-8') if isinstance(value, bytes) else value
                headers_dict[str_key] = str_value
            
            metadata = {
                'status_code': response.status,
                'headers': headers_dict,
                'crawl_depth': response.meta.get('depth', 0)
            }
            item['metadata'] = metadata
            
            yield item
            
            if response.meta.get('depth', 0) < 2:
                for link in self._extract_links(soup, response):
                    yield scrapy.Request(
                        link,
                        callback=self.parse,
                        meta={'depth': response.meta.get('depth', 0) + 1}
                    )
            
        except Exception as e:
            logger.error(f"Failed to parse {response.url}: {e}")
    
    def _extract_title(self, soup: BeautifulSoup, response: Response) -> str:
        title = None
        
        if soup.find('h1'):
            title = soup.find('h1').get_text(strip=True)
        elif soup.find('title'):
            title = soup.find('title').get_text(strip=True)
        elif soup.find('h2'):
            title = soup.find('h2').get_text(strip=True)
        
        meta_title = soup.find('meta', {'property': 'og:title'})
        if meta_title:
            title = meta_title.get('content', title)
        
        return title or "Untitled"
    
    def _extract_content(self, soup: BeautifulSoup) -> str:
        for script in soup(["script", "style"]):
            script.decompose()
        
        content_tags = ['article', 'main', 'div[class*="content"]', 
                       'div[class*="article"]', 'div[class*="post"]']
        
        for tag in content_tags:
            content_elem = soup.select_one(tag)
            if content_elem:
                return content_elem.get_text(separator='\n', strip=True)
        
        paragraphs = soup.find_all('p')
        if paragraphs:
            content = '\n'.join([p.get_text(strip=True) for p in paragraphs])
            if len(content) > 100:
                return content
        
        return soup.get_text(separator='\n', strip=True)
    
    def _extract_author(self, soup: BeautifulSoup) -> str:
        author = None
        
        author_tags = [
            {'name': 'meta', 'attrs': {'name': 'author'}},
            {'name': 'meta', 'attrs': {'property': 'article:author'}},
            {'name': 'span', 'attrs': {'class': 'author'}},
            {'name': 'div', 'attrs': {'class': 'author'}},
            {'name': 'p', 'attrs': {'class': 'author'}}
        ]
        
        for tag in author_tags:
            elem = soup.find(**tag)
            if elem:
                if elem.name == 'meta':
                    author = elem.get('content')
                else:
                    author = elem.get_text(strip=True)
                if author:
                    break
        
        return author
    
    def _extract_date(self, soup: BeautifulSoup) -> datetime:
        date_str = None
        
        date_tags = [
            {'name': 'meta', 'attrs': {'property': 'article:published_time'}},
            {'name': 'meta', 'attrs': {'name': 'publish_date'}},
            {'name': 'time'},
            {'name': 'span', 'attrs': {'class': 'date'}},
            {'name': 'div', 'attrs': {'class': 'date'}}
        ]
        
        for tag in date_tags:
            elem = soup.find(**tag)
            if elem:
                if elem.name == 'meta':
                    date_str = elem.get('content')
                elif elem.name == 'time':
                    date_str = elem.get('datetime') or elem.get_text(strip=True)
                else:
                    date_str = elem.get_text(strip=True)
                if date_str:
                    break
        
        if date_str:
            try:
                from dateutil import parser
                return parser.parse(date_str)
            except:
                pass
        
        return None
    
    def _extract_source(self, soup: BeautifulSoup, response: Response) -> str:
        source = None
        
        og_site = soup.find('meta', {'property': 'og:site_name'})
        if og_site:
            source = og_site.get('content')
        
        if not source:
            source = urlparse(response.url).netloc
        
        return source
    
    def _extract_links(self, soup: BeautifulSoup, response: Response) -> list:
        links = []
        domain = urlparse(response.url).netloc
        
        for link in soup.find_all('a', href=True):
            url = urljoin(response.url, link['href'])
            parsed_url = urlparse(url)
            
            if parsed_url.netloc == domain:
                if not any(ext in url for ext in ['.pdf', '.doc', '.xls', '.zip']):
                    links.append(url)
        
        return links[:10]
    
    def error_callback(self, failure):
        logger.error(f"Request failed: {failure.request.url}")
        logger.error(f"Error: {failure.value}")
