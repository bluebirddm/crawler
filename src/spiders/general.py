import scrapy
from scrapy.http import Response
from datetime import datetime
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup
from loguru import logger

from ..items import ArticleItem


class GeneralSpider(scrapy.Spider):
    name = 'general'
    
    def __init__(self, start_url=None, *args, **kwargs):
        super(GeneralSpider, self).__init__(*args, **kwargs)
        if start_url:
            self.start_urls = [start_url]
        else:
            self.start_urls = []
    
    def start_requests(self):
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
            
            metadata = {
                'status_code': response.status,
                'headers': dict(response.headers),
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