import json
import pandas as pd
from tortoise import Tortoise, run_async
from datetime import datetime
from decimal import Decimal

# 从现成的models文件夹导入模型
from backend.models import User, Article

# ====================== 导入函数 ======================
async def import_csv_to_db(csv_path: str, db_url: str):
    # 初始化 Tortoise ORM
    await Tortoise.init(
        db_url=db_url,
        modules={"models": ["backend.models"]}  # 使用现成的models模块
    )
    # 生成表结构（如果表不存在，已有表则不会覆盖）
    await Tortoise.generate_schemas()

    # 读取 CSV 文件
    df = pd.read_csv(csv_path, encoding="utf-8-sig", header=None)
    # 手动指定列名（根据爬虫输出的 CSV 列顺序）
    df.columns = ["title", "content", "author", "likes_count", "favorites_count", "comments_count", "img_path"]

    # 批量处理数据
    for idx, row in df.iterrows():
        try:
            # 处理空值
            title = row["title"] if pd.notna(row["title"]) else "无标题"
            content = row["content"] if pd.notna(row["content"]) else ""
            author_name = row["author"] if pd.notna(row["author"]) else "未知作者"
            like_count = int(row["likes_count"]) if pd.notna(row["likes_count"]) else 0
            favorite_count = int(row["favorites_count"]) if pd.notna(row["favorites_count"]) else 0
            img_path = row["img_path"] if pd.notna(row["img_path"]) else None

            # 1. 查找/创建用户（email必填，使用占位符邮箱）
            user, created = await User.get_or_create(
                username=author_name,
                defaults={
                    "password_hash": "default_hash_123456",  # 需后续修改
                    "email": f"{author_name}@example.com",  # 使用占位符邮箱
                    "is_active": True
                }
            )
            if created:
                print(f"创建新用户: {author_name}")

            # 2. 处理图片 URL（JSON 格式）
            image_urls = None
            if img_path:
                # 假设图片路径需要拼接成完整 URL，根据实际情况调整
                full_img_url = f"shturl.cc/{img_path}"
                image_urls = json.dumps([full_img_url])  # 转为 JSON 字符串

            # 3. 创建文章
            article = await Article.create(
                title=title,
                subtitle=None,  # CSV 中无副标题，设为 null
                content=content,
                image_urls=image_urls,
                view_count=0,  # CSV 中无浏览量，设为 0
                like_count=like_count,
                favorite_count=favorite_count,
                reward_amount=Decimal("0"),  # CSV 中无打赏金额，设为 0
                status="published",
                published_at=datetime.now(),  # 发布时间设为当前时间
                author_id=user.id
            )
            print(f"成功导入文章: {title} (作者: {author_name})")

        except Exception as e:
            print(f"处理第 {idx} 行数据失败: {e}")
            continue

    # 关闭连接
    await Tortoise.close_connections()


# ====================== 执行导入 ======================
if __name__ == "__main__":
    # 配置参数
    CSV_FILE_PATH = r"D:\Project\SecondCreationBackend-V1\xiaohongshu_notes.csv"
    # 替换为你的数据库连接 URL（SQLite 示例，其他数据库需调整）
    DB_URL = "sqlite://D:/Project/SecondCreationBackend-V1/scforum.db"

    # 运行异步任务
    run_async(import_csv_to_db(CSV_FILE_PATH, DB_URL))