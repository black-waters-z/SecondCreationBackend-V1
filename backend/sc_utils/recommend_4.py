# -*- coding: utf-8 -*-
"""
多模态双塔推荐系统 - Scikit-learn优化版
结合：
1. 基于内容的推荐（Scikit-learn TF-IDF）
2. 协同过滤（Scikit-learn 相似度计算）
3. 矩阵分解（Scikit-learn NMF）
4. 多模态双塔模型（DSSM）- 文本 + 图片特征
"""
import sqlite3
import math
import os
import json
from PIL import Image
from collections import defaultdict
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.decomposition import NMF
from sklearn.preprocessing import normalize

# -----------------------------
# 配置
# -----------------------------
SQLITE_DB_PATH = r"D:\projects\SecondCreationBackend-V1\scforum.db"
IMAGE_ROOT_DIR = r"D:\projects\SecondCreationBackend-V1\backend\static\upload_IMG"

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
            "subtitle": r[2],
            "content": r[3],
            "image_urls": image_urls
        })
    return articles

def load_user_behaviors():
    """加载用户行为数据（点赞、收藏等）"""
    conn = sqlite3.connect(SQLITE_DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT user_id, article_id FROM user_likes")
    rows = cursor.fetchall()
    conn.close()
    
    behaviors = defaultdict(list)
    for user_id, article_id in rows:
        behaviors[int(user_id)].append(int(article_id))
    
    return dict(behaviors)

# -----------------------------
# 基于内容的推荐（Scikit-learn TF-IDF）
# -----------------------------
class ContentBasedRecommender:
    """基于内容的推荐器 - 使用Scikit-learn TF-IDF"""

    def __init__(self, articles=None):
        self.articles = articles if articles else load_articles()
        self.tfidf_matrix = None
        self.vectorizer = None
        self.article_ids = [article['article_id'] for article in self.articles]
        self._build_tfidf_matrix()

    def _build_tfidf_matrix(self):
        """使用Scikit-learn构建TF-IDF矩阵"""
        # 合并标题、副标题和内容
        texts = []
        for article in self.articles:
            text_parts = [
                article['title'] or '',
                article['subtitle'] or '',
                article['content'] or ''
            ]
            full_text = ' '.join(text_parts)
            texts.append(full_text)

        # 使用Scikit-learn的TF-IDF向量化器
        self.vectorizer = TfidfVectorizer(
            stop_words=list(STOPWORDS),
            max_features=5000,
            ngram_range=(1, 2),
            token_pattern=r'\b\w+\b'
        )
        self.tfidf_matrix = self.vectorizer.fit_transform(texts)

    def recommend_by_content(self, query=None, article_id=None, top_k=20):
        """基于内容的推荐"""
        if query:
            # 根据查询文本推荐相似文章
            query_vec = self.vectorizer.transform([query])
            similarities = cosine_similarity(query_vec, self.tfidf_matrix).flatten()
        elif article_id:
            # 根据文章ID推荐相似文章
            try:
                idx = self.article_ids.index(article_id)
                article_vec = self.tfidf_matrix[idx]
                similarities = cosine_similarity(article_vec, self.tfidf_matrix).flatten()
            except ValueError:
                return {}
        else:
            return {}

        # 获取相似度最高的文章
        similar_indices = similarities.argsort()[::-1][1:top_k+1]  # 排除自身
        recommendations = {}
        for idx in similar_indices:
            recommendations[self.article_ids[idx]] = float(similarities[idx])

        return recommendations

# -----------------------------
# 协同过滤推荐（Scikit-learn优化）
# -----------------------------
class CollaborativeFilteringRecommender:
    """协同过滤推荐器 - 使用Scikit-learn相似度计算"""

    def __init__(self, behaviors=None):
        self.behaviors = behaviors if behaviors else load_user_behaviors()
        self.user_item_matrix = None
        self.user_index = {}
        self.item_index = {}
        self._build_user_item_matrix()

    def _build_user_item_matrix(self):
        """构建用户-物品矩阵"""
        users = sorted(self.behaviors.keys())
        items = sorted(list({item for user_items in self.behaviors.values() for item in user_items}))

        self.user_index = {user: i for i, user in enumerate(users)}
        self.item_index = {item: i for i, item in enumerate(items)}

        # 创建用户-物品矩阵
        self.user_item_matrix = np.zeros((len(users), len(items)))
        for user, items in self.behaviors.items():
            user_idx = self.user_index[user]
            for item in items:
                item_idx = self.item_index[item]
                self.user_item_matrix[user_idx, item_idx] = 1.0

    def user_based_cf(self, user_id, top_k=20, k_neighbors=5):
        """基于用户的协同过滤 - 使用Scikit-learn余弦相似度"""
        if user_id not in self.user_index:
            return {}

        user_idx = self.user_index[user_id]
        user_vec = self.user_item_matrix[user_idx].reshape(1, -1)

        # 使用Scikit-learn计算余弦相似度
        similarities = cosine_similarity(user_vec, self.user_item_matrix).flatten()

        # 获取最相似的用户（排除自身）
        similar_indices = similarities.argsort()[::-1][1:k_neighbors+1]

        # 计算推荐分数
        scores = defaultdict(float)
        for idx in similar_indices:
            similarity = similarities[idx]
            neighbor_items = self.user_item_matrix[idx].nonzero()[0]
            for item_idx in neighbor_items:
                if self.user_item_matrix[user_idx, item_idx] == 0:  # 用户未交互过的物品
                    item_id = next(k for k, v in self.item_index.items() if v == item_idx)
                    scores[item_id] += similarity

        # 归一化分数
        if scores:
            max_score = max(scores.values())
            scores = {item: score / max_score for item, score in scores.items()}

        # 返回Top-K推荐
        sorted_scores = sorted(scores.items(), key=lambda x: x[1], reverse=True)[:top_k]
        return dict(sorted_scores)

    def item_based_cf(self, user_id, top_k=20, k_items=5):
        """基于物品的协同过滤 - 使用Scikit-learn余弦相似度"""
        if user_id not in self.user_index:
            return {}

        user_idx = self.user_index[user_id]
        user_items = self.user_item_matrix[user_idx].nonzero()[0]

        if not user_items.size:
            return {}

        # 计算物品相似度矩阵
        item_similarities = cosine_similarity(self.user_item_matrix.T)

        # 计算推荐分数
        scores = defaultdict(float)
        for item_idx in user_items:
            # 获取相似物品
            similar_indices = item_similarities[item_idx].argsort()[::-1][1:k_items+1]
            for sim_idx in similar_indices:
                if self.user_item_matrix[user_idx, sim_idx] == 0:  # 用户未交互过的物品
                    item_id = next(k for k, v in self.item_index.items() if v == sim_idx)
                    scores[item_id] += item_similarities[item_idx, sim_idx]

        # 归一化分数
        if scores:
            max_score = max(scores.values())
            scores = {item: score / max_score for item, score in scores.items()}

        # 返回Top-K推荐
        sorted_scores = sorted(scores.items(), key=lambda x: x[1], reverse=True)[:top_k]
        return dict(sorted_scores)

# -----------------------------
# 矩阵分解推荐（Scikit-learn NMF）
# -----------------------------
class MatrixFactorizationRecommender:
    """矩阵分解推荐器 - 使用Scikit-learn NMF"""

    def __init__(self, behaviors=None, n_components=20):
        self.behaviors = behaviors if behaviors else load_user_behaviors()
        self.n_components = n_components
        self.user_item_matrix = None
        self.user_index = {}
        self.item_index = {}
        self.model = None
        self.user_embeddings = None
        self.item_embeddings = None
        self._build_model()

    def _build_model(self):
        """使用Scikit-learn NMF构建矩阵分解模型"""
        users = sorted(self.behaviors.keys())
        items = sorted(list({item for user_items in self.behaviors.values() for item in user_items}))

        self.user_index = {user: i for i, user in enumerate(users)}
        self.item_index = {item: i for i, item in enumerate(items)}

        # 创建用户-物品矩阵
        self.user_item_matrix = np.zeros((len(users), len(items)))
        for user, items in self.behaviors.items():
            user_idx = self.user_index[user]
            for item in items:
                item_idx = self.item_index[item]
                self.user_item_matrix[user_idx, item_idx] = 1.0

        # 使用Scikit-learn NMF进行矩阵分解
        self.model = NMF(
            n_components=self.n_components,
            init='random',
            random_state=42,
            max_iter=500
        )

        self.user_embeddings = self.model.fit_transform(self.user_item_matrix)
        self.item_embeddings = self.model.components_.T

        # 归一化嵌入向量
        self.user_embeddings = normalize(self.user_embeddings)
        self.item_embeddings = normalize(self.item_embeddings)

    def recommend(self, user_id, top_k=20):
        """使用矩阵分解进行推荐"""
        if user_id not in self.user_index:
            return {}

        user_idx = self.user_index[user_id]
        user_vec = self.user_embeddings[user_idx].reshape(1, -1)

        # 计算用户与所有物品的相似度
        scores = cosine_similarity(user_vec, self.item_embeddings).flatten()

        # 排除用户已交互过的物品
        user_items = self.behaviors[user_id]
        item_indices = [self.item_index[item] for item in user_items if item in self.item_index]
        scores[item_indices] = -1.0

        # 获取Top-K推荐
        top_indices = scores.argsort()[::-1][:top_k]
        recommendations = {}
        for idx in top_indices:
            item_id = next(k for k, v in self.item_index.items() if v == idx)
            recommendations[item_id] = float(scores[idx])

        return recommendations

# -----------------------------
# 多模态双塔模型（DSSM）
# -----------------------------
class DSSMRecommender:
    """多模态双塔推荐器 - 保留原实现"""

    def __init__(self, articles=None, behaviors=None):
        self.articles = articles if articles else load_articles()
        self.behaviors = behaviors if behaviors else load_user_behaviors()
        self.user_embeddings = {}
        self.item_embeddings = {}
        self._init_models()

    def _init_models(self):
        """初始化预训练模型"""
        try:
            from sentence_transformers import SentenceTransformer
            from PIL import Image
            import torch

            self.text_model = SentenceTransformer('all-MiniLM-L6-v2')
            self.image_model = SentenceTransformer('clip-ViT-B-32')
            self.device = 'cuda' if torch.cuda.is_available() else 'cpu'

            # 预计算物品嵌入
            self._precompute_item_embeddings()

        except ImportError as e:
            print(f"警告: 缺少必要的库，DSSM功能将受限: {e}")
            self.text_model = None
            self.image_model = None

    def _precompute_item_embeddings(self):
        """预计算所有物品的嵌入向量"""
        if not self.text_model:
            return

        for article in self.articles:
            article_id = article['article_id']
            
            # 文本特征
            text_parts = [
                article['title'] or '',
                article['subtitle'] or '',
                article['content'][:200] or ''  # 取前200个字符
            ]
            full_text = ' '.join(text_parts)
            text_embedding = self.text_model.encode(full_text)

            # 图片特征
            image_embedding = None
            if article['image_urls']:
                try:
                    image_path = os.path.join(IMAGE_ROOT_DIR, article['image_urls'][0].split('/')[-1])
                    if os.path.exists(image_path):
                        image = Image.open(image_path).convert('RGB')
                        image_embedding = self.image_model.encode(image)
                except Exception as e:
                    print(f"警告: 无法加载图片 {article['image_urls'][0]}: {e}")

            # 融合特征
            if image_embedding is not None:
                combined_embedding = np.concatenate([text_embedding, image_embedding])
            else:
                combined_embedding = text_embedding

            # 归一化
            combined_embedding = combined_embedding / np.linalg.norm(combined_embedding)
            self.item_embeddings[article_id] = combined_embedding

    def _get_user_embedding(self, user_id):
        """获取用户嵌入向量"""
        if user_id in self.user_embeddings:
            return self.user_embeddings[user_id]

        if not self.text_model or user_id not in self.behaviors:
            return None

        # 根据用户交互的物品计算用户嵌入
        user_items = self.behaviors[user_id]
        item_embeddings = []

        for item_id in user_items:
            if item_id in self.item_embeddings:
                item_embeddings.append(self.item_embeddings[item_id])

        if not item_embeddings:
            return None

        # 平均物品嵌入作为用户嵌入
        user_embedding = np.mean(item_embeddings, axis=0)
        user_embedding = user_embedding / np.linalg.norm(user_embedding)
        self.user_embeddings[user_id] = user_embedding

        return user_embedding

    def recommend(self, user_id, behaviors=None, top_k=20):
        """基于用户偏好的多模态推荐"""
        if not self.text_model:
            return {}

        user_embedding = self._get_user_embedding(user_id)
        if user_embedding is None:
            return {}

        # 计算用户与所有物品的相似度
        scores = {}
        for item_id, item_embedding in self.item_embeddings.items():
            if item_id not in self.behaviors.get(user_id, []):
                similarity = cosine_similarity(user_embedding.reshape(1, -1), item_embedding.reshape(1, -1))[0][0]
                scores[item_id] = float(similarity)

        # 返回Top-K推荐
        sorted_scores = sorted(scores.items(), key=lambda x: x[1], reverse=True)[:top_k]
        return dict(sorted_scores)

    def query_by_multimodal(self, query_text=None, query_image_path=None, top_k=20):
        """多模态查询推荐"""
        if not self.text_model:
            return {}

        # 处理文本查询
        text_embedding = None
        if query_text:
            text_embedding = self.text_model.encode(query_text)

        # 处理图片查询
        image_embedding = None
        if query_image_path and os.path.exists(query_image_path):
            try:
                from PIL import Image
                image = Image.open(query_image_path).convert('RGB')
                image_embedding = self.image_model.encode(image)
            except Exception as e:
                print(f"警告: 无法加载查询图片: {e}")

        # 融合查询特征
        if text_embedding is not None and image_embedding is not None:
            query_embedding = np.concatenate([text_embedding, image_embedding])
        elif text_embedding is not None:
            query_embedding = text_embedding
        elif image_embedding is not None:
            query_embedding = image_embedding
        else:
            return {}

        # 归一化
        query_embedding = query_embedding / np.linalg.norm(query_embedding)

        # 计算查询与所有物品的相似度
        scores = {}
        for item_id, item_embedding in self.item_embeddings.items():
            similarity = cosine_similarity(query_embedding.reshape(1, -1), item_embedding.reshape(1, -1))[0][0]
            scores[item_id] = float(similarity)

        # 返回Top-K推荐
        sorted_scores = sorted(scores.items(), key=lambda x: x[1], reverse=True)[:top_k]
        return dict(sorted_scores)

# -----------------------------
# 混合推荐器
# -----------------------------
class HybridMultimodalRecommender:
    """多模态混合推荐器"""

    def __init__(self):
        self.articles = load_articles()
        self.behaviors = load_user_behaviors()
        
        # 初始化各个推荐器
        self.content_rec = ContentBasedRecommender(self.articles)
        self.cf_rec = CollaborativeFilteringRecommender(self.behaviors)
        self.mf_rec = MatrixFactorizationRecommender(self.behaviors)
        self.dssm_rec = None

    def _init_dssm(self):
        """延迟初始化DSSM模型"""
        if not self.dssm_rec:
            self.dssm_rec = DSSMRecommender(self.articles, self.behaviors)

    def recommend(self, user_id, query=None, query_image_path=None, top_k=20,
                 alpha=0.3, beta=0.3, gamma=0.4, cf_method="model_based"):
        """混合推荐"""
        # 1. 基于内容的推荐
        if query:
            content_scores = self.content_rec.recommend_by_content(query=query, top_k=top_k * 2)
        else:
            # 如果没有查询，基于用户已交互物品进行内容推荐
            user_items = self.behaviors.get(user_id, [])
            content_scores = {}
            if user_items:
                # 取用户最近交互的物品
                representative_item = user_items[-1]
                content_scores = self.content_rec.recommend_by_content(article_id=representative_item, top_k=top_k * 2)

        # 2. 基于偏好的推荐（用户历史行为加权）
        preference_scores = {}
        if user_id in self.behaviors:
            user_items = self.behaviors[user_id]
            # 最近交互的物品权重更高
            for i, item_id in enumerate(reversed(user_items)):
                preference_scores[item_id] = 1.0 / (i + 1)  # 倒数衰减

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
        norm_preference = normalize_scores(preference_scores.items()) if preference_scores else {}
        norm_content = normalize_scores(content_scores.items()) if content_scores else {}
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
                # 有query时，使用偏好推荐+内容推荐 - 已调低保真推荐权重
                if item in norm_preference:
                    score += norm_preference[item] * alpha * 0.2  # 从0.5调至0.2
                if item in norm_content:
                    score += norm_content[item] * alpha * 0.8  # 从0.5调至0.8
            else:
                # 没有query时，直接使用偏好推荐 - 已调低保真推荐权重
                if item in norm_preference:
                    score += norm_preference[item] * alpha * 0.3  # 从1.0调至0.3
            if item in norm_cf:
                score += norm_cf[item] * beta
            if item in norm_dssm:
                score += norm_dssm[item] * gamma
            combined_scores[item] = score

        # 过滤已看过的文章 - 已注释，允许推荐用户已交互的文章
        # user_articles = set(self.behaviors.get(user_id, []))
        # combined_scores = {aid: score for aid, score in combined_scores.items() if aid not in user_articles}

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
# -----------------------------
if __name__ == "__main__":
    print("多模态双塔推荐系统 - Scikit-learn优化版演示")
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
    print("混合推荐（内容 + 协同过滤 + 矩阵分解 + 多模态双塔）...")
    hybrid_rec = HybridMultimodalRecommender()
    results = hybrid_rec.recommend(user_id, query, query_image_path, top_k=10,
                                   alpha=0.2, beta=0.3, gamma=0.5,
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