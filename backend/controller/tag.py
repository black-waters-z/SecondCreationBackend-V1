from backend.models import ArticleTag, CrossRoleTag, RoleTag
from backend.schemas.tag import (
    ArticleTagCreate,
    ArticleTagUpdate,
    CrossRoleTagCreate,
    CrossRoleTagUpdate,
    RoleTagCreate,
    RoleTagUpdate,
)

from .base import ApiController


class RoleTagController(ApiController[RoleTag, RoleTagCreate, RoleTagUpdate]):
    def __init__(self) -> None:
        super().__init__(RoleTag)


class CrossRoleTagController(
    ApiController[CrossRoleTag, CrossRoleTagCreate, CrossRoleTagUpdate]
):
    def __init__(self) -> None:
        super().__init__(CrossRoleTag)


class ArticleTagController(
    ApiController[ArticleTag, ArticleTagCreate, ArticleTagUpdate]
):
    def __init__(self) -> None:
        super().__init__(ArticleTag)


role_tag_controller = RoleTagController()
cross_role_tag_controller = CrossRoleTagController()
article_tag_controller = ArticleTagController()
