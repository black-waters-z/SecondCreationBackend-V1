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
import pandas as pd

SQLITE_DB_PATH = r"D:\Project\SecondCreationBackend-V1\scforum.db"

def save_to_csv(all_notes: List[dict]):
    """将所有笔记保存到 CSV 文件。"""
    if not all_notes:
        print("没有数据")
        return

    try:
        df = pd.DataFrame(all_notes)
        df.to_csv(
            "xiaohongshu_notes.csv",
            index=False,
            encoding="utf-8-sig",
            mode="a",
            header=False,
        )
        print("CSV 导出成功")
    except Exception as e:
        print(f"CSV 导出失败: {e}")

def parse_bounds(bounds: str) -> tuple[int, int, int, int]:
    """解析 bounds 字符串为 (left, top, right, bottom) 元组。"""
    try:
        x1, y1, x2, y2 = map(int, bounds.strip("[]").replace("][", ",").split(","))
        return x1, y1, x2, y2
    except (ValueError, AttributeError) as e:
        print(f"解析 bounds 失败: {e}")
        return (0, 0, 0, 0)

def swiper_up():
    """向上滑动。"""
    try:
        width, height = d.window_size()
        sx = width // 2             # 水平方向中点
        sy = height // 2            # 垂直方向中点（起点）
        ey = sy - height // 2       # 向上半屏
        d.swipe(sx, sy, sx, ey, 0.5)  # 0.5秒滑动
        time.sleep(random.uniform(1, 2))
    except Exception as e:
        print(f"向上滑动失败: {e}")

import re
from bs4 import BeautifulSoup


def parse_count(text: str):
    """
    解析:
    收藏 123
    收藏 1.2万
    """
    try:
        if not text:
            return 0

        match = re.search(r'([\d.]+)(万?)', text)

        if not match:
            return 0

        num = float(match.group(1))

        if match.group(2) == '万':
            num *= 10000

        return int(num)
    except (ValueError, AttributeError) as e:
        print(f"解析数量失败: {e}")
        return 0


def download_note_img():
    img_node = d.xpath('//*[starts-with(@content-desc, "图片")]')

    if img_node.exists:
        coords = img_node.bounds  # 使用 coords 而不是 bounds
        x1, y1, x2, y2 = coords

        # 3. 截图并裁剪
        full_img = d.screenshot()  # 获取全屏截图（PIL.Image）
        cropped_img = full_img.crop((x1, y1, x2, y2))  # 裁剪
        timestamp = int(time.time() * 1000)
        cropped_img.save(f"D:/image/rednote_image_{timestamp}.jpg")  # 保存
        print(f"图片已保存为: D:/image/rednote_image_{timestamp}.jpg")
        return f"rednote_image_{timestamp}.jpg"
    else:
        print("未找到图片")
        return None


def _parse_likes_favorites_comments_count():
    """解析笔记点赞、收藏、评论数"""

    soup = BeautifulSoup(d.dump_hierarchy(), "xml")

    # 收藏
    favorites_elem = d.xpath(
        '//*[starts-with(@content-desc,"收藏")]'
    ).get()

    favorites_text = (
        favorites_elem.attrib.get("content-desc", "")
        if favorites_elem else ""
    )

    favorites_count = parse_count(favorites_text)

    # 点赞
    likes_elem = d.xpath(
        '//*[starts-with(@content-desc,"点赞")]'
    ).get()

    likes_text = (
        likes_elem.attrib.get("content-desc", "")
        if likes_elem else ""
    )

    likes_count = parse_count(likes_text)

    # 评论
    comments_elem = d.xpath(
            '//android.widget.Button[starts-with(@content-desc,"评论")]'
    ).get()

    comments_text = (
        comments_elem.attrib.get("content-desc", "")
        if comments_elem else ""
    )
    comments_count = parse_count(comments_text)

    return {
        "likes_count": likes_count,
        "favorites_count": favorites_count,
        "comments_count": comments_count
    }
def _parse_note_title_content_author():
    try:
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

        author_node = soup.find("node", attrs=NOTE_MAP.get("author"))
        author_text = author_node.get("text", None)

        content_node = soup.find(
            "node",
            attrs= NOTE_MAP.get("content"),
        )

        if not content_node:
            swiper_up()

            soup = BeautifulSoup(d.dump_hierarchy(), "xml")
            content_node = soup.find(
                "node",
                attrs= NOTE_MAP.get("content"),
            )

        content_text = content_node.get("text", None)
        title_text = None
        if content_node:
            # 获取上一个兄弟节点
            title_node = content_node.find_previous_sibling("node")
            if title_node:
                title_text = title_node.get("text", None)

        return title_text, content_text, author_text
    except Exception as e:
        print(f"解析笔记标题、内容和作者失败: {e}")
        return None, None, None

def _parse_note_comments():
    """解析笔记评论。"""
    soup = BeautifulSoup(d.dump_hierarchy(), "xml")
    # ,recursive=False 禁止递归查找子元素，也就是只查第一个
    comment_view =soup.find("node",attrs={"class":"androidx.recyclerview.widget.RecyclerView","drawing-order":"2"})

    if not comment_view:
        swiper_up()
        soup = BeautifulSoup(d.dump_hierarchy(), "xml")
        comment_view =soup.find("node",attrs={"class":"androidx.recyclerview.widget.RecyclerView","drawing-order":"2"})

    # print(comment_view)
    comments = comment_view.find_all("node", attrs={"class": "android.widget.LinearLayout"})
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

def parse_note() -> dict | None:
    """解析笔记节点。"""
    # 先找到目标节点
    title_text, content_text, author_text = _parse_note_title_content_author()
    if not title_text and not content_text and not author_text:
        return None
    # comments = _parse_note_comments()
    # img_path = download_note_img()
    img_path = None
    if not title_text and not content_text:
        return None

    return {"title": title_text, "content": content_text, "author": author_text, **_parse_likes_favorites_comments_count(), "img_path": img_path}


def click_note(nodes: List[Tag]):
    """点击笔记节点。"""
    all_notes = []
    for node in nodes:
        try:
            if node.get("content-desc"):
                desc = str(node.get("content-desc", ""))
                # 只保留图文笔记
                if not desc.startswith("笔记"):
                    continue

                # 跳过视频
                if "视频" in desc:
                    continue

                print(desc)

                view = node.find("node", attrs={"class": "android.view.View"})
                if not view:
                    continue
                left, top, right, bottom = parse_bounds(str(view.get("bounds", None)))
                x = random.randint(left, right)
                y = random.randint(top, bottom)
                d.click(x, y)
                time.sleep(random.uniform(1, 2))
                # next we should parse the comment or go to the next note
                note = parse_note()
                if note:
                    all_notes.append(note)

                time.sleep(random.uniform(2, 6))
                d.press("back")
            else:
                continue
        except Exception as e:
            print(f"处理笔记节点时出错: {e}")
            d.press("back")
            continue

    print(f"{len(all_notes)} 条笔记被保存")
    save_to_csv(all_notes)



while True:
    soup = BeautifulSoup(
        d.dump_hierarchy(),
        "xml"
    )
    recycle_node = soup.find("node", attrs={"class": "androidx.recyclerview.widget.RecyclerView","bounds":"[0,429][1268,2457]"})
    if not recycle_node:
        raise Exception("未找到RecyclerView节点")

    nodes = recycle_node.find_all(
        "node",
        attrs={"class": "android.widget.FrameLayout"},
        recursive=False
    )
    click_note(nodes)
    swiper_up()
    random.uniform(2, 6)
    swiper_up()
# parse_note()