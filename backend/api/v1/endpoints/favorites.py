from fastapi import APIRouter, Depends, HTTPException, status
from starlette.responses import JSONResponse
from backend.security import get_current_user
from backend.models import Favorites, Article
from backend.schemas import FavoritesIn_Pydantic, Favorites_Pydantic

# favorites = APIRouter(dependencies=[Depends(get_current_user)], prefix="favorites")
favorites = APIRouter(prefix="/favorites")


# 得到用户的一个收藏夹以及内部收藏的文章
@favorites.get("")
async def get_articles_in_favorites(favorite_id: int, user: dict = Depends(get_current_user)):
    """
    :param favorite_id:收藏夹id，用于点击进入收藏夹后查询
    :param poster_id: 建立收藏夹者的id，用于确认是其创建的文件夹，保证隐私
    :return:
    prefetch_related:预取外键关联的数据
    """
    result = await Favorites.get(id=favorite_id, poster_id=user.get("id"))
    # 预取字段，获取article所对应的poster的名字，
    data = await result.article.all().prefetch_related("poster").values("title", "poster__name", "id","poster__avatar",
                                                                        "likes_count", "favorite_count", "images",
                                                                        "introduction")
    return data


# 得到用户全部的收藏夹以及收藏夹收藏文章的数量
@favorites.get("/get_all_favorites")
async def get_all_favorites(user: dict = Depends(get_current_user)):
    try:
        result = await Favorites.filter(poster_id=user.get("id")).all()
        result_dict = []
        for item in result:
            count = await item.article.all().count()
            data = {
                "id": item.id,
                "name": item.name,
                "description": item.description,
                "count": count
            }
            result_dict.append(data)

        return JSONResponse(status_code=status.HTTP_200_OK, content=result_dict)
    except Exception:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="查询收藏夹失败")


# 建立一个空收藏夹
@favorites.post("/post_just_favorite")
async def post_just_favorites(favorite: FavoritesIn_Pydantic, user: dict = Depends(get_current_user)):
    try:
        await Favorites.create(**favorite.dict(), poster_id=user.get("id"))
        return JSONResponse(status_code=200, content={
            "msg": f"建立{favorite.dict()['name']}收藏夹成功",
            "status": 200
        })
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"建立收藏夹失败{e}")


@favorites.put("/post_article_to_favorites")
async def post_article_to_favorites(favorite_id: int, article_id: int, user: dict = Depends(get_current_user)):
    # 检查收藏夹是否存在且属于当前用户
    favorite_exist = await Favorites.filter(id=favorite_id, poster_id=user.get("id")).exists()
    if not favorite_exist:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="收藏夹不存在或无权访问"
        )

    favorite = await Favorites.get(id=favorite_id, poster_id=user.get("id"))

    # 检查文章是否已存在于文件夹
    article_already_in_favorite = await favorite.article.filter(id=article_id).exists()
    if article_already_in_favorite:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail="文章已在收藏夹内")

    # 检查需要收藏的文章是否存在
    try:
        article = await Article.get(id=article_id)
        article.favorite_count += 1
        await article.save()
    except Exception:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail="文章不存在")

    # 进行添加操作
    await favorite.article.add(article)
    return JSONResponse(status_code=status.HTTP_200_OK, content={
        "msg": "收藏成功",
        "status": 200,
        "favorite_id": favorite_id,
        "article_id": article_id
    })


# 删除整个收藏夹
@favorites.delete("")
async def delete_favorite(favorite_id: int, user=Depends(get_current_user)):
    try:
        result = await Favorites.get(id=favorite_id, poster_id=user.get("id"))
        # 获取所有关联的文章
        articles = await result.article.all()

        # 批量更新所有文章的收藏计数
        for article in articles:
            article.favorite_count -= 1
            await article.save()

        await result.article.clear()
        await result.delete()

        return JSONResponse(status_code=status.HTTP_200_OK,
                            content={
                                "status": "success",
                                "msg": "删除收藏夹成功",
                                "favorite_id": favorite_id
                            })
    except Exception:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="删除收藏夹出错")


@favorites.get("/article_already_in_favorite")
async def get_article_already_in_favorite(article_id: int, user: dict = Depends(get_current_user)):
    article_already_in_favorite = await Favorites.filter(poster_id=user.get("id"), article__id=article_id).exists()
    return article_already_in_favorite


# 删除文件夹中的收藏文件
@favorites.delete("/article_in_favorite")
async def delete_article_in_favorite(article_id: int, user: dict = Depends(get_current_user)):
    try:
        article_in_favorites = await Favorites.filter(poster_id=user.get("id"), article__id=article_id).exists()

        if not article_in_favorites:
            return JSONResponse(status_code=status.HTTP_404_NOT_FOUND,
                                content={
                                    "msg": "文章未在收藏夹内"
                                })

        result = await Favorites.filter(poster_id=user.get("id"), article__id=article_id).first()
        article = await Article.get(id=article_id)
        # 多对多删除操作
        await result.article.remove(article)
        article.favorite_count -= 1
        await article.save()
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "status": "ok",
                "msg": "删除收藏成功",
                "article_id": article_id,
            }
        )
    except Exception:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="取消收藏失败")
