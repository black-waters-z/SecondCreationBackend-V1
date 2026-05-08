# hybrid_content_cf_pymilvus.py
import sqlite3
from sentence_transformers import SentenceTransformer,CrossEncoder
from pymilvus import connections, FieldSchema, CollectionSchema, DataType, Collection, utility

# -----------------------------
# 配置 需要docker部署milvus，端口为19530。需要开vpn访问api。
# -----------------------------
SQLITE_DB_PATH = r"D:\projects\SecondCreationBackend-V1\scforum.db"
MILVUS_HOST = "localhost"
MILVUS_PORT = "19530"
COLLECTION_NAME = "articles_chunks"

BI_ENCODER_MODEL = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
CROSS_ENCODER_MODEL = "cross-encoder/ms-marco-MiniLM-L-6-v2"  # 多语言Cross-Encoder

bi_encoder = SentenceTransformer(BI_ENCODER_MODEL)
cross_encoder = CrossEncoder(CROSS_ENCODER_MODEL)

# -----------------------------
# 连接 Milvus
# -----------------------------
_milvus_connected = False

def _ensure_milvus_connected():
    """确保已连接到Milvus"""
    global _milvus_connected
    if not _milvus_connected:
        connections.connect("default", host=MILVUS_HOST, port=MILVUS_PORT)
        _milvus_connected = True

# -----------------------------
# -----------------------------
def create_milvus_collection():
    """
    创建 Milvus Collection 用于存储文章切块向量。
    如果 Collection 已存在，直接返回。
    """
    _ensure_milvus_connected()
    if COLLECTION_NAME in utility.list_collections():
        print(f"Collection '{COLLECTION_NAME}' already exists")
        return Collection(COLLECTION_NAME)

    # if COLLECTION_NAME in utility.list_collections():
    #     print(f"删除旧的 Collection '{COLLECTION_NAME}'")
    #     utility.drop_collection(COLLECTION_NAME)
    
    
    fields = [
        FieldSchema(name="id", dtype=DataType.INT64, is_primary=True, auto_id=True),  # 自增ID
        FieldSchema(name="article_id", dtype=DataType.INT64),
        FieldSchema(name="chunk_id", dtype=DataType.INT64),
        FieldSchema(name="vector", dtype=DataType.FLOAT_VECTOR, dim=384),
        FieldSchema(name="title", dtype=DataType.VARCHAR, max_length=500),
        FieldSchema(name="chunk_text", dtype=DataType.VARCHAR, max_length=1000),
    ]
    schema = CollectionSchema(fields, description="文章切块向量")
    collection = Collection(name=COLLECTION_NAME, schema=schema)
    # 创建索引
    collection.create_index(field_name="vector", index_params={"index_type": "IVF_FLAT", "metric_type": "COSINE", "params": {"nlist": 1024}})
    return collection

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

# -----------------------------
# 切块函数
# -----------------------------
def chunk_text(text, max_len=300, overlap=50):
    chunks = []
    start = 0
    while start < len(text):
        end = min(start + max_len, len(text))
        chunks.append(text[start:end])
        start += max_len - overlap
    return chunks

# -----------------------------
# 数据同步：SQLite -> Milvus
# -----------------------------
def sync_articles_to_milvus(collection: Collection):
    articles = load_articles()
    # print(f"加载 {len(articles)} 条文章")
    # print(articles)
    for article in articles:
        chunks = chunk_text(article['content'])
        vectors = [bi_encoder.encode(chunk).tolist() for chunk in chunks]
        article_id = article["article_id"]
        # 确保 article_id 是整数
        if not isinstance(article_id, int):
            article_id = int(article_id)
        # 构造字段
        entities = [
            {
                "article_id": article_id,
                "chunk_id": i,
                "vector": vectors[i],
                "title": article["title"],
                "chunk_text": chunks[i]
            }
            for i in range(len(chunks))
        ]
        collection.insert(entities)
    # 刷新
    collection.flush()
    print("加载集合到内存...")
    collection.load()

# -----------------------------
# 基于内容的召回
# BI-Encoder 
# Cross-Encoder
# -----------------------------
def content_based_recall(collection: Collection, query, top_k=20, rerank_top_k=100):
    # 两阶段检索：
    # 1. Bi-Encoder 快速召回候选（粗排）
    # 2. Cross-Encoder 精准重排（精排）
    
    # ========== 阶段1：Bi-Encoder 粗排 ==========
    print("阶段1: Bi-Encoder 粗排...")
    q_vec = bi_encoder.encode(query).tolist()
    
    # 从Milvus获取更多候选（因为后面要重排）
    search_res = collection.search(
        data=[q_vec],
        anns_field="vector",
        param={"metric_type": "COSINE", "params": {"nprobe": 10}},
        limit=rerank_top_k,  # 获取更多候选
        expr=None,
        output_fields=["article_id", "chunk_text", "title"]
    )
    
    # 收集候选结果
    candidates = []
    seen_articles = set()
    
    for hits in search_res:
        for hit in hits:
            aid = hit.entity.get("article_id")
            chunk_text = hit.entity.get("chunk_text")
            title = hit.entity.get("title")
            
            # 去重：每个文章只保留一个chunk
            if aid not in seen_articles:
                seen_articles.add(aid)
                candidates.append({
                    "article_id": aid,
                    "title": title,
                    "chunk_text": chunk_text,
                    "bi_encoder_score": hit.score
                })
    
    print(f"Bi-Encoder 召回 {len(candidates)} 个候选")
    
    # ========== 阶段2：Cross-Encoder 精排 ==========
    print("阶段2: Cross-Encoder 精排...")
    
    # 准备Cross-Encoder输入：(query, document) 对
    cross_encoder_inputs = [
        (query, f"{c['title']} {c['chunk_text']}") 
        for c in candidates
    ]
    
    # 批量计算Cross-Encoder分数
    cross_scores = cross_encoder.predict(cross_encoder_inputs)
    
    # 合并分数
    for i, candidate in enumerate(candidates):
        candidate["cross_encoder_score"] = float(cross_scores[i])
        # 可选：加权融合两种分数
        candidate["final_score"] = (
            0.3 * candidate["bi_encoder_score"] + 
            0.7 * candidate["cross_encoder_score"]
        )
    
    # 按Cross-Encoder分数排序
    candidates.sort(key=lambda x: x["final_score"], reverse=True)
    
    # 返回top_k结果
    top_candidates = candidates[:top_k]
    
    # 转换为原来的返回格式
    article_scores = {c["article_id"]: c["final_score"] for c in top_candidates}
    
    print(f"Cross-Encoder 精排完成，返回 top {len(article_scores)} 结果")
    return article_scores, top_candidates

