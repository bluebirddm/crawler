import pytest
from datetime import datetime
from src.utils.helpers import (
    clean_text,
    extract_domain,
    calculate_hash,
    extract_numbers,
    is_valid_url,
    truncate_text,
    remove_html_tags,
    normalize_whitespace,
    extract_chinese,
    is_chinese_text
)
from src.api.utils.datetime import parse_datetime_param


class TestHelpers:
    def test_clean_text(self):
        dirty_text = "  Hello\n\n  World\t\t  "
        clean = clean_text(dirty_text)
        assert clean == "Hello World"
        
        html_text = "Test &amp; &lt;html&gt;"
        clean = clean_text(html_text)
        assert clean == "Test & <html>"
    
    def test_extract_domain(self):
        assert extract_domain("https://www.example.com/path") == "example.com"
        assert extract_domain("http://subdomain.example.com") == "subdomain.example.com"
        assert extract_domain("https://example.com:8080") == "example.com:8080"
        assert extract_domain("invalid-url") == ""
    
    def test_calculate_hash(self):
        text1 = "Hello World"
        text2 = "Hello World"
        text3 = "Different Text"
        
        hash1 = calculate_hash(text1)
        hash2 = calculate_hash(text2)
        hash3 = calculate_hash(text3)
        
        assert hash1 == hash2
        assert hash1 != hash3
        assert len(hash1) == 32  # MD5 hash length
    
    def test_extract_numbers(self):
        text = "I have 10 apples and 3.14 oranges"
        numbers = extract_numbers(text)
        assert numbers == [10, 3.14]
        
        text = "No numbers here"
        numbers = extract_numbers(text)
        assert numbers == []
    
    def test_is_valid_url(self):
        assert is_valid_url("https://www.example.com")
        assert is_valid_url("http://localhost:8080")
        assert is_valid_url("https://192.168.1.1")
        assert not is_valid_url("not-a-url")
        assert not is_valid_url("ftp://example.com")
    
    def test_truncate_text(self):
        text = "This is a very long text that needs to be truncated"
        truncated = truncate_text(text, max_length=20)
        assert len(truncated) <= 20
        assert truncated.endswith("...")
        
        short_text = "Short"
        truncated = truncate_text(short_text, max_length=20)
        assert truncated == short_text
    
    def test_remove_html_tags(self):
        html = "<p>Hello <b>World</b></p>"
        text = remove_html_tags(html)
        assert text == "Hello World"
        
        html = "<div><span>Test</span> <a href='#'>Link</a></div>"
        text = remove_html_tags(html)
        assert text == "Test Link"
    
    def test_normalize_whitespace(self):
        text = "Hello    World  !  Test  ."
        normalized = normalize_whitespace(text)
        assert normalized == "Hello World! Test."
        
        text = "  Multiple   \n\n  lines  \t\t  "
        normalized = normalize_whitespace(text)
        assert normalized == "Multiple lines"
    
    def test_extract_chinese(self):
        text = "Hello 世界 World 你好"
        chinese = extract_chinese(text)
        assert chinese == "世界你好"
        
        text = "No Chinese here"
        chinese = extract_chinese(text)
        assert chinese == ""
    
    def test_is_chinese_text(self):
        assert is_chinese_text("这是中文文本")
        assert is_chinese_text("这是中文 with some English", threshold=0.3)
        assert not is_chinese_text("This is English text")
        assert not is_chinese_text("123456789")


class TestApiDatetimeUtils:
    def test_parse_datetime_param_supports_milliseconds(self):
        dt = parse_datetime_param("1757520000000", "start_date")
        assert dt == datetime.fromtimestamp(1757520000)

    def test_parse_datetime_param_supports_iso(self):
        dt = parse_datetime_param("2025-09-11T12:30:00", "start_date")
        assert dt == datetime(2025, 9, 11, 12, 30, 0)

    def test_parse_datetime_param_rejects_invalid(self):
        with pytest.raises(ValueError):
            parse_datetime_param("not-a-date", "start_date")
