import logging
from typing import Any, Dict, List, Optional

from tortoise.expressions import Q

from backend.models import (
    Article,
    ArticleRecommendation,
    ArticleRewardRanking,
    Tag,
)
from backend.schemas.article import (
    ArticleCreate,
    ArticleRecommendationCreate,
    ArticleRecommendationUpdate,
    ArticleRewardRankingCreate,
    ArticleRewardRankingUpdate,
    ArticleUpdate,
    ArticleShow
)

from .base import ApiController


class ArticleController(ApiController[Article, ArticleCreate, ArticleUpdate]):
    def __init__(self) -> None:
        super().__init__(Article)

    async def create(self, obj_in: ArticleCreate | Dict[str, Any]) -> Article:
        if isinstance(obj_in, dict):
            tag_ids = obj_in.get("tag_ids")
            data = {
                k: v
                for k, v in obj_in.items()
                if k not in {"tag_ids", "collection"}
            }
        else:
            tag_ids = obj_in.tag_ids
            data = obj_in.model_dump(
                exclude={"tag_ids", "collection"},
                exclude_none=True,
            )

        article = await super().create(data)
        if tag_ids:
            tags = await self._get_tags_by_ids(tag_ids)
            await article.tags.add(*tags)
        return await self._load_tags(article)

    async def update(
        self,
        id: int,
        obj_in: ArticleUpdate | Dict[str, Any],
    ) -> Article:
        if isinstance(obj_in, dict):
            tags_supplied = "tag_ids" in obj_in
            tag_ids = obj_in.get("tag_ids")
            data = {k: v for k, v in obj_in.items() if k != "tag_ids"}
        else:
            tags_supplied = "tag_ids" in obj_in.model_fields_set
            tag_ids = obj_in.tag_ids
            data = obj_in.model_dump(exclude={"tag_ids"}, exclude_unset=True)

        article = await super().update(id=id, obj_in=data)
        if tags_supplied:
            await article.tags.clear()
            if tag_ids:
                tags = await self._get_tags_by_ids(tag_ids)
                await article.tags.add(*tags)
        return await self._load_tags(article)

    async def get_item(self, id: int) -> Article:
        article = await super().get_item(id)
        return await self._load_tags(article)

    async def list_items(
        self,
        page: int,
        page_size: int,
        search=Q(),
        order: Optional[List[str]] = None,
    ):
        total, records = await super().list_items(page, page_size, search, order)
        await self._prefetch_tags(records)
        return total, records

    async def _prefetch_tags(self, articles: List[Article]) -> None:
        for article in articles:
            await article.fetch_related("tags")

    @staticmethod
    async def _load_tags(article: Article) -> Article:
        await article.fetch_related("tags")
        return article

    async def _get_tags_by_ids(self, tag_ids: List[int]) -> List[Tag]:
        unique_ids: List[int] = []
        seen = set()
        for tag_id in tag_ids:
            if tag_id not in seen:
                seen.add(tag_id)
                unique_ids.append(tag_id)
        if not unique_ids:
            return []
        tags = await Tag.filter(id__in=unique_ids)
        tag_map = {tag.id: tag for tag in tags}
        missing = [tag_id for tag_id in unique_ids if tag_id not in tag_map]
        if missing:
            raise ValueError(f"标签ID不存在: {missing}")
        return [tag_map[tag_id] for tag_id in unique_ids]


class ArticleRewardRankingController(
    ApiController[
        ArticleRewardRanking,
        ArticleRewardRankingCreate,
        ArticleRewardRankingUpdate,
    ]
):
    def __init__(self) -> None:
        super().__init__(ArticleRewardRanking)


class ArticleRecommendationController(
    ApiController[
        ArticleRecommendation,
        ArticleRecommendationCreate,
        ArticleRecommendationUpdate,
    ]
):
    def __init__(self) -> None:
        super().__init__(ArticleRecommendation)


article_controller = ArticleController()
article_reward_ranking_controller = ArticleRewardRankingController()
article_recommendation_controller = ArticleRecommendationController()
