import re
import hashlib
from urllib.parse import urlparse
from typing import Optional
import html
from bs4 import BeautifulSoup


def clean_text(text: str) -> str:
    """清理文本内容"""
    if not text:
        return ""
    
    # 解码HTML实体
    text = html.unescape(text)
    
    # 移除多余的空白字符
    text = re.sub(r'\s+', ' ', text)
    
    # 移除特殊字符
    text = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', text)
    
    # 移除首尾空白
    text = text.strip()
    
    return text


def extract_domain(url: str) -> str:
    """从URL中提取域名"""
    try:
        parsed = urlparse(url)
        domain = parsed.netloc
        
        # 移除www前缀
        if domain.startswith('www.'):
            domain = domain[4:]
        
        return domain
    except:
        return ""


def calculate_hash(text: str) -> str:
    """计算文本的MD5哈希值"""
    if not text:
        return ""
    
    return hashlib.md5(text.encode('utf-8')).hexdigest()


def extract_numbers(text: str) -> list:
    """从文本中提取数字"""
    numbers = re.findall(r'\d+\.?\d*', text)
    return [float(n) if '.' in n else int(n) for n in numbers]


def is_valid_url(url: str) -> bool:
    """验证URL是否有效"""
    url_pattern = re.compile(
        r'^https?://'  # http:// or https://
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'  # domain...
        r'localhost|'  # localhost...
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ...or ip
        r'(?::\d+)?'  # optional port
        r'(?:/?|[/?]\S+)$', re.IGNORECASE)
    
    return url_pattern.match(url) is not None


def truncate_text(text: str, max_length: int = 100, suffix: str = "...") -> str:
    """截断文本到指定长度"""
    if not text or len(text) <= max_length:
        return text
    
    return text[:max_length - len(suffix)] + suffix


def remove_html_tags(html_text: str) -> str:
    """移除HTML标签"""
    if not html_text:
        return ""
    
    soup = BeautifulSoup(html_text, 'html.parser')
    return soup.get_text(separator=' ', strip=True)


def normalize_whitespace(text: str) -> str:
    """规范化空白字符"""
    if not text:
        return ""
    
    # 将所有空白字符替换为单个空格
    text = re.sub(r'\s+', ' ', text)
    
    # 移除标点符号前的空格
    text = re.sub(r'\s+([,.!?;:])', r'\1', text)
    
    return text.strip()


def extract_chinese(text: str) -> str:
    """提取文本中的中文字符"""
    pattern = re.compile(r'[\u4e00-\u9fff]+')
    chinese_chars = pattern.findall(text)
    return ''.join(chinese_chars)


def is_chinese_text(text: str, threshold: float = 0.3) -> bool:
    """判断文本是否为中文文本"""
    if not text:
        return False
    
    chinese_chars = len(extract_chinese(text))
    total_chars = len(text.replace(' ', ''))
    
    if total_chars == 0:
        return False
    
    return (chinese_chars / total_chars) >= threshold