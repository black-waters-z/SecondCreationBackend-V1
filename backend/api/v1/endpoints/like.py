from fastapi import APIRouter, Depends, status, HTTPException
from starlette.responses import JSONResponse

from backend.security import get_current_user
from backend.models import Like, Article

like = APIRouter(dependencies=[Depends(get_current_user)])


# 判断用户有没有like
@like.get("/like")
async def get_is_like(article_id, user=Depends(get_current_user)):
    result = await Like.filter(article_id=article_id, user_id=user.get("id"), is_active=True).exists()
    if not result:
        return JSONResponse(status_code=status.HTTP_200_OK,
                            content={
                                "status": "ok",
                                "data": {
                                    "is_active": False,
                                    "article_id": article_id,
                                }
                            })

    return JSONResponse(status_code=status.HTTP_200_OK,
                        content={
                            "status": "ok",
                            "data": {
                                "is_active": True,
                                "article_id": article_id,
                            }
                        })


@like.post("/like")
async def post_like(article_id: int, user=Depends(get_current_user)):
    """
    当用户点赞文章的时候，朝like数据库插入数据，前端传入id即可，前端通过判断
    :param article_id:
    :param user:
    :return:
    """
    try:
        have_like = await Like.filter(article_id=article_id,
                                      user_id=user.get("id"), is_active=True).exists()
        if have_like:
            return []

        article = await Article.get(id=article_id)
        article.likes_count += 1
        await article.save()
        result, created = await Like.update_or_create(
            article_id=article_id,
            user_id=user.get("id"),
            defaults={"is_active": True}  # 更新或创建时设置的值
        )
        return result
    except Exception:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST)


@like.delete("/like")
async def delete_like(article_id: int, user=Depends(get_current_user)):
    try:
        result = await Like.get(article_id=article_id, user_id=user.get("id"))
        result.is_active = False
        await result.save()
        article = await Article.get(id=article_id)
        article.likes_count -= 1
        await article.save()
        return JSONResponse(status_code=status.HTTP_200_OK,
                            content={
                                "msg": "取消点赞成功",
                                "data": {
                                    "article_id": article_id,
                                    "user_id": user.get("id"),
                                }
                            })
    except Exception:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="取消点赞失败")
