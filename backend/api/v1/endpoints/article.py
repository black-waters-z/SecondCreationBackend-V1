import random

from fastapi import APIRouter, HTTPException, status, Depends
from fastapi.responses import JSONResponse
from backend.models import Article, Zone, Favorites
from backend.schemas import Article_Pydantic, ArticleIn_Pydantic
from datetime import datetime, timedelta
from backend.security import get_current_user
import os

article = APIRouter(dependencies=[Depends(get_current_user)])


@article.get("/article/search_article")
async def get_article(search_str: str, zone: int = None):
    try:
        if zone:
            articles = await Article.filter(title__icontains=search_str.strip(), zones__id=zone).all() \
                .prefetch_related("poster") \
                .values("id", "title", "introduction", "images", "created_at", "likes_count", "share_count",
                        "favorite_count",
                        "poster_id", "poster__name", "poster__avatar")
            return articles
        else:
            articles = await Article.filter(title__icontains=search_str.strip()).all() \
                .prefetch_related("poster") \
                .values("id", "title", "introduction", "images", "created_at", "likes_count", "share_count",
                        "favorite_count",
                        "poster_id", "poster__name", "poster__avatar")
            return articles

    except Exception:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="查询失败")


@article.post("/article")
async def post_article(content: ArticleIn_Pydantic, zone_name: str, poster=Depends(get_current_user)):
    try:
        article_content = await Article.create(**content.dict(exclude_unset=True), poster_id=poster.get("id"))
        choose_zone = await Zone.get(name=zone_name)
        await article_content.zones.add(choose_zone)
        return await Article_Pydantic.from_tortoise_orm(article_content)
    except Exception:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="发布失败！请登录重试。")


@article.put("/article")
async def put_article(content: ArticleIn_Pydantic,
                      poster_id: int, zone_name: str, id: int):
    """
    :param id: 从上一步获取到的要更新文章的id值
    :return:
    """
    try:
        await Article.filter(id=id).update(**content.dict(), poster_id=poster_id)
        article_content = await Article.get(id=id)
        await article_content.zones.clear()  # 清除之前的关系
        choose_zones = await Zone.get(name=zone_name)
        await article_content.zones.add(choose_zones)
        return {
            "status": status.HTTP_200_OK,
            "msg": "更新成功"
        }
    except Exception:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="更新出错，请登录重试")


@article.delete("/article")
async def delete_article(article_id: int, poster=Depends(get_current_user)):
    """
    :param article_id:文章id
    :param poster_id:用户id
    :return:
    """
    try:
        # 我们需要从localstorage中提取的poster_id来获取删除文章的作者是不是处于登录状态
        # 并且判断是不是该作者
        result = await Article.filter(id=article_id, poster_id=poster.get("id")).first()

        if result.images.get("additionalProp1"):
            # 删除文章中可能存在的图片
            for item in result.images.get("additionalProp1"):
                image_path = result.images.get("additionalProp1")[item]
                file_path = f'backend/static/uploadimg/{image_path}'
                if os.path.exists(file_path):
                    os.remove(file_path)

        await result.delete()
        return {"status": "ok", "msg": "删除文章成功"}
    except Exception:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="发布失败！请登录重试。")


@article.get("/get_newest_article")
async def get_newest_article():
    try:
        latest_article = await Article.all().prefetch_related("poster").all().order_by("-created_at").limit(30) \
            .values("id", "title", "introduction", "images", "created_at", "likes_count", "share_count",
                    "favorite_count",
                    "poster_id", "poster__name", "poster__avatar")

        for key, article in enumerate(latest_article):
            article["created_at"] = article["created_at"].date()
            result = await Article.filter(id=article["id"]).first()
            article_zone = await result.zones.all().values("id", "name")
            article["zone"] = article_zone

        return latest_article  # 它期望的是一个 QuerySet 对象（未执行的查询）。
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"查询出错！{e}")


@article.get("/fromIdGetArticle")
async def get_article(id: int, user=Depends(get_current_user)):
    """
    :param id:文章id
    :param user:
    :return:
    """
    try:
        articles = await Article.get(id=id).prefetch_related("poster").values(
            "id", "title", "content", "images", "created_at", "likes_count", "share_count", "favorite_count",
            "introduction",
            "poster__name", "poster__avatar", "poster__id")
        can_delete = articles.get("poster__name") == user.get("name")
        # 查询当前用户是否已经收藏此文章
        has_favorite = await Favorites.filter(poster_id=user.get("id"), article__id=id).exists()
        result = articles
        if not has_favorite:
            data = {
                "articles": result,
                "favorite": False,
                "like": False,
                "can_delete": can_delete,
            }
        else:
            data = {
                "articles": result,
                "favorite": True,
                "like": False,
                "can_delete": can_delete,
            }
        return data
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"查询失败{e}")


@article.get("/article/fromPosterIdGetArticle")
async def get_poster_id_article(user: dict = Depends(get_current_user)):
    try:
        articles = await Article.filter(poster_id=user.get("id")).all().order_by("-created_at").prefetch_related(
            "poster").values(
            "id", "title", "images", "created_at", "likes_count", "share_count", "favorite_count",
            "introduction",
            "poster__name", "poster__avatar")

        print(">>>", articles)
        for key, article in enumerate(articles):
            # 将时间进行处理
            article["created_at"] = article["created_at"].date()
            # 查询区域
            result = await Article.filter(id=article["id"]).first()
            article_zone = await result.zones.all().values("id", "name")
            articles[key]["zone"] = article_zone

        return articles
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"查询失败{e}")


