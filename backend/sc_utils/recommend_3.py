
# -*- coding: utf-8 -*-
"""
多模态双塔推荐系统
结合：
1. 基于内容的推荐（TF-IDF）
2. 协同过滤（基于邻域/矩阵分解）
3. 多模态双塔模型（DSSM）- 文本 + 图片特征
"""
import sqlite3
import math
import os
import json
from collections import defaultdict
import numpy as np

# -----------------------------
# 配置
# -----------------------------
SQLITE_DB_PATH = r"D:\Project\SecondCreationBackend-V1\scforum.db"
IMAGE_ROOT_DIR = r"D:\Project\SecondCreationBackend-V1\backend\static\upload_IMG"

# HuggingFace Token - 用于认证请求，提高下载速度和速率限制
# 可以通过环境变量 HF_TOKEN 设置，或在此处直接设置
HF_TOKEN = os.environ.get("HF_TOKEN", "")

# 停用词列表
STOPWORDS = set([
    '的', '了', '和', '是', '就', '都', '而', '及', '与', '着', '或', '一个', '没有', '我们', '你们',
    '他们', '它们', '这个', '那个', '这些', '那些', '什么', '怎么', '为什么', '因为', '所以',
    '但是', '然而', '虽然', '如果', '可以', '可能', '应该', '必须', '需要', '已经', '正在',
    '曾经', '将会', '能够', '不能', '不要', '不会', '觉得', '认为', '知道', '说', '想', '看',
    '听', '做', '有', '在', '到', '去', '来', '上', '下', '左', '右', '前', '后', '中', '外'
])

