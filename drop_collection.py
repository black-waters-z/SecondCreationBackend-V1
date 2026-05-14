from pymilvus import connections, utility

# 连接Milvus
connections.connect(
    alias="default",
    host="localhost",
    port="19530"
)

# 删除集合
if utility.has_collection("article_embeddings"):
    utility.drop_collection("article_embeddings")
    print("成功删除集合 article_embeddings")
else:
    print("集合 article_embeddings 不存在")

# 断开连接
connections.disconnect("default")