# -----------------------------
# 基于用户的协同过滤
# top_k:函数会返回 得分最高的前 20 个推荐项
# 函数 user_based_cf 使用 behaviors 来：

# 获取目标用户看过的文章：user_articles = set(behaviors.get(user_id, []))
# 遍历其他用户的行为，计算文章重叠度，并累加得分
# behaviors = {
#     "user1": ["article1", "article2", "article3"],
#     "user2": ["article2", "article4"],
#     "user3": ["article1", "article3", "article5"]
# }
# -----------------------------
def user_based_cf(user_id, behaviors, top_k=20):
    user_articles = set(behaviors.get(user_id, []))
    candidate_scores = {}
    for uid, articles in behaviors.items():
        if uid == user_id:
            continue
        overlap = len(user_articles & set(articles))
        for a in articles:
            candidate_scores[a] = candidate_scores.get(a, 0) + overlap
    top_articles = sorted(candidate_scores.items(), key=lambda x: x[1], reverse=True)[:top_k]
    return {a: s for a, s in top_articles}


def hybrid_recommend(collection: Collection, user_id, query, top_k=5, alpha=1.0, beta=1.0):
    """
    改进的混合推荐，使用两阶段检索
    """
    # 1. 内容召回（Bi-Encoder + Cross-Encoder）
    content_scores, detailed_candidates = content_based_recall(
        collection, query, top_k=top_k*2, rerank_top_k=100
    )
    
    # 2. 协同过滤
    behaviors = load_user_behaviors()
    cf_scores = user_based_cf(user_id, behaviors, top_k=top_k*2)
    
    # 3. 加权融合
    combined_scores = {}
    for aid, score in content_scores.items():
        combined_scores[aid] = score * alpha
    for aid, score in cf_scores.items():
        combined_scores[aid] = combined_scores.get(aid, 0) + score * beta
    
    # 4. 排序 top_k
    final_results = sorted(combined_scores.items(), key=lambda x: x[1], reverse=True)[:top_k]
    
    # 获取详细信息
    detailed_results = []
    for aid, score in final_results:
        # 从detailed_candidates中查找详细信息
        detail = next((c for c in detailed_candidates if c["article_id"] == aid), None)
        if detail:
            detailed_results.append({
                "article_id": aid,
                "score": score,
                "title": detail["title"],
                "chunk_text": detail["chunk_text"][:100] + "...",  # 截取部分文本
                "bi_encoder_score": detail["bi_encoder_score"],
                "cross_encoder_score": detail["cross_encoder_score"]
            })
        else:
            detailed_results.append({
                "article_id": aid,
                "score": score,
                "title": "N/A",
                "chunk_text": "N/A",
                "bi_encoder_score": 0,
                "cross_encoder_score": 0
            })
    
    return detailed_results

# -----------------------------
# 主函数演示
# -----------------------------
if __name__ == "__main__":
    collection = create_milvus_collection()
    print("同步文章到 Milvus...")
    sync_articles_to_milvus(collection)
    print("同步完成")
    
    # 加载集合
    collection.load()
    
    user_id = 1
    query = "创作的内容"
    
    print("\n" + "="*50)
    print("开始推荐...")
    results = hybrid_recommend(collection, user_id, query, top_k=5, alpha=1.0, beta=1.0)
    
    print("\n推荐结果:")
    for i, r in enumerate(results, 1):
        print(f"\n{i}. Article ID: {r['article_id']}")
        print(f"   标题: {r['title']}")
        print(f"   综合得分: {r['score']:.4f}")
        print(f"   Bi-Encoder得分: {r['bi_encoder_score']:.4f}")
        print(f"   Cross-Encoder得分: {r['cross_encoder_score']:.4f}")
        print(f"   内容片段: {r['chunk_text']}")
# from pymilvus import connections, utility

# try:
#     connections.connect("default", host="localhost", port="19530")
#     print("✅ Milvus 连接成功！")
#     print(f"现有 Collections: {utility.list_collections()}")
# except Exception as e:
#     print(f"❌ 连接失败: {e}")