# -----------------------------
# SQLite 数据加载
# -----------------------------
def load_articles():
    """加载文章数据（包含图片URL）"""
    conn = sqlite3.connect(SQLITE_DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT id, title, subtitle, content, image_urls FROM articles WHERE status='published'")
    rows = cursor.fetchall()
    conn.close()
    articles = []
    for r in rows:
        image_urls = json.loads(r[4]) if r[4] else []
        articles.append({
            "article_id": int(r[0]),
            "title": r[1],
            "subtitle": r[2] or "",
            "content": r[3],
            "image_urls": image_urls
        })
    return articles


def load_user_behaviors():
    """加载用户行为数据"""
    conn = sqlite3.connect(SQLITE_DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT user_id, article_id FROM user_likes")
    rows = cursor.fetchall()
    conn.close()
    behaviors = {}
    for r in rows:
        behaviors.setdefault(r[0], []).append(r[1])
    return behaviors


def get_full_image_path(db_suffix):
    """获取图片完整路径"""
    if not db_suffix:
        return None
    suffix = db_suffix.lstrip("/")
    full_path = os.path.join(IMAGE_ROOT_DIR, suffix)
    return full_path if os.path.exists(full_path) else None


# =============================
# 基于内容的推荐类
# =============================
class ContentBasedRecommender:
    """基于内容的推荐器（使用TF-IDF向量空间模型）"""

    def __init__(self):
        self.tfidf = None
        self.article_vectors = None
        self.article_ids = None
        self.article_info = {}

    @staticmethod
    def tokenize(text):
        """文本预处理：简单字符分割，去除停用词"""
        words = list(text)
        return [word for word in words if word not in STOPWORDS and len(word) > 0]

    def fit(self, articles):
        """训练TF-IDF模型"""
        self.article_ids = [article['article_id'] for article in articles]
        self.article_info = {article['article_id']: article for article in articles}
        article_texts = [f"{article['title']} {article['subtitle']} {article['content']}" for article in articles]

        # 构建词汇表和IDF
        doc_count = len(article_texts)
        doc_word_count = defaultdict(int)

        for doc in article_texts:
            words = set(self.tokenize(doc))
            for word in words:
                doc_word_count[word] += 1

        vocabulary = {word: idx for idx, word in enumerate(sorted(doc_word_count.keys()))}
        idf = {}
        for word, doc_freq in doc_word_count.items():
            idf[word] = math.log(doc_count / (1 + doc_freq))

        # 转换文档为TF-IDF向量
        vectors = []
        for doc in article_texts:
            words = self.tokenize(doc)
            word_freq = defaultdict(int)
            max_freq = 1
            for word in words:
                word_freq[word] += 1
                if word_freq[word] > max_freq:
                    max_freq = word_freq[word]

            vector = [0.0] * len(vocabulary)
            for word, freq in word_freq.items():
                if word in vocabulary:
                    idx = vocabulary[word]
                    tf = freq / max_freq
                    vector[idx] = tf * idf.get(word, 0)
            vectors.append(vector)

        self.tfidf = {'vocabulary': vocabulary, 'idf': idf}
        self.article_vectors = np.array(vectors)

    @staticmethod
    def cosine_similarity(vec1, vec2):
        """计算余弦相似度"""
        dot_product = np.dot(vec1, vec2)
        norm1 = np.linalg.norm(vec1)
        norm2 = np.linalg.norm(vec2)
        if norm1 == 0 or norm2 == 0:
            return 0.0
        return dot_product / (norm1 * norm2)

    def transform_query(self, query):
        """将查询转换为TF-IDF向量"""
        if not self.tfidf:
            raise ValueError("模型尚未训练，请先调用fit()方法")

        words = self.tokenize(query)
        word_freq = defaultdict(int)
        max_freq = 1
        for word in words:
            word_freq[word] += 1
            if word_freq[word] > max_freq:
                max_freq = word_freq[word]

        vector = [0.0] * len(self.tfidf['vocabulary'])
        for word, freq in word_freq.items():
            if word in self.tfidf['vocabulary']:
                idx = self.tfidf['vocabulary'][word]
                tf = freq / max_freq
                vector[idx] = tf * self.tfidf['idf'].get(word, 0)

        return np.array(vector)

    def recall(self, query=None, top_k=20):
        """基于内容的召回"""
        if self.article_vectors is None:
            articles = load_articles()
            self.fit(articles)

        if query:
            query_vector = self.transform_query(query)
            scores = []
            for i, aid in enumerate(self.article_ids):
                score = self.cosine_similarity(query_vector, self.article_vectors[i])
                scores.append((aid, score))
            scores.sort(key=lambda x: x[1], reverse=True)
            top_scores = scores[:top_k]
            return {aid: score for aid, score in top_scores}

        return {}

    def learn_user_preference(self, user_id, behaviors):
        """学习用户偏好向量"""
        user_articles = behaviors.get(user_id, [])
        if not user_articles or self.article_vectors is None:
            return np.zeros(self.article_vectors.shape[1] if self.article_vectors is not None else 0)

        liked_indices = [i for i, aid in enumerate(self.article_ids) if aid in user_articles]
        if not liked_indices:
            return np.zeros(self.article_vectors.shape[1])

        liked_vectors = self.article_vectors[liked_indices]
        return np.mean(liked_vectors, axis=0)

    def recommend_by_preference(self, user_id, behaviors, top_k=10):
        """基于用户偏好的推荐"""
        if self.article_vectors is None:
            articles = load_articles()
            self.fit(articles)

        user_preference = self.learn_user_preference(user_id, behaviors)
        user_articles = set(behaviors.get(user_id, []))

        scores = []
        for i, aid in enumerate(self.article_ids):
            if aid in user_articles:
                continue
            score = self.cosine_similarity(user_preference, self.article_vectors[i])
            scores.append((aid, score))

        scores.sort(key=lambda x: x[1], reverse=True)
        return scores[:top_k]


# =============================
# 协同过滤推荐类
# =============================
class CollaborativeFilteringRecommender:
    """协同过滤推荐器"""

    def __init__(self, behaviors=None):
        self.behaviors = behaviors if behaviors else load_user_behaviors()
        self.user_similarity_matrix = {}
        self.item_similarity_matrix = {}

    @staticmethod
    def pearson_correlation(list1, list2):
        """计算皮尔逊相关系数"""
        if len(list1) != len(list2):
            return 0.0

        n = len(list1)
        sum1 = sum(list1)
        sum2 = sum(list2)
        sum1_sq = sum(x * x for x in list1)
        sum2_sq = sum(x * x for x in list2)
        p_sum = sum(x * y for x, y in zip(list1, list2))

        num = p_sum - (sum1 * sum2 / n)
        den = math.sqrt((sum1_sq - sum1 ** 2 / n) * (sum2_sq - sum2 ** 2 / n))

        return num / den if den != 0 else 0.0

    def build_user_similarity_matrix(self):
        """构建用户相似度矩阵"""
        users = list(self.behaviors.keys())
        self.user_similarity_matrix = {}

        for i, u1 in enumerate(users):
            self.user_similarity_matrix[u1] = {}
            for j, u2 in enumerate(users):
                if i == j:
                    self.user_similarity_matrix[u1][u2] = 1.0
                elif j > i:
                    u1_items = set(self.behaviors[u1])
                    u2_items = set(self.behaviors[u2])
                    common_items = u1_items & u2_items

                    if common_items:
                        u1_ratings = [1 if item in u1_items else 0 for item in common_items]
                        u2_ratings = [1 if item in u2_items else 0 for item in common_items]
                        sim = self.pearson_correlation(u1_ratings, u2_ratings)
                    else:
                        sim = 0.0

                    self.user_similarity_matrix[u1][u2] = sim
                    self.user_similarity_matrix[u2][u1] = sim

    def build_item_similarity_matrix(self):
        """构建物品相似度矩阵"""
        item_users = defaultdict(set)
        for user, items in self.behaviors.items():
            for item in items:
                item_users[item].add(user)

        items = list(item_users.keys())
        self.item_similarity_matrix = {}

        for i, item1 in enumerate(items):
            self.item_similarity_matrix[item1] = {}
            for j, item2 in enumerate(items):
                if i == j:
                    self.item_similarity_matrix[item1][item2] = 1.0
                elif j > i:
                    users1 = item_users[item1]
                    users2 = item_users[item2]
                    common_users = users1 & users2

                    if common_users:
                        item1_ratings = [1 if user in users1 else 0 for user in common_users]
                        item2_ratings = [1 if user in users2 else 0 for user in common_users]
                        sim = self.pearson_correlation(item1_ratings, item2_ratings)
                    else:
                        sim = 0.0

                    self.item_similarity_matrix[item1][item2] = sim
                    self.item_similarity_matrix[item2][item1] = sim

    def user_based_cf(self, user_id, top_k=20, k_neighbors=5):
        """基于用户的协同过滤"""
        if user_id not in self.behaviors:
            return {}

        if not self.user_similarity_matrix:
            self.build_user_similarity_matrix()

        user_articles = set(self.behaviors[user_id])
        candidate_scores = defaultdict(float)

        if user_id in self.user_similarity_matrix:
            similar_users = sorted(
                self.user_similarity_matrix[user_id].items(),
                key=lambda x: x[1],
                reverse=True
            )[1:k_neighbors + 1]

            for neighbor_id, similarity in similar_users:
                if similarity <= 0:
                    continue
                for article in self.behaviors.get(neighbor_id, []):
                    if article not in user_articles:
                        candidate_scores[article] += similarity

        top_articles = sorted(candidate_scores.items(), key=lambda x: x[1], reverse=True)[:top_k]
        return {a: s for a, s in top_articles}

    def item_based_cf(self, user_id, top_k=20, k_items=5):
        """基于物品的协同过滤"""
        if user_id not in self.behaviors:
            return {}

        if not self.item_similarity_matrix:
            self.build_item_similarity_matrix()

        user_articles = set(self.behaviors[user_id])
        candidate_scores = defaultdict(float)

        for liked_item in user_articles:
            if liked_item in self.item_similarity_matrix:
                similar_items = sorted(
                    self.item_similarity_matrix[liked_item].items(),
                    key=lambda x: x[1],
                    reverse=True
                )[1:k_items + 1]

                for similar_item, similarity in similar_items:
                    if similarity <= 0:
                        continue
                    if similar_item not in user_articles:
                        candidate_scores[similar_item] += similarity

        top_articles = sorted(candidate_scores.items(), key=lambda x: x[1], reverse=True)[:top_k]
        return {a: s for a, s in top_articles}


# =============================
# 矩阵分解推荐类
# =============================
class MatrixFactorizationRecommender:
    """基于矩阵分解的协同过滤"""

    def __init__(self, behaviors=None, latent_factors=20, learning_rate=0.01, regularization=0.02, iterations=100):
        self.behaviors = behaviors if behaviors else load_user_behaviors()
        self.latent_factors = latent_factors
        self.learning_rate = learning_rate
        self.regularization = regularization
        self.iterations = iterations

        self.user_matrix = None
        self.item_matrix = None
        self.user_bias = None
        self.item_bias = None
        self.global_bias = None

        self.user_id_map = {}
        self.item_id_map = {}
        self.item_id_list = []

    def _build_mappings(self):
        """构建ID到索引的映射"""
        users = sorted(set(self.behaviors.keys()))
        items = set()
        for user_items in self.behaviors.values():
            items.update(user_items)
        items = sorted(items)

        self.user_id_map = {user: idx for idx, user in enumerate(users)}
        self.item_id_map = {item: idx for idx, item in enumerate(items)}
        self.item_id_list = items

        return len(users), len(items)

    def _create_rating_matrix(self, num_users, num_items):
        """创建评分矩阵"""
        R = np.zeros((num_users, num_items))
        for user, items in self.behaviors.items():
            if user in self.user_id_map:
                u_idx = self.user_id_map[user]
                for item in items:
                    if item in self.item_id_map:
                        i_idx = self.item_id_map[item]
                        R[u_idx, i_idx] = 1.0
        return R

    def train(self):
        """训练矩阵分解模型"""
        num_users, num_items = self._build_mappings()

        if num_users == 0 or num_items == 0:
            return

        np.random.seed(42)
        self.user_matrix = np.random.randn(num_users, self.latent_factors) * 0.1
        self.item_matrix = np.random.randn(num_items, self.latent_factors) * 0.1
        self.user_bias = np.zeros(num_users)
        self.item_bias = np.zeros(num_items)

        R = self._create_rating_matrix(num_users, num_items)
        self.global_bias = np.mean(R[R > 0]) if np.any(R > 0) else 0.0

        for iteration in range(self.iterations):
            for user, items in self.behaviors.items():
                if user not in self.user_id_map:
                    continue
                u_idx = self.user_id_map[user]

                for item in items:
                    if item not in self.item_id_map:
                        continue
                    i_idx = self.item_id_map[item]

                    pred = self.global_bias + self.user_bias[u_idx] + self.item_bias[i_idx] + \
                           np.dot(self.user_matrix[u_idx], self.item_matrix[i_idx].T)

                    error = 1.0 - pred

                    self.user_matrix[u_idx] += self.learning_rate * (
                        error * self.item_matrix[i_idx] - self.regularization * self.user_matrix[u_idx]
                    )

                    self.item_matrix[i_idx] += self.learning_rate * (
                        error * self.user_matrix[u_idx] - self.regularization * self.item_matrix[i_idx]
                    )

                    self.user_bias[u_idx] += self.learning_rate * (error - self.regularization * self.user_bias[u_idx])
                    self.item_bias[i_idx] += self.learning_rate * (error - self.regularization * self.item_bias[i_idx])

    def recommend(self, user_id, top_k=20):
        """推荐"""
        if user_id not in self.behaviors:
            return {}

        if self.user_matrix is None:
            self.train()

        if user_id not in self.user_id_map:
            return {}

        u_idx = self.user_id_map[user_id]
        user_articles = set(self.behaviors[user_id])

        predictions = []
        for item in self.item_id_list:
            if item in user_articles:
                continue

            if item in self.item_id_map:
                i_idx = self.item_id_map[item]
                pred = self.global_bias + self.user_bias[u_idx] + self.item_bias[i_idx] + \
                       np.dot(self.user_matrix[u_idx], self.item_matrix[i_idx].T)
                predictions.append((item, float(pred)))

        predictions.sort(key=lambda x: x[1], reverse=True)
        return {item: score for item, score in predictions[:top_k]}


# =============================
# 多模态特征提取类
# =============================
class MultimodalFeatureExtractor:
    """多模态特征提取器（文本 + 图片）"""

    def __init__(self, embedding_dim=128):
        self.embedding_dim = embedding_dim
        self.text_encoder_available = False
        self.image_encoder_available = False

        try:
            from sentence_transformers import SentenceTransformer
            # 使用 HuggingFace Token 进行认证，提高下载速度和速率限制
            model_kwargs = {}
            if HF_TOKEN:
                model_kwargs['use_auth_token'] = HF_TOKEN
            self.text_model = SentenceTransformer('all-MiniLM-L6-v2', **model_kwargs)
            self.text_encoder_available = True
        except ImportError:
            print("Warning: sentence-transformers not available, text features will be simulated")
            self.text_model = None
        except Exception as e:
            print(f"Warning: Failed to load sentence-transformers model: {e}")
            self.text_model = None

        try:
            import torch
            from torchvision import models, transforms
            from torchvision.models import ResNet50_Weights
            from PIL import Image
            self.torch = torch
            self.models = models
            self.transforms = transforms
            self.Image = Image
            self.image_model = models.resnet50(weights=ResNet50_Weights.DEFAULT)
            self.image_model.eval()
            self.image_encoder_available = True
        except ImportError:
            print("Warning: torch/torchvision/PIL not available, image features will be simulated")
            self.image_model = None

    def extract_text_feature(self, text):
        """提取文本特征"""
        if self.text_encoder_available and self.text_model:
            return self.text_model.encode(text)
        else:
            # 模拟文本特征
            np.random.seed(hash(text) % (2**32))
            return np.random.randn(384)

    def extract_image_feature(self, image_path):
        """提取图片特征"""
        if not image_path or not os.path.exists(image_path):
            return np.zeros(1000)

        if self.image_encoder_available and self.image_model:
            try:
                preprocess = self.transforms.Compose([
                    self.transforms.Resize((224, 224)),
                    self.transforms.ToTensor(),
                    self.transforms.Normalize(mean=[0.485, 0.456, 0.406],
                                             std=[0.229, 0.224, 0.225])
                ])
                image = self.Image.open(image_path).convert("RGB")
                input_tensor = preprocess(image).unsqueeze(0)
                with self.torch.no_grad():
                    feature = self.image_model(input_tensor)
                return feature.squeeze().numpy()
            except Exception as e:
                print(f"Error extracting image feature: {e}")
                return np.zeros(1000)
        else:
            # 模拟图片特征
            np.random.seed(hash(image_path) % (2**32))
            return np.random.randn(1000)

    def extract_multimodal_feature(self, article):
        """提取多模态特征"""
        text = f"{article['title']} {article['subtitle']} {article['content']}"
        text_feature = self.extract_text_feature(text)

        image_feature = np.zeros(1000)
        if article.get('image_urls'):
            first_image = article['image_urls'][0] if article['image_urls'] else None
            image_path = get_full_image_path(first_image)
            if image_path:
                image_feature = self.extract_image_feature(image_path)

        # 拼接多模态特征
        multimodal_feature = np.concatenate([text_feature, image_feature])
        return multimodal_feature


# =============================
# 双塔 DSSM 推荐类
# =============================
class DSSMRecommender:
    """多模态双塔 DSSM 推荐器"""

    def __init__(self, embedding_dim=128):
        self.embedding_dim = embedding_dim
        self.feature_extractor = MultimodalFeatureExtractor(embedding_dim)
        self.user_embeddings = {}
        self.item_embeddings = {}
        self.item_features = {}
        self.user_id_map = {}
        self.item_id_map = {}
        self.user_id_list = []
        self.item_id_list = []

        # 简单的MLP层参数
        self.user_mlp_weights = None
        self.user_mlp_bias = None
        self.item_mlp_weights = None
        self.item_mlp_bias = None

    def fit(self, articles, behaviors):
        """训练 DSSM 模型"""
        self.item_id_list = [article['article_id'] for article in articles]
        self.item_id_map = {aid: idx for idx, aid in enumerate(self.item_id_list)}

        self.user_id_list = sorted(behaviors.keys())
        self.user_id_map = {uid: idx for idx, uid in enumerate(self.user_id_list)}

        # 提取物品的多模态特征
        print("Extracting multimodal features for items...")
        for article in articles:
            aid = article['article_id']
            self.item_features[aid] = self.feature_extractor.extract_multimodal_feature(article)

        # 初始化MLP参数
        input_dim = 384 + 1000  # text (384) + image (1000)
        np.random.seed(42)
        self.user_mlp_weights = np.random.randn(input_dim, self.embedding_dim) * 0.1
        self.user_mlp_bias = np.random.randn(self.embedding_dim) * 0.1
        self.item_mlp_weights = np.random.randn(input_dim, self.embedding_dim) * 0.1
        self.item_mlp_bias = np.random.randn(self.embedding_dim) * 0.1

        # 计算物品嵌入
        print("Computing item embeddings...")
        for aid in self.item_id_list:
            feature = self.item_features[aid]
            embedding = self._item_mlp_forward(feature)
            self.item_embeddings[aid] = embedding

        # 计算用户嵌入（基于历史物品的平均）
        print("Computing user embeddings...")
        for user_id in self.user_id_list:
            user_items = behaviors.get(user_id, [])
            if user_items:
                item_embs = []
                for aid in user_items:
                    if aid in self.item_embeddings:
                        item_embs.append(self.item_embeddings[aid])
                if item_embs:
                    user_embedding = np.mean(item_embs, axis=0)
                    self.user_embeddings[user_id] = user_embedding

    # 用户塔的输入是用户喜欢的文章的向量
    def _user_mlp_forward(self, x):
        """用户塔前向传播"""
        return np.tanh(np.dot(x, self.user_mlp_weights) + self.user_mlp_bias)

    def _item_mlp_forward(self, x):
        """物品塔前向传播"""
        return np.tanh(np.dot(x, self.item_mlp_weights) + self.item_mlp_bias)

    def get_user_embedding(self, user_id, behaviors):
        """获取用户嵌入"""
        if user_id in self.user_embeddings:
            return self.user_embeddings[user_id]

        # 冷启动：基于用户历史物品计算
        user_items = behaviors.get(user_id, [])
        if user_items:
            item_embs = []
            for aid in user_items:
                if aid in self.item_embeddings:
                    item_embs.append(self.item_embeddings[aid])
            if item_embs:
                return np.mean(item_embs, axis=0)

        return np.zeros(self.embedding_dim)

    def recommend(self, user_id, behaviors, top_k=20):
        """基于 DSSM 的推荐"""
        if not self.item_embeddings:
            return {}

        user_emb = self.get_user_embedding(user_id, behaviors)
        user_articles = set(behaviors.get(user_id, []))

        scores = []
        for aid, item_emb in self.item_embeddings.items():
            if aid in user_articles:
                continue
            score = float(np.dot(user_emb, item_emb))
            scores.append((aid, score))

        scores.sort(key=lambda x: x[1], reverse=True)
        return {aid: score for aid, score in scores[:top_k]}

    def query_by_multimodal(self, query_text=None, query_image_path=None, top_k=20):
        """
        基于多模态查询的推荐
        :param query_text: 查询文本
        :param query_image_path: 查询图片路径
        :param top_k: 返回数量
        :return: 推荐结果字典
        """
        if not self.item_embeddings:
            return {}

        # 提取查询的多模态特征
        text_feature = np.zeros(384)
        if query_text:
            text_feature = self.feature_extractor.extract_text_feature(query_text)

        image_feature = np.zeros(1000)
        if query_image_path:
            full_image_path = get_full_image_path(query_image_path)
            if full_image_path:
                image_feature = self.feature_extractor.extract_image_feature(full_image_path)

        # 拼接多模态特征
        query_feature = np.concatenate([text_feature, image_feature])

        # 通过物品塔计算查询嵌入
        query_embedding = self._item_mlp_forward(query_feature)

        # 计算与所有物品的相似度
        scores = []
        for aid, item_emb in self.item_embeddings.items():
            score = float(np.dot(query_embedding, item_emb))
            scores.append((aid, score))

        scores.sort(key=lambda x: x[1], reverse=True)
        return {aid: score for aid, score in scores[:top_k]}


# =============================
# 混合推荐器（多模态版）
# =============================
class HybridMultimodalRecommender:
    """混合推荐器（结合内容推荐、协同过滤、多模态双塔）"""

    def __init__(self):
        self.content_rec = ContentBasedRecommender()
        self.cf_rec = CollaborativeFilteringRecommender()
        self.mf_rec = MatrixFactorizationRecommender()
        self.dssm_rec = DSSMRecommender()
        self.articles = None
        self.behaviors = None
        self.dssm_initialized = False

    def _init_dssm(self):
        """初始化 DSSM 模型"""
        print(f"_init_dssm called: dssm_initialized={self.dssm_initialized}, has_articles={bool(self.articles)}, has_behaviors={bool(self.behaviors)}")
        if not self.dssm_initialized:
            if not self.articles:
                print("Loading articles...")
                self.articles = load_articles()
            if not self.behaviors:
                print("Loading behaviors...")
                self.behaviors = load_user_behaviors()

            # 只要有文章数据就能初始化 DSSM（用户行为不是必须的，用于查询时不需要）
            if self.articles:
                print("Initializing DSSM model...")
                # 如果没有用户行为数据，传一个空字典
                behaviors_to_use = self.behaviors if self.behaviors else {}
                self.dssm_rec.fit(self.articles, behaviors_to_use)
                self.dssm_initialized = True
                print(f"DSSM initialized, item_embeddings count: {len(self.dssm_rec.item_embeddings)}")
            else:
                print("Could not initialize DSSM: missing articles")

    def recommend(self, user_id, query=None, query_image_path=None, top_k=10,
                  alpha=0.3, beta=0.3, gamma=0.4,
                  cf_method="model_based"):
        """
        混合推荐
        :param user_id: 用户ID
        :param query: 查询词（可选）
        :param query_image_path: 查询图片路径（可选）
        :param top_k: 返回数量
        :param alpha: 内容推荐权重
        :param beta: 协同过滤权重
        :param gamma: DSSM权重
        :param cf_method: 协同过滤方法
        :return: 推荐结果列表
        """
        # 智能权重调整：如果有图片查询，提高DSSM权重

        self.articles = load_articles()
        self.behaviors = load_user_behaviors()

        if not self.articles:
            return []

        # 初始化内容推荐器
        self.content_rec.fit(self.articles)

        # 1. 基于用户偏好的内容推荐
        preference_scores = self.content_rec.recommend_by_preference(
            user_id, self.behaviors, top_k=top_k * 2
        )

        # 2. 基于查询词的内容推荐
        content_scores = {}
        if query:
            content_scores = self.content_rec.recall(query, top_k=top_k * 2)
            content_scores = list(content_scores.items())

        # 3. 协同过滤推荐
        if cf_method == "item_based":
            cf_scores = self.cf_rec.item_based_cf(user_id, top_k=top_k * 2)
        elif cf_method == "model_based":
            cf_scores = self.mf_rec.recommend(user_id, top_k=top_k * 2)
        else:
            cf_scores = self.cf_rec.user_based_cf(user_id, top_k=top_k * 2)
        cf_scores = list(cf_scores.items())

        # 4. DSSM 多模态推荐
        self._init_dssm()
        if query or query_image_path:
            # 如果有查询（文本或图片），使用多模态查询
            dssm_scores = self.dssm_rec.query_by_multimodal(
                query_text=query,
                query_image_path=query_image_path,
                top_k=top_k * 2
            )
        else:
            # 否则使用基于用户偏好的推荐
            dssm_scores = self.dssm_rec.recommend(user_id, self.behaviors, top_k=top_k * 2)
        dssm_scores = list(dssm_scores.items())

        # 5. 加权融合
        combined_scores = {}

        # 归一化得分并融合
        def normalize_scores(scores):
            if not scores:
                return {}
            max_score = max(s for _, s in scores) if scores else 1.0
            min_score = min(s for _, s in scores) if scores else 0.0
            if max_score - min_score <= 1e-6:
                return {a: 0.5 for a, s in scores}
            return {a: (s - min_score) / (max_score - min_score) for a, s in scores}

        # 确保所有归一化后的得分都被正确定义
        norm_preference = normalize_scores(preference_scores) if preference_scores else {}
        norm_content = normalize_scores(content_scores) if content_scores else {}
        norm_cf = normalize_scores(cf_scores) if cf_scores else {}
        norm_dssm = normalize_scores(dssm_scores) if dssm_scores else {}

        # 获取所有候选物品
        all_items = set()
        for scores_dict in [norm_preference, norm_content, norm_cf, norm_dssm]:
            all_items.update(scores_dict.keys())

        # 如果没有候选物品，返回空列表
        if not all_items:
            return []

        for item in all_items:
            score = 0.0
            if query:
                # 有query时，使用偏好推荐+内容推荐
                if item in norm_preference:
                    score += norm_preference[item] * alpha * 0.5
                if item in norm_content:
                    score += norm_content[item] * alpha * 0.5
            else:
                # 没有query时，直接使用偏好推荐
                if item in norm_preference:
                    score += norm_preference[item] * alpha
            if item in norm_cf:
                score += norm_cf[item] * beta
            if item in norm_dssm:
                score += norm_dssm[item] * gamma
            combined_scores[item] = score

        # 过滤已看过的文章
        user_articles = set(self.behaviors.get(user_id, []))
        combined_scores = {aid: score for aid, score in combined_scores.items() if aid not in user_articles}

        # 排序
        final_results = sorted(combined_scores.items(), key=lambda x: x[1], reverse=True)[:top_k]

        # 获取详细信息
        article_info = {article['article_id']: article for article in self.articles}
        detailed_results = []
        for aid, score in final_results:
            info = article_info.get(aid, {})
            detailed_results.append({
                "article_id": aid,
                "score": score,
                "score_detail": {
                    "preference": norm_preference.get(aid, 0),
                    "content": norm_content.get(aid, 0),
                    "cf": norm_cf.get(aid, 0),
                    "dssm": norm_dssm.get(aid, 0)
                },
                "title": info.get("title", "N/A"),
                "subtitle": info.get("subtitle", ""),
                "content": info.get("content", "")[:100] + "..." if info.get("content") else "N/A",
                "image_urls": info.get("image_urls", [])
            })

        return detailed_results


# -----------------------------
# 主函数演示
# 用户嵌入向量是经过user_likes进行查询到的user_id=特定值的用户嵌入向量，物品嵌入向量是所有文章的嵌入向量
# -----------------------------
if __name__ == "__main__":
    print("多模态双塔推荐系统演示")
    print("=" * 60)

    user_id = 1
    # query = "大黄蜂"
    # query_image_path = "shturl.cc/rednote_image_1778466627463.jpg"  # 可以设置为图片路径进行测试
    query = None
    query_image_path = None

    print(f"\n用户ID: {user_id}")
    print(f"查询词: {query}")
    print(f"查询图片: {query_image_path or '无'}")

    # 测试混合推荐（多模态版）
    print("\n" + "=" * 60)
    print("混合推荐（内容 + 协同过滤 + 多模态双塔）...")
    hybrid_rec = HybridMultimodalRecommender()
    results = hybrid_rec.recommend(user_id, query, query_image_path, top_k=5,
                                    alpha=0.5, beta=0.3, gamma=0.2,
                                    cf_method="model_based")

    print("\n推荐结果:")
    for i, r in enumerate(results, 1):
        print(f"\n{i}. Article ID: {r['article_id']}")
        print(f"   标题: {r['title']}")
        print(f"   综合得分: {r['score']:.4f}")
        if 'score_detail' in r:
            print(f"   详细得分:")
            print(f"      - 偏好推荐: {r['score_detail']['preference']:.4f}")
            print(f"      - 内容推荐: {r['score_detail']['content']:.4f}")
            print(f"      - 协同过滤: {r['score_detail']['cf']:.4f}")
            print(f"      - DSSM多模态: {r['score_detail']['dssm']:.4f}")
        if r['image_urls']:
            print(f"   图片: {r['image_urls'][0]}")



# ### 1. 离线评估指标 （1）准确性指标
# - Precision@k ：前k个推荐中用户实际喜欢的比例
# - Recall@k ：用户喜欢的物品中被推荐出来的比例
# - F1@k ：Precision和Recall的调和平均
# - MAP（Mean Average Precision） ：平均准确率均值
# - NDCG@k ：归一化折损累计增益，考虑推荐顺序
# - MRR（Mean Reciprocal Rank） ：平均倒数排名