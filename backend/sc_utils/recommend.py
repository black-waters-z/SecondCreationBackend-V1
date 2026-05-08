import pandas as pd
import numpy as np
import sqlite3
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


# ===================== 1. 从 SQLite 读取帖子数据 =====================
DB_PATH = r"D:\Project\SecondCreationBackend-V1\scforum.db"

# 连接数据库
conn = sqlite3.connect(DB_PATH)

# 读取 post 表（如果你的表名不是 post，改成你自己的）
df = pd.read_sql_query("SELECT * FROM articles LIMIT 2000", conn)  # 取前2000条

# 关闭连接
conn.close()

# 数据清洗（必须字段）
df = df.dropna(subset=["id", "title", "content", "author_id"]).reset_index(drop=True)

# ===================== 2. 构建内容特征 =====================
# 合并标题 + 内容（推荐核心文本）
df["text"] = df["title"].fillna("") + " " + df["content"].fillna("")

# 热度权重（浏览+点赞+收藏）
df["hot"] = (
    df["view_count"].fillna(0) * 0.3 +
    df["like_count"].fillna(0) * 0.4 +
    df["favorite_count"].fillna(0) * 0.3
)
df["hot_weight"] = df["hot"] / df["hot"].max()  # 归一化 0~1

# TF-IDF 向量化
tfidf = TfidfVectorizer(stop_words="english", max_features=10000)
tfidf_matrix = tfidf.fit_transform(df["text"])

# ===================== 3. 构建用户-帖子交互矩阵 =====================
user_post_matrix = df.pivot_table(
    index="author_id",
    columns="id",
    values="like_count"
).fillna(0)

# ===================== 4. 内容推荐 =====================
def content_recommend(post_id, top_n=10):
    try:
        idx = df[df["id"] == post_id].index[0]
    except:
        return pd.DataFrame()

    sim = cosine_similarity(tfidf_matrix[idx], tfidf_matrix).flatten()
    sim = sim * df["hot_weight"].values  # 热度加权
    indices = np.argsort(sim)[::-1][1:top_n+1]

    recs = df.iloc[indices][["id", "title", "view_count", "like_count"]].copy()
    recs["content_score"] = np.round(sim[indices], 4)
    return recs

# ===================== 5. 协同过滤推荐 =====================
def collab_recommend(post_id, top_n=10):
    if post_id not in user_post_matrix.columns:
        return pd.DataFrame()

    item_sim = cosine_similarity(user_post_matrix.T)
    idx = list(user_post_matrix.columns).index(post_id)
    sim = item_sim[idx]
    indices = np.argsort(sim)[::-1][1:top_n+1]

    recs = pd.DataFrame({
        "id": [user_post_matrix.columns[i] for i in indices],
        "collab_score": np.round(sim[indices], 4)
    })
    return recs

# ===================== 6. 混合推荐（核心） =====================
def hybrid_post_recommend(post_id, w_content=0.6, w_collab=0.4, top_n=10):
    content_rec = content_recommend(post_id, 20)
    collab_rec = collab_recommend(post_id, 20)

    merged = pd.merge(content_rec, collab_rec, on="id", how="outer").fillna(0)
    merged["final_score"] = merged["content_score"] * w_content + merged["collab_score"] * w_collab
    merged = merged.sort_values("final_score", ascending=False).head(top_n)
    return merged.reset_index(drop=True)

# ===================== 测试 =====================
if __name__ == "__main__":
    test_post_id = df["id"].iloc[0]
    print("测试帖子 ID:", test_post_id)
    print("标题:", df[df["id"] == test_post_id]["title"].values[0])

    print("\n===== 混合推荐结果 =====")
    result = hybrid_post_recommend(test_post_id, 0.6, 0.4, top_n=10)
    print(result[["id", "title", "final_score"]])