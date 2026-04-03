import time
import requests
import json
import httpx
from typing import List, Dict, Optional
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from sse_starlette.sse import EventSourceResponse
from typing import Annotated, AsyncGenerator
from backend.sc_utils import _extract_user_id_from_token
from backend.security.password_security import oauth2_scheme
from settings import AI_TOKEN

ai = APIRouter()

# 简单的内存存储（生产环境建议使用 Redis 或数据库）
conversation_store: Dict[str, List[Dict]] = {}


class ChatMessage(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    session_id: Optional[str] = None  # 用于标识用户会话
    message: str
    model: Optional[str] = "4.0Ultra"
    max_tokens: Optional[int] = 32768
    temperature: Optional[float] = 1.2
    top_k: Optional[int] = 6


@ai.post("/chat")
async def chat_with_context(token: Annotated[str, Depends(oauth2_scheme)], request: ChatRequest):
    """
    支持上下文的 AI 对话接口
    session_id: 用于区分不同用户的会话
    message: 用户当前的问题
    """
    user_id = _extract_user_id_from_token(token)
    request.session_id = str(user_id)
    url = "https://spark-api-open.xf-yun.com/v1/chat/completions"

    # 获取或创建会话历史
    if request.session_id not in conversation_store:
        conversation_store[request.session_id] = [
            {
                "role": "system",
                "content": "你是一个有用的 AI 助手。"
            }
        ]

    # 添加用户的新消息到历史记录
    conversation_store[request.session_id].append({
        "role": "user",
        "content": request.message
    })

    # 构建请求数据（包含完整的对话历史）
    data = {
        "max_tokens": request.max_tokens,
        "top_k": request.top_k,
        "temperature": request.temperature,
        "messages": conversation_store[request.session_id],
        "model": request.model,
        "tools": [
            {
                "web_search": {
                    "search_mode": "normal",
                    "enable": False
                },
                "type": "web_search"
            }
        ],
        "stream": False  # 接口模式建议关闭流式
    }

    header = {
        "Authorization": "Bearer jshoFKSRcnSAhXjJOmIU:ozKndSjiatvoMNmTnsTh"
    }

    try:
        response = requests.post(url, headers=header, json=data)
        response.raise_for_status()
        result = response.json()

        # 获取 AI 回复
        ai_content = result.get('choices', [{}])[0].get('message', {}).get('content', '')

        # 将 AI 回复也添加到历史记录中
        conversation_store[request.session_id].append({
            "role": "assistant",
            "content": ai_content
        })

        # 限制历史长度，避免 token 超限（可选）
        if len(conversation_store[request.session_id]) > 20:  # 保留最近 10 轮对话
            # 保留 system 消息和最近的 19 条消息
            conversation_store[request.session_id] = [
                                                         conversation_store[request.session_id][0]
                                                     ] + conversation_store[request.session_id][-19:]

        return {
            "session_id": request.session_id,
            "message": ai_content,
            "history_count": len(conversation_store[request.session_id])
        }

    except requests.exceptions.RequestException as e:
        raise HTTPException(
            status_code=500,
            detail=f"AI 服务请求失败：{str(e)}"
        )


@ai.get("/chat-stream")
async def chat_with_context(message: str,user_id:str):
    """
    支持上下文的 AI 对话接口（SSE 流式返回）
    session_id: 用于区分不同用户的会话
    message: 用户当前的问题
    """
    request = ChatRequest(
        session_id= None,
        message=message,
        max_tokens =32768,
        temperature= 1.2,
        top_k=6,
        model="4.0Ultra"
    )
    request.session_id = str(user_id)
    url = "https://spark-api-open.xf-yun.com/v1/chat/completions"

    # 获取或创建会话历史
    if request.session_id not in conversation_store:
        conversation_store[request.session_id] = [
            {
                "role": "system",
                "content": "你是一个有用的 AI 助手。"
            }
        ]

    # 添加用户的新消息到历史记录
    conversation_store[request.session_id].append({
        "role": "user",
        "content": request.message
    })

    # 构建请求数据（包含完整的对话历史）
    data = {
        "max_tokens": request.max_tokens,
        "top_k": request.top_k,
        "temperature": request.temperature,
        "messages": conversation_store[request.session_id],
        "model": request.model,
        "tools": [
            {
                "web_search": {
                    "search_mode": "normal",
                    "enable": False
                },
                "type": "web_search"
            }
        ],
        "stream": True  # 启用流式模式
    }

    header = {
        "Authorization": f"Bearer {AI_TOKEN}"
    }

    # SSE 事件生成器
    async def generate_sse_events() -> AsyncGenerator[str, None]:
        full_response = ""

        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                async with client.stream(
                        "POST",
                        url,
                        headers=header,
                        json=data
                ) as response:
                    response.raise_for_status()

                    async for line in response.aiter_lines():
                        try:
                            if line.startswith("data: "):
                                json_str = line[6:]  # 去掉 "data: "
                                if json_str.strip() == "[DONE]":
                                    break

                                json_data = json.loads(json_str)
                                content = (json_data.get('choices', [{}])[0]
                                           .get('delta', {})
                                           .get('content', ''))

                                if content:
                                    full_response += content
                                    # 发送每个 token 作为 SSE 事件
                                    yield {
                                        "event": "message",
                                        "data": json.dumps({
                                            "content": content,
                                            "type": "chunk"
                                        }, ensure_ascii=False)
                                    }
                        except json.JSONDecodeError:
                            continue

                    # 将完整回复添加到历史记录
                    conversation_store[request.session_id].append({
                        "role": "assistant",
                        "content": full_response
                    })

                    # 限制历史长度
                    if len(conversation_store[request.session_id]) > 20:
                        conversation_store[request.session_id] = [
                                                                     conversation_store[request.session_id][0]
                                                                 ] + conversation_store[request.session_id][-19:]

                    # 发送结束事件
                    yield {
                        "event": "message",
                        "data": json.dumps({
                            "session_id": request.session_id,
                            "message": full_response,
                            "history_count": len(conversation_store[request.session_id]),
                            "type": "complete"
                        }, ensure_ascii=False)
                    }

        except Exception as e:
            yield {
                "event": "error",
                "data": json.dumps({
                    "error": f"AI 服务请求失败：{str(e)}"
                })
            }
        finally:
            # 确保无论如何都会保存历史记录（即使客户端断开连接）
            if full_response:
                # 将完整回复添加到历史记录
                conversation_store[request.session_id].append({
                    "role": "assistant",
                    "content": full_response
                })

                # 限制历史长度
                if len(conversation_store[request.session_id]) > 20:
                    conversation_store[request.session_id] = [
                                                                 conversation_store[request.session_id][0]
                                                             ] + conversation_store[request.session_id][-19:]

    return EventSourceResponse(generate_sse_events(), media_type="text/event-stream")


@ai.get("/conversation/{session_id}")
async def get_conversation_history(session_id: str):
    """获取指定会话的完整对话历史"""
    if session_id not in conversation_store:
        raise HTTPException(status_code=404, detail="会话不存在")

    return {
        "session_id": session_id,
        "history": conversation_store[session_id]
    }


@ai.delete("/conversation/{session_id}")
async def clear_conversation(session_id: str):
    """清空指定会话的对话历史"""
    if session_id in conversation_store:
        del conversation_store[session_id]

    return {"message": "会话已清空"}

