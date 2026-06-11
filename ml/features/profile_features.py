import numpy as np
from typing import Optional
from dataclasses import dataclass


@dataclass
class ProfileFeatures:
    follower_count: int = 0
    following_count: int = 0
    post_count: int = 0
    account_age_days: int = 0
    has_profile_pic: bool = False
    has_bio: bool = False
    is_verified: bool = False
    is_business: bool = False
    follow_ratio: float = 0.0
    engagement_rate: float = 0.0
    username_entropy: float = 0.0
    digit_ratio: float = 0.0
    post_like_avg: float = 0.0
    post_comment_avg: float = 0.0
    follower_growth_rate: float = 0.0
    default_profile_pic: bool = False
    caption_similarity: float = 0.0
    hashtag_ratio: float = 0.0
    label: Optional[int] = None

    def to_array(self) -> np.ndarray:
        return np.array([
            self.follower_count,
            self.following_count,
            self.post_count,
            self.account_age_days,
            self.follow_ratio,
            self.engagement_rate,
            self.username_entropy,
            self.digit_ratio,
            self.post_like_avg,
            self.post_comment_avg,
            self.follower_growth_rate,
            self.caption_similarity,
            self.hashtag_ratio,
            float(self.has_profile_pic),
            float(self.has_bio),
            float(self.is_verified),
            float(self.is_business),
            float(self.default_profile_pic),
        ], dtype=np.float64)
