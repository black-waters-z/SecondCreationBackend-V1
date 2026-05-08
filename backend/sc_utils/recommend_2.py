# content_based_recommender.py
import sqlite3
import math
from collections import defaultdict
import numpy as np

# -----------------------------
# 配置
# -----------------------------
SQLITE_DB_PATH = r"D:\Project\SecondCreationBackend-V1\scforum.db"

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
    conn = sqlite3.connect(SQLITE_DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT id, title, content FROM articles WHERE status='published'")
    rows = cursor.fetchall()
    conn.close()
    return [{"article_id": int(r[0]), "title": r[1], "content": r[2]} for r in rows]


def load_user_behaviors():
    conn = sqlite3.connect(SQLITE_DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT user_id, article_id FROM user_likes")
    rows = cursor.fetchall()
    conn.close()
    behaviors = {}
    for r in rows:
        behaviors.setdefault(r[0], []).append(r[1])
    return behaviors


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
        article_texts = [f"{article['title']} {article['content']}" for article in articles]

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
        """
        基于内容的召回
        :param query: 查询词（可选）
        :param top_k: 返回数量
        :return: {article_id: score}, 详细信息列表
        """
        if self.article_vectors is None:
            articles = load_articles()
            self.fit(articles)

        if query:
            # 基于查询词的内容召回
            query_vector = self.transform_query(query)
            scores = []
            for i, aid in enumerate(self.article_ids):
                score = self.cosine_similarity(query_vector, self.article_vectors[i])
                scores.append((aid, score))
            scores.sort(key=lambda x: x[1], reverse=True)
            top_scores = scores[:top_k]

            detailed_candidates = []
            for aid, score in top_scores:
                info = self.article_info.get(aid, {})
                detailed_candidates.append({
                    "article_id": aid,
                    "title": info.get("title", "N/A"),
                    "content": info.get("content", "")[:100] + "..." if info.get("content") else "N/A",
                    "score": score
                })

            return {aid: score for aid, score in top_scores}, detailed_candidates

        return {}, []

    def learn_user_preference(self, user_id, behaviors):
        """
        学习用户偏好向量
        :param user_id: 用户ID
        :param behaviors: 用户行为字典
        :return: 用户偏好向量
        """
        user_articles = behaviors.get(user_id, [])
        if not user_articles:
            return np.zeros(self.article_vectors.shape[1])

        liked_indices = [i for i, aid in enumerate(self.article_ids) if aid in user_articles]
        if not liked_indices:
            return np.zeros(self.article_vectors.shape[1])

        liked_vectors = self.article_vectors[liked_indices]
        return np.mean(liked_vectors, axis=0)

    def recommend_by_preference(self, user_id, behaviors, top_k=10):
        """
        基于用户偏好的推荐
        :param user_id: 用户ID
        :param behaviors: 用户行为字典
        :param top_k: 返回数量
        :return: [(article_id, score), ...]
        """
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
# 基于模型的协同过滤推荐类（矩阵分解）
# =============================
class MatrixFactorizationRecommender:
    """基于矩阵分解的协同过滤推荐器（基于模型的方法）"""

    def __init__(self, behaviors=None, latent_factors=20, learning_rate=0.01, regularization=0.02, iterations=100):
        self.behaviors = behaviors if behaviors else load_user_behaviors()
        self.latent_factors = latent_factors  # 隐因子数量
        self.learning_rate = learning_rate    # 学习率
        self.regularization = regularization  # 正则化系数
        self.iterations = iterations          # 迭代次数

        self.user_matrix = None  # 用户隐因子矩阵
        self.item_matrix = None  # 物品隐因子矩阵
        self.user_bias = None    # 用户偏置
        self.item_bias = None    # 物品偏置
        self.global_bias = None  # 全局偏置

        self.user_id_map = {}    # 用户ID到索引的映射
        self.item_id_map = {}    # 物品ID到索引的映射
        self.item_id_list = []   # 物品ID列表

    def _build_mappings(self):
        """构建用户和物品的ID到索引的映射"""
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
        """创建评分矩阵（二值评分）"""
        R = np.zeros((num_users, num_items))
        for user, items in self.behaviors.items():
            if user in self.user_id_map:
                u_idx = self.user_id_map[user]
                for item in items:
                    if item in self.item_id_map:
                        i_idx = self.item_id_map[item]
                        R[u_idx, i_idx] = 1.0  # 喜欢=1
        return R

    def train(self):
        """训练矩阵分解模型"""
        num_users, num_items = self._build_mappings()

        if num_users == 0 or num_items == 0:
            return

        # 初始化隐因子矩阵和偏置
        np.random.seed(42)
        self.user_matrix = np.random.randn(num_users, self.latent_factors) * 0.1
        self.item_matrix = np.random.randn(num_items, self.latent_factors) * 0.1
        self.user_bias = np.zeros(num_users)
        self.item_bias = np.zeros(num_items)

        # 计算全局偏置（所有评分的平均值）
        R = self._create_rating_matrix(num_users, num_items)
        self.global_bias = np.mean(R[R > 0])

        # 随机梯度下降训练
        for iteration in range(self.iterations):
            for user, items in self.behaviors.items():
                if user not in self.user_id_map:
                    continue
                u_idx = self.user_id_map[user]

                for item in items:
                    if item not in self.item_id_map:
                        continue
                    i_idx = self.item_id_map[item]

                    # 计算预测评分
                    pred = self.global_bias + self.user_bias[u_idx] + self.item_bias[i_idx] + \
                           np.dot(self.user_matrix[u_idx], self.item_matrix[i_idx].T)

                    # 计算误差
                    error = 1.0 - pred  # 实际评分是1（喜欢）

                    # 更新用户隐因子
                    self.user_matrix[u_idx] += self.learning_rate * (
                        error * self.item_matrix[i_idx] - self.regularization * self.user_matrix[u_idx]
                    )

                    # 更新物品隐因子
                    self.item_matrix[i_idx] += self.learning_rate * (
                        error * self.user_matrix[u_idx] - self.regularization * self.item_matrix[i_idx]
                    )

                    # 更新偏置
                    self.user_bias[u_idx] += self.learning_rate * (error - self.regularization * self.user_bias[u_idx])
                    self.item_bias[i_idx] += self.learning_rate * (error - self.regularization * self.item_bias[i_idx])

    def predict(self, user_id, item_id):
        """预测用户对物品的评分"""
        if user_id not in self.user_id_map or item_id not in self.item_id_map:
            return 0.0

        u_idx = self.user_id_map[user_id]
        i_idx = self.item_id_map[item_id]

        pred = self.global_bias + self.user_bias[u_idx] + self.item_bias[i_idx] + \
               np.dot(self.user_matrix[u_idx], self.item_matrix[i_idx].T)

        return float(pred)

    def recommend(self, user_id, top_k=20):
        """
        基于矩阵分解模型的推荐
        :param user_id: 用户ID
        :param top_k: 返回数量
        :return: {article_id: score}
        """
        if user_id not in self.behaviors:
            return {}

        # 如果模型尚未训练，先训练
        if self.user_matrix is None:
            self.train()

        if user_id not in self.user_id_map:
            return {}

        u_idx = self.user_id_map[user_id]
        user_articles = set(self.behaviors[user_id])

        # 预测所有物品的评分
        predictions = []
        for item in self.item_id_list:
            if item in user_articles:
                continue

            if item in self.item_id_map:
                i_idx = self.item_id_map[item]
                pred = self.global_bias + self.user_bias[u_idx] + self.item_bias[i_idx] + \
                       np.dot(self.user_matrix[u_idx], self.item_matrix[i_idx].T)
                predictions.append((item, float(pred)))

        # 按预测评分排序
        predictions.sort(key=lambda x: x[1], reverse=True)

        return {item: score for item, score in predictions[:top_k]}


# =============================
# 协同过滤推荐类（基于邻域的方法）
# =============================
class CollaborativeFilteringRecommender:
    """协同过滤推荐器（支持基于用户和基于物品的协同过滤）"""

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
        """
        基于用户的协同过滤推荐
        :param user_id: 用户ID
        :param top_k: 返回数量
        :param k_neighbors: 相似用户数量
        :return: {article_id: score}
        """
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
        """
        基于物品的协同过滤推荐
        :param user_id: 用户ID
        :param top_k: 返回数量
        :param k_items: 相似物品数量
        :return: {article_id: score}
        """
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
# 混合推荐器
# =============================
class HybridRecommender:
    """混合推荐器（结合内容推荐和协同过滤）"""

    def __init__(self):
        self.content_rec = ContentBasedRecommender()
        self.cf_rec = CollaborativeFilteringRecommender()
        self.mf_rec = MatrixFactorizationRecommender()

    def recommend(self, user_id, query=None, top_k=10, alpha=0.7, beta=0.3, cf_method="user_based"):
        """
        混合推荐
        :param user_id: 用户ID
        :param query: 查询词（可选）
        :param top_k: 返回数量
        :param alpha: 内容推荐权重
        :param beta: 协同过滤权重
        :param cf_method: 协同过滤方法 ("user_based", "item_based", 或 "model_based")
        :return: 推荐结果列表
        """
        articles = load_articles()
        behaviors = load_user_behaviors()

        if not articles:
            return []

        # 初始化内容推荐器
        self.content_rec.fit(articles)

        # 1. 基于用户偏好的内容推荐
        preference_scores = self.content_rec.recommend_by_preference(
            user_id, behaviors, top_k=top_k * 2
        )

        # 2. 基于查询词的内容推荐
        content_scores = {}
        detailed_candidates = []
        if query:
            content_scores, detailed_candidates = self.content_rec.recall(query, top_k=top_k * 2)
            content_scores = list(content_scores.items())

        # 3. 协同过滤推荐
        if cf_method == "item_based":
            cf_scores = self.cf_rec.item_based_cf(user_id, top_k=top_k * 2)
        elif cf_method == "model_based":
            cf_scores = self.mf_rec.recommend(user_id, top_k=top_k * 2)
        else:
            cf_scores = self.cf_rec.user_based_cf(user_id, top_k=top_k * 2)
        cf_scores = list(cf_scores.items())

        # 4. 加权融合
        combined_scores = {}

        # 用户偏好得分
        for aid, score in preference_scores:
            combined_scores[aid] = score * (1 - alpha)

        # 查询内容得分
        for aid, score in content_scores:
            combined_scores[aid] = combined_scores.get(aid, 0) + score * alpha

        # 协同过滤得分
        for aid, score in cf_scores:
            combined_scores[aid] = combined_scores.get(aid, 0) + score * beta

        # 过滤已看过的文章
        user_articles = set(behaviors.get(user_id, []))
        combined_scores = {aid: score for aid, score in combined_scores.items() if aid not in user_articles}

        # 排序
        final_results = sorted(combined_scores.items(), key=lambda x: x[1], reverse=True)[:top_k]

        # 获取详细信息
        article_info = {article['article_id']: article for article in articles}
        detailed_results = []
        for aid, score in final_results:
            info = article_info.get(aid, {})
            detailed_results.append({
                "article_id": aid,
                "score": score,
                "title": info.get("title", "N/A"),
                "content": info.get("content", "")[:100] + "..." if info.get("content") else "N/A"
            })

        return detailed_results


# -----------------------------
# 主函数演示
# -----------------------------
if __name__ == "__main__":
    print("基于内容的推荐算法演示（改进版）")
    print("=" * 50)

    user_id = 1
    query = "创作的内容"

    print(f"\n用户ID: {user_id}")
    print(f"查询词: {query}")

    # 测试基于邻域的协同过滤推荐
    print("\n" + "=" * 50)
    print("基于用户的协同过滤推荐（基于邻域）...")
    cf_rec = CollaborativeFilteringRecommender()
    user_cf_results = cf_rec.user_based_cf(user_id, top_k=5)
    print(f"用户CF推荐结果: {user_cf_results}")

    print("\n" + "=" * 50)
    print("基于物品的协同过滤推荐（基于邻域）...")
    item_cf_results = cf_rec.item_based_cf(user_id, top_k=5)
    print(f"物品CF推荐结果: {item_cf_results}")

    # 测试基于模型的协同过滤推荐（矩阵分解）
    print("\n" + "=" * 50)
    print("基于模型的协同过滤推荐（矩阵分解）...")
    mf_rec = MatrixFactorizationRecommender()
    mf_results = mf_rec.recommend(user_id, top_k=5)
    print(f"矩阵分解推荐结果: {mf_results}")

    # 测试混合推荐（使用基于模型的协同过滤）
    print("\n" + "=" * 50)
    print("混合推荐（使用矩阵分解）...")
    hybrid_rec = HybridRecommender()
    results = hybrid_rec.recommend(user_id, query, top_k=5, cf_method="model_based")

    print("\n推荐结果:")
    for i, r in enumerate(results, 1):
        print(f"\n{i}. Article ID: {r['article_id']}")
        print(f"   标题: {r['title']}")
        print(f"   综合得分: {r['score']:.4f}")
        # print(f"   内容片段: {r['content']}")