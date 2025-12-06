from fastapi import APIRouter, WebSocket, WebSocketException, WebSocketDisconnect, HTTPException, status, Depends
from backend.core import rt
from backend.models import PrivateMessage, User
import aioredis
from tortoise.expressions import F, Q
from backend.security import get_current_user

import asyncio

ws = APIRouter()


class PrivateMessageConnection:
    # name1:当前用户,name2聊天用户,websocket：传入的websocket
    def __init__(self, name1, name2, websocket: WebSocket):
        self.user = name1
        self.post_to = name2
        sort_name = sorted([name1, name2])
        # 设置当前订阅的频道
        self.channel = f"private_message:{sort_name[0]}&{sort_name[1]}"
        self.websocket = websocket
        self.running = True
        self.redis_connect = None
        self.pubsub = None

    async def start(self):
        """初始化连接"""
        self.redis_connect = await aioredis.from_url("redis://127.0.0.1")
        self.pubsub = self.redis_connect.pubsub()
        await self.pubsub.subscribe(self.channel)
        await self.websocket.accept()
        await self.websocket.send_text("您已进入聊天室")

    async def get_id(self, name):
        """获取当前两个用户的id"""
        try:
            result = await User.get(name=name)
            return result
        except Exception as e:
            raise

    async def publish_message(self):
        poster_id = await self.get_id(self.user)
        post_to_id = await self.get_id(self.post_to)

        while self.running:
            if not poster_id or not post_to_id:
                break
            try:
                data = await self.websocket.receive_text()
                await self.redis_connect.publish(self.channel, f"{self.user}:{data}")
                # 在这里可以加入数据库插入操作
                print(f"开始插入数据库")
                try:
                    await PrivateMessage.create(message=data, poster=poster_id, post_to=post_to_id)
                except Exception as e:
                    print(f"插入数据库失败{e}")

            except WebSocketException:
                break
            except Exception as e:
                # 前端断开连接时走的这里
                break

        self.running = False

    async def subscribe_message(self):
        try:
            async for message in self.pubsub.listen():
                if not self.running:
                    break
                if message['type'] == 'message' and message['data'].decode().split(":")[0] != self.user:
                    await self.websocket.send_text(message['data'].decode())
        except Exception as e:
            print(f"接收消息错误: {e}")

    async def cleanup(self):
        """清理资源"""
        self.running = False
        try:
            if self.pubsub:
                await self.pubsub.unsubscribe(self.channel)
            if self.redis_connect:
                await self.redis_connect.close()
        except Exception as e:
            print(f"清理资源时发生错误: {e}")

        if self.redis_connect:
            await self.redis_connect.close()


@ws.websocket("/ws/{name}/{send_to_name}")
async def send_private_message(name: str, send_to_name: str, websocket: WebSocket):
    if name == send_to_name:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="不可与自己私聊哦，亲。")
    private_message_connect = PrivateMessageConnection(name, send_to_name, websocket)
    try:
        # 并行运行
        await private_message_connect.start()
        # 创建任务
        publish_task = asyncio.create_task(private_message_connect.publish_message())
        subscribe_task = asyncio.create_task(private_message_connect.subscribe_message())

        # 等待任意一个任务完成或出错
        done, pending = await asyncio.wait(
            [publish_task, subscribe_task],
            return_when=asyncio.FIRST_COMPLETED  # 当第一个任务完成时返回
        )

        # 取消其他还在运行的任务
        for task in pending:
            task.cancel()

        # 等待所有任务结束（包括被取消的）
        if pending:
            await asyncio.wait(pending, timeout=5.0)

    except asyncio.CancelledError:
        # 客户端断开连接，正常处理
        print("WebSocket连接已断开")
        return
    except WebSocketException:
        print("连接已断开")
        await private_message_connect.cleanup()
    except Exception as e:
        print(f"WebSocket错误: {e}")
    finally:
        await private_message_connect.cleanup()


@ws.get("/private_message/{name1}/{name2}")
async def get_private_message(name1, name2):
    result = await PrivateMessage.filter((Q(poster__name=name1) & Q(post_to__name=name2) & Q(poster_delete=False)) |
                                         (Q(poster__name=name2) & Q(post_to__name=name1)) & Q(post_to_delete=False)) \
        .all().order_by("-created_at").limit(30).prefetch_related("poster", "post_to") \
        .values("message", "created_at", "poster__name", "poster__avatar")

    result = list(reversed(result))
    return result


@ws.get("/private_message_to_name")
async def get_private_message_to_name(user=Depends(get_current_user)):
    try:
        result = await PrivateMessage.filter(
            (Q(poster_id=user.get("id")) | Q(post_to_id=user.get("id")))
            & ((Q(post_to_delete=False) & Q(post_to__id=user.get("id")))
               | (Q(poster_delete=False) & Q(poster__id=user.get("id")))
               )).all().distinct().prefetch_related("post_to",
                                                    "poster").values(
            "post_to__name", "poster__name", "post_to__avatar", "poster__avatar")
        room = []
        name = user.get("name")
        for item in result:
            if item["post_to__name"] != user.get("name"):
                data = {
                    "avatar": item["post_to__avatar"],
                    "path": f"{name}/{item['post_to__name']}"
                }
                if data not in room:
                    room.append(data)

            if item["poster__name"] != user.get("name"):
                data = {
                    "avatar": item["poster__avatar"],
                    "path": f"{name}/{item['poster__name']}"
                }
                if data not in room:
                    room.append(data)

        return {
            "user_name": user.get("name"),
            "data": list(room)
        }
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"获取私信对象失败{e}")


@ws.get("/from_name_private_message_path")
def get_from_name_private_message_path(post_to_name: str, user: dict = Depends(get_current_user)):
    try:
        if post_to_name == user.get("name"):
            return {
                "path": False
            }

        return {
            "path": f"{user.get('name')}/{post_to_name}"
        }
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="无法私信")


# 在用户的视角删除私聊
@ws.delete("/private_message")
async def delete_private_message(post_to_name: str, user=Depends(get_current_user)):
    result = await PrivateMessage.filter(post_to_id=user.get("id"), poster__name=post_to_name).all()
    for item in result:
        item.post_to_delete = True
        await item.save()

    result = await PrivateMessage.filter(poster_id=user.get("id"), post_to__name=post_to_name).all()
    for item in result:
        item.poster_delete = True
        await item.save()

    return {
        "msg": "成功删除聊天记录"
    }