@article.get("/article/todayHotArticle")
async def get_today_hot_article():
    try:
        today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        today_end = today_start + timedelta(days=1)
        articles = await Article.filter(
            created_at__gte=today_start,
            created_at__lt=today_end
        ).all().prefetch_related("poster").all().order_by("-likes_count").limit(10) \
            .values("id", "title", "introduction", "images", "created_at", "likes_count", "share_count",
                    "favorite_count",
                    "poster_id", "poster__name", "poster__avatar")

        for key, article in enumerate(articles):
            article["created_at"] = article["created_at"].date()
            result = await Article.filter(id=article["id"]).first()
            article_zone = await result.zones.all().values("id", "name")
            article["zone"] = article_zone

        return articles
    except Exception:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="今日热门查询失败")


@article.get("/article/monthHotArticle")
async def get_month_hot_article():
    try:
        # 获取本月开始和结束的日期时间
        now = datetime.now()
        month_start = datetime(now.year, now.month, 1)  # 本月第一天
        next_month = month_start.replace(day=28) + timedelta(days=4)  # 确保进入下个月
        month_end = datetime(next_month.year, next_month.month, 1)  # 下个月第一天

        articles = await Article.filter(
            created_at__gte=month_start,
            created_at__lt=month_end
        ).all().prefetch_related("poster").all().order_by("-likes_count").limit(10) \
            .values("id", "title", "introduction", "images", "created_at", "likes_count", "share_count",
                    "favorite_count",
                    "poster_id", "poster__name", "poster__avatar")

        for key, article in enumerate(articles):
            article["created_at"] = article["created_at"].date()
            result = await Article.filter(id=article["id"]).first()
            article_zone = await result.zones.all().values("id", "name")
            article["zone"] = article_zone

        return articles
    except Exception:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="今日热门查询失败")


@article.get("/article/fromPosterNameGetArticle")
async def fromPosterNameGetArticle(name: str):
    articles = await Article.filter(poster__name=name).all().prefetch_related("poster").values(
        "id", "title", "introduction", "images", "created_at", "likes_count", "share_count",
        "favorite_count",
        "poster_id", "poster__name", "poster__avatar"
    )

    for key, article in enumerate(articles):
        article["created_at"] = article["created_at"].date()
        result = await Article.filter(id=article["id"]).first()
        article_zone = await result.zones.all().values("id", "name")
        article["zone"] = article_zone

    return articles


@article.get("/article/fromZoneGetNewestArticle")
async def from_zone_get_newest_article(zone_id: int):
    try:
        articles = await Article.filter(zones__id=zone_id).all().order_by("-created_at").values(
            "id", "title", "introduction", "images", "created_at", "likes_count", "share_count",
            "favorite_count",
            "poster_id", "poster__name", "poster__avatar"
        )

        for key, article in enumerate(articles):
            article["created_at"] = article["created_at"].date()
            result = await Article.filter(id=article["id"]).first()
            article_zone = await result.zones.all().values("id", "name")
            article["zone"] = article_zone

        return articles
    except Exception:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="获取文章失败")


@article.get("/article/fromZoneGetHotestArticle")
async def from_zone_get_hotest_article(zone_id: int, page: int):
    try:
        articles = await Article.filter(zones__id=zone_id).all()[:page * 10].order_by("-likes_count").values(
            "id", "title", "introduction", "images", "created_at", "likes_count", "share_count",
            "favorite_count",
            "poster_id", "poster__name", "poster__avatar"
        )

        for key, article in enumerate(articles):
            article["created_at"] = article["created_at"].date()
            result = await Article.filter(id=article["id"]).first()
            article_zone = await result.zones.all().values("id", "name")
            article["zone"] = article_zone

        return articles
    except Exception:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="获取文章失败")


@article.get("/article/fromZoneGetRecommendArticle")
async def from_zone_get_hotest_article(zone_id: int, limit=10):
    try:
        articles = await Article.filter(zones__id=zone_id).all().values(
            "id", "title", "introduction", "images", "created_at", "likes_count", "share_count",
            "favorite_count",
            "poster_id", "poster__name", "poster__avatar"
        )

        # 随机打乱列表顺序
        random.shuffle(articles)

        # 取前 limit 条
        articles = articles[:limit]

        for key, article in enumerate(articles):
            article["created_at"] = article["created_at"].date()
            result = await Article.filter(id=article["id"]).first()
            article_zone = await result.zones.all().values("id", "name")
            article["zone"] = article_zone

        return articles
    except Exception:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="获取文章失败")


@article.get("/article/filter_by_date/{zone_id}/{year}/{month}")
async def get_article_filter_by_date(zone_id: int, year: int, month: int):
    try:
        articles = await Article.filter(zones__id=zone_id, created_at__year=year, created_at__month=month).all().values(
            "id", "title", "introduction", "images", "created_at", "likes_count", "share_count",
            "favorite_count",
            "poster_id", "poster__name", "poster__avatar"
        )
        for key, article in enumerate(articles):
            article["created_at"] = article["created_at"].date()
            result = await Article.filter(id=article["id"]).first()
            article_zone = await result.zones.all().values("id", "name")
            article["zone"] = article_zone

        return articles
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="筛选文章失败")
