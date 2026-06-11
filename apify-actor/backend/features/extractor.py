import math
import re
from collections import Counter
from typing import Optional
from app.models.schemas import ProfileData, FeatureVector


class FeatureExtractor:
    NUMERIC_FEATURES = [
        "follower_count",
        "following_count",
        "post_count",
        "account_age_days",
        "follow_ratio",
        "engagement_rate",
        "username_entropy",
        "digit_ratio_in_username",
        "post_like_avg",
        "post_comment_avg",
        "follower_growth_rate",
        "caption_similarity_score",
        "posts_with_hashtags_ratio",
    ]

    BINARY_FEATURES = [
        "has_profile_pic",
        "has_bio",
        "is_verified",
        "is_business",
        "default_profile_pic",
    ]

    @classmethod
    def extract_numeric_features(cls, profile: ProfileData) -> list[float]:
        return [getattr(profile, f, 0.0) for f in cls.NUMERIC_FEATURES]

    @classmethod
    def extract_binary_features(cls, profile: ProfileData) -> list[float]:
        return [float(getattr(profile, f, False)) for f in cls.BINARY_FEATURES]

    @classmethod
    def to_feature_vector(cls, profile: ProfileData) -> FeatureVector:
        numeric = cls.extract_numeric_features(profile)
        binary = cls.extract_binary_features(profile)
        all_features = numeric + binary
        all_names = cls.NUMERIC_FEATURES + cls.BINARY_FEATURES
        return FeatureVector(
            profile_id=profile.id,
            features=all_features,
            feature_names=all_names,
        )

    @staticmethod
    def compute_derived_features(profile: ProfileData) -> None:
        profile.follow_ratio = (
            profile.following_count / max(profile.follower_count, 1)
        )
        total_interactions = profile.post_like_avg + profile.post_comment_avg
        profile.engagement_rate = (
            (total_interactions / max(profile.follower_count, 1)) * 100
        )

    @staticmethod
    def compute_username_entropy(username: str) -> float:
        if not username:
            return 0.0
        freq = Counter(username)
        length = len(username)
        entropy = 0.0
        for count in freq.values():
            p = count / length
            entropy -= p * math.log2(p)
        return entropy

    @staticmethod
    def compute_digit_ratio(username: str) -> float:
        if not username:
            return 0.0
        digits = sum(1 for c in username if c.isdigit())
        return digits / len(username)

    @staticmethod
    def compute_caption_similarity(captions: list[str]) -> float:
        if len(captions) < 2:
            return 0.0
        total_similarity = 0.0
        pairs = 0
        for i in range(len(captions)):
            for j in range(i + 1, len(captions)):
                total_similarity += FeatureExtractor._jaccard_similarity(
                    captions[i], captions[j]
                )
                pairs += 1
        return total_similarity / max(pairs, 1)

    @staticmethod
    def _jaccard_similarity(text_a: str, text_b: str) -> float:
        words_a = set(text_a.lower().split())
        words_b = set(text_b.lower().split())
        if not words_a or not words_b:
            return 0.0
        intersection = words_a & words_b
        union = words_a | words_b
        return len(intersection) / len(union)
