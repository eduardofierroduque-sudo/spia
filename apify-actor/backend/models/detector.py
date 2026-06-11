import joblib
import numpy as np
from pathlib import Path
from typing import Optional

from app.core.config import get_settings
from app.features.extractor import FeatureExtractor
from app.models.schemas import ProfileData, FeatureVector, DetectionResult

settings = get_settings()


class BotDetector:
    def __init__(self):
        self.model = None
        self.scaler = None
        self.threshold = 0.65
        self._load_models()

    def _load_models(self) -> None:
        model_path = Path(settings.model_path)
        scaler_path = Path(settings.feature_model_path)
        if model_path.exists():
            self.model = joblib.load(str(model_path))
        if scaler_path.exists():
            self.scaler = joblib.load(str(scaler_path))

    def predict(self, profile: ProfileData) -> DetectionResult:
        FeatureExtractor.compute_derived_features(profile)
        vector = FeatureExtractor.to_feature_vector(profile)
        features = np.array(vector.features, dtype=np.float64).reshape(1, -1)

        if self.scaler is not None:
            features = self.scaler.transform(features)

        flagged = self._get_flagged_features(profile)

        if self.model is not None:
            proba = self.model.predict_proba(features)[0]
            bot_prob = proba[1] if len(proba) > 1 else proba[0]
            confidence = float(max(proba))
            is_fake = bot_prob >= self.threshold
        else:
            bot_prob = self._heuristic_score(profile)
            confidence = bot_prob
            is_fake = bot_prob >= self.threshold

        risk_score = min(bot_prob * 100, 100.0)
        is_bot = risk_score > 70

        return DetectionResult(
            profile_id=profile.id,
            username=profile.username,
            is_fake=is_fake,
            is_bot=is_bot,
            confidence=round(confidence, 4),
            risk_score=round(risk_score, 2),
            flagged_features=flagged,
            explanation=self._generate_explanation(flagged, risk_score),
            is_active=profile.is_active,
            last_post_days_ago=profile.last_post_days_ago,
            activity_level=profile.activity_level,
            public_email=profile.public_email,
            public_phone=profile.public_phone,
            external_url=profile.external_url,
            bio_text=profile.bio_text,
            associated_platforms=profile.associated_platforms,
            web_presence=profile.web_presence,
            posts_found=profile.posts_found,
            data_source=profile.data_source,
        )

    def _get_flagged_features(self, profile: ProfileData) -> list[str]:
        flagged = []

        if profile.follow_ratio > 10 or profile.follow_ratio < 0.01:
            flagged.append("follow_ratio")

        if profile.follower_count > 0 and profile.engagement_rate < 0.5:
            flagged.append("low_engagement")

        if profile.account_age_days < 30 and profile.post_count > 50:
            flagged.append("suspicious_activity_new_account")

        if profile.digit_ratio_in_username > 0.4:
            flagged.append("high_digit_ratio_username")

        if not profile.has_profile_pic:
            flagged.append("no_profile_pic")

        if not profile.has_bio:
            flagged.append("no_bio")

        if profile.follower_growth_rate > 500:
            flagged.append("rapid_follower_growth")

        if profile.caption_similarity_score > 0.8:
            flagged.append("repetitive_content")

        if profile.posts_with_hashtags_ratio > 0.9:
            flagged.append("hashtag_spam")

        if profile.default_profile_pic:
            flagged.append("default_profile_pic")

        if not profile.is_active:
            flagged.append("inactive_account")

        return flagged

    def _heuristic_score(self, profile: ProfileData) -> float:
        score = 0.0
        flags = 0

        if profile.follow_ratio > 10 or profile.follow_ratio < 0.01:
            score += 0.15
            flags += 1

        if profile.follower_count > 0 and profile.engagement_rate < 0.5:
            score += 0.12
            flags += 1

        if profile.account_age_days < 30 and profile.post_count > 50:
            score += 0.15
            flags += 1

        if profile.digit_ratio_in_username > 0.4:
            score += 0.10
            flags += 1

        if not profile.has_profile_pic:
            score += 0.12
            flags += 1

        if not profile.has_bio:
            score += 0.10
            flags += 1

        if profile.follower_growth_rate > 500:
            score += 0.10
            flags += 1

        if profile.default_profile_pic:
            score += 0.08
            flags += 1

        if profile.caption_similarity_score > 0.8:
            score += 0.08
            flags += 1

        if not profile.is_active:
            score += 0.05
            flags += 1

        return min(score, 1.0)

    def _generate_explanation(self, flagged: list[str], risk_score: float) -> str:
        explanations = {
            "follow_ratio": "Abnormal follower/following ratio",
            "low_engagement": "Suspiciously low engagement for follower count",
            "suspicious_activity_new_account": "New account with high activity",
            "high_digit_ratio_username": "Username contains many digits (bot pattern)",
            "no_profile_pic": "No profile picture",
            "no_bio": "No bio",
            "rapid_follower_growth": "Abnormally fast follower growth",
            "repetitive_content": "Highly repetitive content",
            "hashtag_spam": "Excessive hashtag usage",
            "default_profile_pic": "Default profile picture",
            "inactive_account": "Inactive or abandoned account",
        }

        if not flagged:
            return "No significant suspicious indicators detected"

        reasons = [explanations.get(f, f) for f in flagged]
        level = "high" if risk_score > 70 else "medium" if risk_score > 40 else "low"
        return f"Risk {level}. Indicators: " + "; ".join(reasons)
