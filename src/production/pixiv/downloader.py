import requests
from typing import Iterable
from concurrent.futures import ThreadPoolExecutor, as_completed

from src.base.model.artwork import ArtworkImage, ArtworkInfo


# Forward declaration
def CreateArtworkInfoFromAPIResponse(data):
    pass


class PixivDownloader:

    def __init__(self, cookie: str = ""):
        self.cookie = cookie

    def _get_images_uri(self, art_id: int):
        return f"https://www.pixiv.net/ajax/illust/{art_id}/pages"

    def _get_info_uri(self, art_id: int):
        return f"https://www.pixiv.net/touch/ajax/illust/details?illust_id={art_id}"

    def _get_headers(self, art_id: str = ""):
        return {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) "
                          "Chrome/90.0.4430.72 Safari/537.36",
            "Referer": f"https://www.pixiv.net/artworks/{art_id}",
            "Cookie": self.cookie,
        }

    def get_artwork_info(self, art_id: int) -> ArtworkInfo:
        uri = self._get_info_uri(art_id)
        headers = self._get_headers(art_id)
        data = requests.get(uri, headers=headers, timeout=5).json()
        return CreateArtworkInfoFromAPIResponse(data)

    def download_images(self, art_id: int) -> Iterable[ArtworkImage]:
        uri_list = self.get_artwork_uris(art_id)
        art_list = []
        with ThreadPoolExecutor(max_workers=4) as executor:
            future_to_uri = {executor.submit(self._download_image, uri): uri for uri in uri_list}
            for future in as_completed(future_to_uri):
                uri = future_to_uri[future]
                data = future.result()
                art_list.append(ArtworkImage(art_id, uri=uri, data=data))
        return art_list

    def _download_image(self, uri: str) -> bytes:
        headers = self._get_headers()
        res = requests.get(uri, headers=headers, timeout=5)
        return res.content

    def get_artwork_uris(self, art_id: int) -> Iterable[str]:
        uri = self._get_images_uri(art_id)
        headers = self._get_headers(art_id)
        res = requests.get(uri, headers=headers)
        data = res.json()
        return tuple(img_info["urls"]["regular"] for img_info in data["body"])


def CreateArtworkInfoFromAPIResponse(data):
    try:
        details = data["body"]["illust_details"]
    except (AttributeError, TypeError):
        return None
    tags = "#" + "#".join(details["tags"]) if details["tags"] and len(details["tags"]) > 0 else ""
    return ArtworkInfo(
        art_id=details["id"],
        title=details["title"],
        tags=tags,
        view_count=details["rating_view"],
        like_count=details["rating_count"],
        love_count=details["bookmark_user_total"],
        author_id=details["user_id"],
        upload_timestamp=details["upload_timestamp"]
    )


