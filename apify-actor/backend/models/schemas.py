from datetime import datetime, timezone
from typing import Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, field_validator


class ExposedDatum(BaseModel):
    category: str
    label: str
    detail: str
    url: str = ""
    risk_level: str = "low"


class PrivacyReport(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    query: str
    query_type: str
    privacy_score: int
    total_exposures: int
    exposures: list[ExposedDatum]
    images: list[ExposedDatum] = Field(default_factory=list)
    categories: dict[str, int]
    data_sources: list[str]
    recommendations: list[str] = Field(default_factory=list)
    analyzed_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class PrivacyRequest(BaseModel):
    query: str = Field(..., min_length=2, max_length=200)
    query_type: str = Field(default="auto", max_length=50)

    @field_validator("query")
    @classmethod
    def sanitize_query(cls, v: str) -> str:
        import re
        stripped = v.strip()
        if re.search(r'[<>{}()\[\];&|`$]', stripped):
            raise ValueError("Query contains forbidden characters")
        if re.search(r'(?:\.\./|\.\.\\)', stripped):
            raise ValueError("Query contains forbidden patterns")
        return stripped

    @field_validator("query_type")
    @classmethod
    def validate_query_type(cls, v: str) -> str:
        allowed = {"auto", "email", "phone", "username", "name"}
        if v not in allowed:
            return "auto"
        return v


class PrivacyResponse(BaseModel):
    status: str
    report: Optional[PrivacyReport] = None
    message: Optional[str] = None


class FeatureVector(BaseModel):
    profile_id: UUID
    features: list[float]
    feature_names: list[str]


class DetectionResult(BaseModel):
    profile_id: UUID
    username: str
    is_fake: bool
    is_bot: bool
    confidence: float
    risk_score: float
    flagged_features: list[str]
    explanation: str
    is_active: bool = False
    last_post_days_ago: int = 0
    activity_level: str = ""
    public_email: str = ""
    public_phone: str = ""
    external_url: str = ""
    bio_text: str = ""
    associated_platforms: list[dict] = Field(default_factory=list)
    web_presence: list[dict] = Field(default_factory=list)
    posts_found: list[dict] = Field(default_factory=list)
    data_source: str = ""


class ProfileData(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    username: str
    platform: str
    follower_count: int = 0
    following_count: int = 0
    post_count: int = 0
    account_age_days: int = 365
    has_profile_pic: bool = False
    has_bio: bool = False
    has_external_url: bool = False
    is_verified: bool = False
    is_business: bool = False
    bio_length: int = 0
    bio_text: str = ""
    public_email: str = ""
    public_phone: str = ""
    external_url: str = ""
    is_active: bool = False
    last_post_days_ago: int = 0
    posts_per_week: float = 0.0
    activity_level: str = ""
    follow_ratio: float = 0.0
    engagement_rate: float = 0.0
    username_entropy: float = 0.0
    digit_ratio_in_username: float = 0.0
    post_like_avg: float = 0.0
    post_comment_avg: float = 0.0
    follower_growth_rate: float = 0.0
    following_growth_rate: float = 0.0
    caption_similarity_score: float = 0.0
    posts_with_hashtags_ratio: float = 0.0
    unique_hashtags_ratio: float = 0.0
    posts_with_mentions_ratio: float = 0.0
    avg_post_interval_hours: float = 0.0
    default_profile_pic: bool = False
    associated_platforms: list[dict] = Field(default_factory=list)
    web_presence: list[dict] = Field(default_factory=list)
    posts_found: list[dict] = Field(default_factory=list)
    data_source: str = ""
