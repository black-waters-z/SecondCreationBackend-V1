from fastapi import APIRouter, Depends, HTTPException, status
from backend.models import User
from backend.security import get_current_user

follow = APIRouter(prefix="/follow", dependencies=[Depends(get_current_user)])


# 关注的人
@follow.get("")
async def get_follow(user: dict = Depends(get_current_user)):
    user = await User.get(id=user.get("id"))
    # 获取关注列表
    following_list = await user.following.all()

    # 返回关注用户的基本信息
    result = []
    for follow_user in following_list:
        result.append({
            "id": follow_user.id,
            "name": follow_user.name,
            "avatar": follow_user.avatar,
        })

    return {"following": result}


# 判断有没有被关注
@follow.get("/has_follow/{following_name}")
async def get_has_follow(following_name: str, user: dict = Depends(get_current_user)):
    try:
        user = await User.get(id=user.get("id"))
        result = await user.following.filter(name=following_name).exists()
        return {"exist": result}
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="查看是否关注失败")


@follow.post("/{following_id}")
async def post_follow(following_id: int, user: dict = Depends(get_current_user)):
    try:
        user = await User.get(id=user.get("id"))
        following = await User.get(id=following_id)
        await user.following.add(following)
        return {"msg": "关注成功"}
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="关注失败")


@follow.post("/follow_through_name/{following_name}")
async def post_follow_through_name(following_name: str, user: dict = Depends(get_current_user)):
    try:
        user = await User.get(id=user.get("id"))
        following = await User.get(name=following_name)
        await user.following.add(following)
        return {"msg": "关注成功"}
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="关注失败")


@follow.delete("/{following_id}")
async def delete_following(following_id: int, user: dict = Depends(get_current_user)):
    try:
        user = await User.get(id=user.get("id"))
        following = await User.get(id=following_id)
        await user.following.remove(following)
        return {"msg": "取消关注成功"}
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="取消关注失败")


@follow.delete("/follow_through_name/{following_name}")
async def delete_follow_through_name(following_name: str, user: dict = Depends(get_current_user)):
    try:
        user = await User.get(id=user.get("id"))
        following = await User.get(name=following_name)
        await user.following.remove(following)
        return {"msg": "取消关注成功"}
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="关注失败")
