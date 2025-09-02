import pytest
from src.nlp.processor import NLPProcessor
from src.nlp.classifier import TextClassifier
from src.nlp.extractor import KeywordExtractor


class TestNLPProcessor:
    def setup_method(self):
        self.processor = NLPProcessor()
    
    def test_process_article(self):
        title = "人工智能在医疗领域的应用"
        content = """
        近年来，人工智能技术在医疗健康领域取得了突破性进展。
        通过深度学习算法，AI可以帮助医生进行疾病诊断，提高诊断准确率。
        机器学习模型在药物研发、影像分析等方面也展现出巨大潜力。
        """
        
        result = self.processor.process(title, content)
        
        assert 'category' in result
        assert 'tags' in result
        assert 'keywords' in result
        assert 'level' in result
        assert 'sentiment' in result
        assert 'summary' in result
        
        assert isinstance(result['tags'], list)
        assert isinstance(result['keywords'], list)
        assert isinstance(result['level'], int)
        assert 0 <= result['level'] <= 5
    
    def test_empty_content(self):
        result = self.processor.process("", "")
        
        assert result['category'] == 'uncategorized'
        assert result['level'] == 0
        assert result['tags'] == []


class TestTextClassifier:
    def setup_method(self):
        self.classifier = TextClassifier()
    
    def test_classify_tech_article(self):
        text = "人工智能和机器学习正在改变软件开发的方式，深度学习算法带来新突破"
        category = self.classifier.classify(text)
        assert category == '科技'
    
    def test_classify_finance_article(self):
        text = "股票市场今日大涨，基金投资收益创新高，银行利率调整影响经济"
        category = self.classifier.classify(text)
        assert category == '财经'
    
    def test_classify_mixed_content(self):
        text = "今天天气很好，我去公园散步"
        category = self.classifier.classify(text)
        assert category in ['综合', '社会']


class TestKeywordExtractor:
    def setup_method(self):
        self.extractor = KeywordExtractor()
    
    def test_extract_keywords(self):
        text = """
        人工智能技术正在快速发展，深度学习和机器学习成为研究热点。
        自然语言处理技术在文本分析领域应用广泛。
        """
        
        keywords = self.extractor.extract_keywords(text, top_k=5)
        
        assert isinstance(keywords, list)
        assert len(keywords) <= 5
        assert all(isinstance(k, str) for k in keywords)
    
    def test_extract_phrases(self):
        text = "人工智能技术在自然语言处理领域的应用研究"
        
        phrases = self.extractor.extract_phrases(text, top_k=3)
        
        assert isinstance(phrases, list)
        assert len(phrases) <= 3
    
    def test_extract_named_entities(self):
        text = "马云创立了阿里巴巴，总部位于杭州"
        
        entities = self.extractor.extract_named_entities(text)
        
        assert isinstance(entities, dict)
        assert 'person' in entities
        assert 'location' in entities
        assert 'organization' in entities