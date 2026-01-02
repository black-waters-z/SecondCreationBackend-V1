from typing import Any, Dict, List, Optional

from backend.models import (
    Article,
    ArticleRecommendation,
    ArticleRewardRanking,
    CrossRoleTag,
)
from backend.schemas.article import (
    ArticleCreate,
    ArticleRecommendationCreate,
    ArticleRecommendationUpdate,
    ArticleRewardRankingCreate,
    ArticleRewardRankingUpdate,
    ArticleUpdate,
)

from .base import ApiController


class ArticleController(ApiController[Article, ArticleCreate, ArticleUpdate]):
    def __init__(self) -> None:
        super().__init__(Article)

    async def create(self, obj_in: ArticleCreate | Dict[str, Any]) -> Article:
        if isinstance(obj_in, dict):
            tag_ids = obj_in.get("tag_ids")
            data = {k: v for k, v in obj_in.items() if k != "tag_ids"}
        else:
            tag_ids = obj_in.tag_ids
            data = obj_in.model_dump(exclude={"tag_ids"}, exclude_none=True)

        article = await super().create(data)
        if tag_ids:
            tags = await CrossRoleTag.filter(id__in=list(tag_ids))
            if tags:
                await article.tags.add(*tags)
        return article

    async def update(
        self,
        id: int,
        obj_in: ArticleUpdate | Dict[str, Any],
    ) -> Article:
        if isinstance(obj_in, dict):
            tag_ids = obj_in.get("tag_ids")
            data = {k: v for k, v in obj_in.items() if k != "tag_ids"}
        else:
            tag_ids = obj_in.tag_ids
            data = obj_in.model_dump(exclude={"tag_ids"}, exclude_unset=True)

        article = await super().update(id=id, obj_in=data)
        if tag_ids is not None:
            await article.tags.clear()
            if tag_ids:
                tags = await CrossRoleTag.filter(id__in=list(tag_ids))
                if tags:
                    await article.tags.add(*tags)
        return article


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
