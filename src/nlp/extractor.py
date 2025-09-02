import jieba
import jieba.analyse
from typing import List, Dict, Tuple
from collections import Counter
import re
from loguru import logger


class KeywordExtractor:
    def __init__(self):
        self.stop_words = self._load_stop_words()
        # 移除jieba.analyse.set_stop_words()调用，直接在提取时过滤停用词
    
    def _load_stop_words(self) -> set:
        common_stop_words = {
            '的', '了', '和', '是', '就', '都', '而', '及', '与', '或',
            '在', '有', '为', '以', '于', '上', '中', '下', '等', '到',
            '这', '那', '些', '个', '之', '将', '来', '去', '但', '也',
            '又', '从', '被', '把', '让', '向', '往', '如', '此', '其'
        }
        return common_stop_words
    
    def extract_keywords(self, text: str, top_k: int = 10) -> List[str]:
        try:
            keywords_tfidf = self._extract_by_tfidf(text, top_k)
            
            keywords_textrank = self._extract_by_textrank(text, top_k)
            
            keywords_freq = self._extract_by_frequency(text, top_k)
            
            all_keywords = keywords_tfidf + keywords_textrank + keywords_freq
            keyword_counter = Counter(all_keywords)
            
            final_keywords = [word for word, _ in keyword_counter.most_common(top_k)]
            
            return final_keywords
            
        except Exception as e:
            logger.error(f"Keyword extraction error: {e}")
            return []
    
    def _extract_by_tfidf(self, text: str, top_k: int) -> List[str]:
        keywords = jieba.analyse.extract_tags(
            text,
            topK=top_k,
            withWeight=False,
            allowPOS=('n', 'nr', 'ns', 'nt', 'nw', 'nz', 'v', 'vn', 'a')
        )
        return [k for k in keywords if len(k) > 1 and k not in self.stop_words]
    
    def _extract_by_textrank(self, text: str, top_k: int) -> List[str]:
        keywords = jieba.analyse.textrank(
            text,
            topK=top_k,
            withWeight=False,
            allowPOS=('n', 'nr', 'ns', 'nt', 'nw', 'nz', 'v', 'vn')
        )
        return [k for k in keywords if len(k) > 1 and k not in self.stop_words]
    
    def _extract_by_frequency(self, text: str, top_k: int) -> List[str]:
        words = jieba.lcut(text)
        
        filtered_words = [
            word for word in words 
            if len(word) > 1 
            and word not in self.stop_words
            and not re.match(r'^[0-9\W]+$', word)
        ]
        
        word_freq = Counter(filtered_words)
        
        return [word for word, _ in word_freq.most_common(top_k)]
    
    def extract_phrases(self, text: str, top_k: int = 5) -> List[str]:
        try:
            words = jieba.lcut(text)
            
            bigrams = []
            for i in range(len(words) - 1):
                if (len(words[i]) > 1 and len(words[i+1]) > 1 and
                    words[i] not in self.stop_words and 
                    words[i+1] not in self.stop_words):
                    bigrams.append(f"{words[i]}{words[i+1]}")
            
            trigrams = []
            for i in range(len(words) - 2):
                if (len(words[i]) > 1 and len(words[i+1]) > 1 and len(words[i+2]) > 1 and
                    words[i] not in self.stop_words and 
                    words[i+2] not in self.stop_words):
                    trigrams.append(f"{words[i]}{words[i+1]}{words[i+2]}")
            
            all_phrases = bigrams + trigrams
            phrase_freq = Counter(all_phrases)
            
            return [phrase for phrase, freq in phrase_freq.most_common(top_k) if freq > 1]
            
        except Exception as e:
            logger.error(f"Phrase extraction error: {e}")
            return []
    
    def extract_named_entities(self, text: str) -> Dict[str, List[str]]:
        try:
            entities = {
                'person': [],
                'location': [],
                'organization': [],
                'product': []
            }
            
            words_with_pos = jieba.posseg.lcut(text)
            
            for word, pos in words_with_pos:
                if pos == 'nr':
                    entities['person'].append(word)
                elif pos == 'ns':
                    entities['location'].append(word)
                elif pos == 'nt':
                    entities['organization'].append(word)
                elif pos == 'nz':
                    entities['product'].append(word)
            
            for key in entities:
                entities[key] = list(set(entities[key]))
            
            return entities
            
        except Exception as e:
            logger.error(f"Named entity extraction error: {e}")
            return {'person': [], 'location': [], 'organization': [], 'product': []}