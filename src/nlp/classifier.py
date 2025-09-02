import jieba
from typing import List, Dict
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.naive_bayes import MultinomialNB
import numpy as np
from loguru import logger


class TextClassifier:
    def __init__(self):
        self.categories = {
            '科技': ['人工智能', '机器学习', '深度学习', '算法', '编程', '软件', '硬件', 
                   '互联网', '5G', '云计算', '大数据', '区块链', '物联网', '芯片'],
            '财经': ['股票', '基金', '投资', '金融', '经济', '市场', '银行', '货币', 
                   '利率', '通胀', '资产', '债券', '期货', '外汇'],
            '教育': ['学校', '学生', '教师', '课程', '考试', '培训', '教学', '大学', 
                   '高考', '中考', '留学', '职业教育', '在线教育'],
            '健康': ['医疗', '健康', '疾病', '治疗', '医院', '医生', '药物', '疫苗', 
                   '养生', '保健', '营养', '运动', '心理健康'],
            '娱乐': ['电影', '音乐', '游戏', '明星', '综艺', '演出', '娱乐圈', '网红', 
                   '直播', '短视频', '影视', '演员', '歌手'],
            '体育': ['足球', '篮球', '乒乓球', '羽毛球', '网球', '游泳', '田径', 
                   '奥运会', '世界杯', '运动员', '比赛', '冠军', '体育赛事'],
            '政策': ['政府', '政策', '法律', '法规', '国家', '部门', '改革', '发展', 
                   '规划', '战略', '监管', '立法', '执法'],
            '社会': ['社会', '民生', '城市', '农村', '环境', '交通', '住房', '就业', 
                   '养老', '社保', '公益', '慈善', '社区'],
            '文化': ['文化', '艺术', '历史', '文学', '诗歌', '小说', '绘画', '书法', 
                   '博物馆', '文化遗产', '传统文化', '文化交流'],
            '国际': ['国际', '外交', '国外', '美国', '欧洲', '亚洲', '联合国', 
                   '贸易', '合作', '冲突', '全球', '世界']
        }
        
        self.vectorizer = None
        self.classifier = None
        self._prepare_training_data()
    
    def _prepare_training_data(self):
        pass
    
    def classify(self, text: str) -> str:
        try:
            words = jieba.lcut(text.lower())
            
            category_scores = {}
            for category, keywords in self.categories.items():
                score = 0
                for keyword in keywords:
                    if keyword in text:
                        score += text.count(keyword) * 2
                    for word in words:
                        if keyword in word or word in keyword:
                            score += 1
                category_scores[category] = score
            
            if max(category_scores.values()) == 0:
                return '综合'
            
            return max(category_scores, key=category_scores.get)
            
        except Exception as e:
            logger.error(f"Classification error: {e}")
            return '综合'
    
    def classify_batch(self, texts: List[str]) -> List[str]:
        return [self.classify(text) for text in texts]
    
    def get_category_keywords(self, category: str) -> List[str]:
        return self.categories.get(category, [])