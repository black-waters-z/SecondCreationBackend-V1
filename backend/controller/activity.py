from backend.models import (
    Reward,
    UserFavorite,
    UserInterest,
    UserLike,
    UserViewHistory,
)
from backend.schemas.activity import (
    RewardCreate,
    RewardUpdate,
    UserFavoriteCreate,
    UserFavoriteUpdate,
    UserInterestCreate,
    UserInterestUpdate,
    UserLikeCreate,
    UserLikeUpdate,
    UserViewHistoryCreate,
    UserViewHistoryUpdate,
)

from .base import ApiController


class UserViewHistoryController(
    ApiController[UserViewHistory, UserViewHistoryCreate, UserViewHistoryUpdate]
):
    def __init__(self) -> None:
        super().__init__(UserViewHistory)


class UserFavoriteController(
    ApiController[UserFavorite, UserFavoriteCreate, UserFavoriteUpdate]
):
    def __init__(self) -> None:
        super().__init__(UserFavorite)


class UserLikeController(ApiController[UserLike, UserLikeCreate, UserLikeUpdate]):
    def __init__(self) -> None:
        super().__init__(UserLike)


class RewardController(ApiController[Reward, RewardCreate, RewardUpdate]):
    def __init__(self) -> None:
        super().__init__(Reward)


class UserInterestController(
    ApiController[UserInterest, UserInterestCreate, UserInterestUpdate]
):
    def __init__(self) -> None:
        super().__init__(UserInterest)


user_view_history_controller = UserViewHistoryController()
user_favorite_controller = UserFavoriteController()
user_like_controller = UserLikeController()
reward_controller = RewardController()
user_interest_controller = UserInterestController()
