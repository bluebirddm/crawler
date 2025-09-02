import jieba
import jieba.analyse
from typing import Dict, List, Optional
from loguru import logger
from .classifier import TextClassifier
from .extractor import KeywordExtractor


class NLPProcessor:
    def __init__(self):
        self.classifier = TextClassifier()
        self.extractor = KeywordExtractor()
        self._init_jieba()
    
    def _init_jieba(self):
        jieba.setLogLevel(20)
        custom_words = [
            '人工智能', '机器学习', '深度学习', '自然语言处理',
            '大数据', '云计算', '区块链', '物联网'
        ]
        for word in custom_words:
            jieba.add_word(word)
    
    def process(self, title: str, content: str) -> Dict:
        try:
            full_text = f"{title} {content}"
            
            category = self.classifier.classify(full_text)
            
            level = self._calculate_level(full_text, category)
            
            tags = self._extract_tags(full_text)
            
            keywords = self.extractor.extract_keywords(full_text)
            
            sentiment = self._analyze_sentiment(full_text)
            
            summary = self._generate_summary(content)
            
            return {
                'category': category,
                'level': level,
                'tags': tags,
                'keywords': keywords,
                'sentiment': sentiment,
                'summary': summary
            }
            
        except Exception as e:
            logger.error(f"NLP processing error: {e}")
            return {
                'category': 'uncategorized',
                'level': 0,
                'tags': [],
                'keywords': [],
                'sentiment': 0.0,
                'summary': content[:200] if len(content) > 200 else content
            }
    
    def _calculate_level(self, text: str, category: str) -> int:
        level = 1
        
        quality_indicators = [
            '原创', '深度', '分析', '研究', '报告', '白皮书',
            '独家', '专访', '权威', '官方'
        ]
        
        for indicator in quality_indicators:
            if indicator in text:
                level += 1
        
        if len(text) > 2000:
            level += 1
        if len(text) > 5000:
            level += 1
        
        important_categories = ['科技', '财经', '政策', '研究']
        if category in important_categories:
            level += 1
        
        return min(level, 5)
    
    def _extract_tags(self, text: str) -> List[str]:
        tags = jieba.analyse.extract_tags(
            text,
            topK=10,
            withWeight=False,
            allowPOS=('n', 'nr', 'ns', 'nt', 'nw', 'nz', 'v', 'vn')
        )
        
        return [tag for tag in tags if len(tag) > 1]
    
    def _analyze_sentiment(self, text: str) -> float:
        positive_words = [
            '好', '优秀', '成功', '增长', '提升', '创新', '突破',
            '领先', '优势', '积极', '进步', '发展'
        ]
        negative_words = [
            '差', '失败', '下降', '问题', '困难', '危机', '风险',
            '落后', '劣势', '消极', '退步', '衰退'
        ]
        
        words = jieba.lcut(text)
        
        positive_count = sum(1 for word in words if word in positive_words)
        negative_count = sum(1 for word in words if word in negative_words)
        
        total = positive_count + negative_count
        if total == 0:
            return 0.0
        
        sentiment = (positive_count - negative_count) / total
        return round(sentiment, 2)
    
    def _generate_summary(self, content: str, max_length: int = 200) -> str:
        sentences = self._split_sentences(content)
        
        if not sentences:
            return content[:max_length]
        
        scores = {}
        for sentence in sentences:
            words = jieba.lcut(sentence)
            word_count = len(words)
            if word_count > 5:
                keywords = jieba.analyse.extract_tags(sentence, topK=5)
                score = len(keywords) / word_count
                scores[sentence] = score
        
        sorted_sentences = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        
        summary = []
        current_length = 0
        for sentence, _ in sorted_sentences[:3]:
            if current_length + len(sentence) <= max_length:
                summary.append(sentence)
                current_length += len(sentence)
        
        return ''.join(summary) if summary else sentences[0][:max_length]
    
    def _split_sentences(self, text: str) -> List[str]:
        import re
        sentences = re.split(r'[。！？\n]+', text)
        return [s.strip() for s in sentences if s.strip() and len(s.strip()) > 10]