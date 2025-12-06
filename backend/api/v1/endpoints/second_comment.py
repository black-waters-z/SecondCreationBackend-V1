from fastapi import APIRouter, HTTPException, status, Depends
from backend.models import SecondComment
from backend.core import rt
from backend.schemas import SecondCommentIn_Pydantic, SecondComment_Pydantic
from backend.security import get_current_user

second_comment = APIRouter(prefix="/second_comment")


@second_comment.get("/count")
async def get_second_comment_count(first_comment_id: int):
    try:
        result = await SecondComment.filter(post_to_id=first_comment_id).all().count()
        return result
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="查询二级评论失败")


@second_comment.get("")
async def get_second_comment(first_comment_id: int):
    try:
        result = await SecondComment.filter(post_to_id=first_comment_id).all().prefetch_related("poster") \
            .values("id", "content", "poster__name", "poster__avatar", "likes_count", "created_at")
        return result
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="查询二级评论失败")


@second_comment.post("")
async def post_second_comment(first_comment_id: int, second_comment_dict: SecondCommentIn_Pydantic,
                              second_comment_reply_id=None,
                              user: dict = Depends(get_current_user)):
    try:
        result = await SecondComment.create(**second_comment_dict.dict(), post_to_id=first_comment_id,
                                            poster_id=user.get("id"), parent_comment_id=second_comment_reply_id)
        await result.save()
        return {
            "msg": "评论成功",
            "data": result
        }
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="发送二级评论失败")
