import uiautomator2 as u2
# 连接并启动
d = u2.connect_usb()
print(d.info)
print(d.serial)
# print(d.dump_hierarchy())

import random
import time
from bs4 import BeautifulSoup
from bs4 import Tag
from typing import List
import sqlite3

soup = BeautifulSoup(d.dump_hierarchy(), "xml")
nodes = soup.find_all("node", attrs={"class": "android.widget.FrameLayout"})
SQLITE_DB_PATH = r"D:\Project\SecondCreationBackend-V1\scforum.db"

def parse_bounds(bounds: str) -> tuple[int, int, int, int]:
    """解析 bounds 字符串为 (left, top, right, bottom) 元组。"""
    x1, y1, x2, y2 = map(int, bounds.strip("[]").replace("][", ",").split(","))
    return x1, y1, x2, y2

def swiper_up():
    """向上滑动。"""
    width, height = d.window_size()
    sx = width // 2             # 水平方向中点
    sy = height // 2            # 垂直方向中点（起点）
    ey = sy - height // 2       # 向上半屏
    d.swipe(sx, sy, sx, ey, 0.5)  # 0.5秒滑动
    time.sleep(random.uniform(1, 2))

def parse_note() -> dict | None:
    """解析笔记节点。"""
    # 先找到目标节点

    def _parse_note_title_content_author():
        soup = BeautifulSoup(d.dump_hierarchy(), "xml")
        """解析笔记标题、内容和作者。"""
        NOTE_MAP = {
            "author": {
                "resource-id": "com.xingin.xhs:id/nickNameTV",
            },
            "content": {
                "class": "android.widget.TextView",
                "drawing-order": "3",
                "resource-id": "com.xingin.xhs:id/0_resource_name_obfuscated",
            }
        }

        author_text = soup.find(name="node", attrs=NOTE_MAP["author"]).get("text", None)

        content_node = soup.find(
           name= "node",
            attrs= NOTE_MAP["content"],
        )

        if not content_node:
            swiper_up()

            soup = BeautifulSoup(d.dump_hierarchy(), "xml")
            content_node = soup.find(
                "node",
                attrs= NOTE_MAP["content"],
            )

        content_text = content_node.get("text", None)
        title_text = None
        if content_node:
            # 获取上一个兄弟节点
            title_node = content_node.find_previous_sibling("node")
            if title_node:
                title_text = title_node.get("text", None)

        return title_text, content_text, author_text

    def _parse_note_comments():
        """解析笔记评论。"""
        soup = BeautifulSoup(d.dump_hierarchy(), "xml")
        # ,recursive=False 禁止递归查找子元素，也就是只查第一个
        comment_view =soup.find("node",attrs={"class":"androidx.recyclerview.widget.RecyclerView","drawing-order":"2"})

        if not comment_view:
            swiper_up()
            soup = BeautifulSoup(d.dump_hierarchy(), "xml")
            comment_view =soup.find("node",attrs={"class":"androidx.recyclerview.widget.RecyclerView","drawing-order":"2"},recursive=False)

        # print(comment_view)
        comments = comment_view.find_all("node", attrs={"class": "android.widget.LinearLayout"},recursive=False)
        results = []
        for comment in comments:
            items = comment.find_all("node",attrs={"class":"android.widget.TextView"})
            author = None
            content=None

            if items and len(items) >= 3:
                author = items[0].get("text", None)
                content = items[1].get("text", None)
                if content == "作者":
                    content = items[2].get("text", None)

                results.append({
                    "poster": author,
                    "content": content,
                })
        return results

    title_text, content_text, author_text = _parse_note_title_content_author()
    # comments = _parse_note_comments()

    if not title_text and not content_text:
        return None

    return {"title": title_text, "content": content_text, "author": author_text}


def click_note(nodes: List[Tag]):
    for node in nodes:
        if node.get("content-desc") and str(node.get("content-desc")).startswith("笔记"):
            view = node.find("node", attrs={"class": "android.view.View"})
            if not view:
                continue
            left, top, right, bottom = parse_bounds(str(view.get("bounds", None)))
            x = random.randint(left, right)
            y = random.randint(top, bottom)
            d.click(x, y)
            time.sleep(random.uniform(1, 2))
            print(parse_note())
            # next we should parse the comment or go to the next note

            time.sleep(random.uniform(2, 6))
            d.press("back")


while True:
    click_note(nodes)
    swiper_up()
    random.uniform(2, 6)
    swiper_up()
# parse_note()