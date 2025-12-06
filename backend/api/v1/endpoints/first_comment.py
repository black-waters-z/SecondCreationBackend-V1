from fastapi import APIRouter, Depends, HTTPException, status
from backend.models import Comment
from backend.schemas import Comment_Pydantic, CommentIn_Pydantic
from backend.security import get_current_user
from tortoise.functions import Count  # 导入 Count
from backend.models import SecondComment
first_comment = APIRouter(prefix="/first_comment")


@first_comment.get("/one_page_comments")
async def get_one_page_comments(article_id: int, page: int):
    result = await Comment.filter(post_to_id=article_id).offset((page - 1) * 10) \
        .annotate(second_comment_count=Count("secondComments"))\
        .limit(10).prefetch_related("poster") \
        .values("id", "poster__name", "poster__avatar", "created_at", "content","second_comment_count")
    return result


@first_comment.post("/comment/{post_to_id}")
async def post_comment(comment: CommentIn_Pydantic, post_to_id: int, poster=Depends(get_current_user)):
    try:
        result = await Comment.create(**comment.dict(), poster_id=poster.get("id"), post_to_id=post_to_id)
        return result
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"评论发表错误")


@first_comment.delete("/comment", status_code=200)
async def delete_comment(comment_id: int, poster=Depends(get_current_user)):
    try:
        result = await Comment.filter(id=comment_id, poster_id=poster.get("id")).first()
        await result.delete()
        return await Comment_Pydantic.from_tortoise_orm(result)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"删除评论错误{e}")


# 查看接收到的评论（文章方面）
@first_comment.get("/comment_to_article")
async def get_comment_to_article(user: dict = Depends(get_current_user)):
    try:
        results = await Comment.filter(post_to__poster_id=user.get("id"), is_read=False).all()
        for result in results:
            result.is_read = True
            await result.save()
        return {
            "msg": "查看成功",
            "data": results
        }
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"获取收到的评论出错,{e}")


# 获取当前用户未读的评论数量
@first_comment.get("/no_read_comment_count")
async def get_no_read_comment(user=Depends(get_current_user)):
    result = await Comment.filter(post_to__poster_id=user.get("id"), is_read=False).all().count()
    return result


# 获取当前用户未读的评论
@first_comment.get("/from_user_id_get_comment")
async def from_user_id_get_comment(user=Depends(get_current_user)):
    result = await Comment.filter(post_to__poster_id=user.get("id")) \
        .order_by("-created_at").limit(50).prefetch_related("poster", "post_to"). \
        values("poster__name", "post_to__title", "poster__avatar", "content", "post_to__id", "poster__id")

    comment = await Comment.filter(post_to__poster_id=user.get("id"), is_read=False).all()
    for item in comment:
        item.is_read = True
        await item.save()

    return result
