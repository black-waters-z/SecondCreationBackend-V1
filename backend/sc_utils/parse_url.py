# parse image url, return full url
from settings import APP_BASE_URL


def _parse_image_url(article_obj: dict):
    images = []
    if hasattr(article_obj, 'image_urls') and article_obj.image_urls:
        print("has", article_obj.image_urls)
        for image_url in article_obj.image_urls:
            if not image_url.startswith("http"):
                if image_url.endswith(".png") or image_url.endswith(".jpg") or image_url.endswith(".jpeg"):
                    images.append(APP_BASE_URL + '/static/upload_IMG/' + image_url)
                else:
                    images.append(APP_BASE_URL + '/static/upload_Video/' + image_url)
            else:
                images.append(image_url)
    return images


def _parse_list_urls(article_url_list: list):
    images = []
    for image_url in article_url_list:
        if not image_url.startswith("http"):
            if image_url.endswith(".png") or image_url.endswith(".jpg") or image_url.endswith(".jpeg"):
                images.append(APP_BASE_URL + '/static/upload_IMG/' + image_url)
            elif image_url.endswith(".mp4") or image_url.endswith(".avi") or image_url.endswith(
                    ".mkv") or image_url.endswith(".wmv") or image_url.endswith(".flv") or image_url.endswith(
                    ".m3u8") or image_url.endswith(".ts") or image_url.endswith(".m4"):
                images.append(APP_BASE_URL + '/static/upload_Video/' + image_url)
            else:
                images.append(image_url)
        else:
            images.append(image_url)
    return images


def _parse_url(image_url: str):
    if not image_url:
        return image_url
    if not image_url.startswith("http"):
        if image_url.endswith(".png") or image_url.endswith(".jpg") or image_url.endswith(".jpeg"):
            return APP_BASE_URL + '/static/upload_IMG/' + image_url
        elif image_url.endswith(".mp4") or image_url.endswith(".avi") or image_url.endswith(
                ".mkv") or image_url.endswith(".wmv") or image_url.endswith(".flv") or image_url.endswith(
            ".m3u8") or image_url.endswith(".ts") or image_url.endswith(".m4"):
            return APP_BASE_URL + '/static/upload_Video/' + image_url
        else:
            return image_url

    return image_url
