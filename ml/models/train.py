import numpy as np
import joblib
from pathlib import Path
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.metrics import classification_report, confusion_matrix
from xgboost import XGBClassifier

from ml.features.profile_features import ProfileFeatures


MODEL_DIR = Path(__file__).parent.parent / "models" / "trained"


class BotClassifierTrainer:
    def __init__(self, model_type: str = "xgboost"):
        self.model_type = model_type
        self.scaler = StandardScaler()
        self.model = self._build_model()

    def _build_model(self):
        models = {
            "xgboost": XGBClassifier(
                n_estimators=200,
                max_depth=6,
                learning_rate=0.1,
                subsample=0.8,
                colsample_bytree=0.8,
                random_state=42,
            ),
            "random_forest": RandomForestClassifier(
                n_estimators=200,
                max_depth=10,
                random_state=42,
            ),
            "gradient_boosting": GradientBoostingClassifier(
                n_estimators=200,
                max_depth=5,
                learning_rate=0.1,
                random_state=42,
            ),
        }
        return models.get(self.model_type, models["xgboost"])

    def prepare_data(
        self, samples: list[ProfileFeatures]
    ) -> tuple[np.ndarray, np.ndarray]:
        X = np.array([s.to_array() for s in samples], dtype=np.float64)
        y = np.array([s.label for s in samples], dtype=np.int32)
        return X, y

    def train(
        self,
        samples: list[ProfileFeatures],
        test_size: float = 0.2,
    ) -> dict:
        X, y = self.prepare_data(samples)
        X_scaled = self.scaler.fit_transform(X)

        X_train, X_test, y_train, y_test = train_test_split(
            X_scaled, y, test_size=test_size, random_state=42, stratify=y
        )

        self.model.fit(X_train, y_train)

        y_pred = self.model.predict(X_test)
        y_proba = self.model.predict_proba(X_test)

        cv_scores = cross_val_score(self.model, X_scaled, y, cv=5)

        report = classification_report(y_test, y_pred, output_dict=True)
        report["cv_mean"] = float(cv_scores.mean())
        report["cv_std"] = float(cv_scores.std())

        return report

    def save(self, suffix: str = "") -> None:
        MODEL_DIR.mkdir(parents=True, exist_ok=True)
        joblib.dump(self.model, str(MODEL_DIR / f"bot_classifier{suffix}.pkl"))
        joblib.dump(self.scaler, str(MODEL_DIR / f"feature_scaler{suffix}.pkl"))

    @staticmethod
    def generate_synthetic_data(n_samples: int = 5000) -> list[ProfileFeatures]:
        np.random.seed(42)
        samples = []

        for _ in range(n_samples):
            is_bot = np.random.random() < 0.3

            if is_bot:
                followers = np.random.randint(0, 200)
                following = np.random.randint(500, 5000)
                posts = np.random.randint(0, 20)
                age = np.random.randint(1, 90)
                has_pic = np.random.random() < 0.3
                has_bio = np.random.random() < 0.2
                verified = False
                business = False
                likes = np.random.uniform(0, 5)
                comments = np.random.uniform(0, 1)
                growth = np.random.uniform(0, 100)
                default_pic = np.random.random() < 0.5
                caption_sim = np.random.uniform(0.5, 1.0)
                hashtag_r = np.random.uniform(0.7, 1.0)
            else:
                followers = np.random.randint(50, 50000)
                following = np.random.randint(30, 2000)
                posts = np.random.randint(5, 2000)
                age = np.random.randint(30, 3650)
                has_pic = np.random.random() < 0.95
                has_bio = np.random.random() < 0.9
                verified = np.random.random() < 0.05
                business = np.random.random() < 0.1
                likes = np.random.uniform(10, followers * 0.2)
                comments = np.random.uniform(1, followers * 0.05)
                growth = np.random.uniform(0, 50)
                default_pic = np.random.random() < 0.02
                caption_sim = np.random.uniform(0, 0.4)
                hashtag_r = np.random.uniform(0, 0.5)

            follow_ratio = following / max(followers, 1)
            engagement = ((likes + comments) / max(followers, 1)) * 100
            entropy = np.random.uniform(1.0, 4.0) if is_bot else np.random.uniform(1.5, 3.5)
            digit_r = np.random.uniform(0, 1.0)

            profile = ProfileFeatures(
                follower_count=followers,
                following_count=following,
                post_count=posts,
                account_age_days=age,
                has_profile_pic=has_pic,
                has_bio=has_bio,
                is_verified=verified,
                is_business=business,
                follow_ratio=follow_ratio,
                engagement_rate=engagement,
                username_entropy=entropy,
                digit_ratio=digit_r,
                post_like_avg=likes,
                post_comment_avg=comments,
                follower_growth_rate=growth,
                default_profile_pic=default_pic,
                caption_similarity=caption_sim,
                hashtag_ratio=hashtag_r,
                label=1 if is_bot else 0,
            )
            samples.append(profile)

        return samples


if __name__ == "__main__":
    trainer = BotClassifierTrainer(model_type="xgboost")
    data = BotClassifierTrainer.generate_synthetic_data(5000)
    report = trainer.train(data)
    print(f"CV Accuracy: {report['cv_mean']:.4f} (+/- {report['cv_std']:.4f})")
    trainer.save()
    print(f"Modelo guardado en: {MODEL_DIR}")
