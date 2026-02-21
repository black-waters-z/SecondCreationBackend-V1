# parse image url, return full url
from settings import APP_BASE_URL


def _parse_image_url(article_obj: dict):
    images = []
    if hasattr(article_obj, 'image_urls') and article_obj.image_urls:
        print("has",article_obj.image_urls)
        for image_url in article_obj.image_urls:
            if not image_url.startswith("http"):
                if image_url.endswith(".png") or image_url.endswith(".jpg") or image_url.endswith(".jpeg"):
                    images.append(APP_BASE_URL + '/static/upload_IMG/' + image_url)
                else:
                    images.append(APP_BASE_URL + '/static/upload_Video/' + image_url)
    return images


def _parse_list_urls(article_url_list: list):
    images = []
    for image_url in article_url_list:
        if not image_url.startswith("http"):
            if image_url.endswith(".png") or image_url.endswith(".jpg") or image_url.endswith(".jpeg"):
                images.append(APP_BASE_URL + '/static/upload_IMG/' + image_url)
            else:
                images.append(APP_BASE_URL + '/static/upload_Video/' + image_url)
    return images