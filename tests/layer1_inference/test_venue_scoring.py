"""
Layer 1: Inference Tests - Venue Scoring Algorithm

Tests the venue scoring and recommendation logic.
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'backend'))

from backend.app.services.recommendation import RecommendationEngine
from backend.app.models.user import User, UserPreferences, UserPersona
from backend.app.models.venue import Venue


class TestVenueScoring:
    """Test venue scoring algorithm."""

    @pytest.mark.layer1
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_venue_score_within_range(self, db_session, sample_user_with_preferences, multiple_venues):
        """Venue scores should be between 0 and 1."""
        user, preferences = sample_user_with_preferences
        engine = RecommendationEngine(db_session)

        for venue in multiple_venues:
            score = await engine._calculate_venue_score(user, preferences, venue)
            assert 0.0 <= score <= 1.0, f"Score {score} out of range for venue {venue.name}"

    @pytest.mark.layer1
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_distance_filter_excludes_far_venues(self, db_session, sample_user_with_preferences):
        """Venues beyond max distance should score 0."""
        user, preferences = sample_user_with_preferences
        # Set max distance to 5 km
        preferences.max_distance = 5.0

        # Create a venue far away (Brooklyn)
        far_venue = Venue(
            name="Far Away Place",
            latitude=40.6782,  # Brooklyn
            longitude=-73.9442,
            category="restaurant",
            cuisine_type="italian",
            price_level=2,
            rating=4.5,
            popularity_score=0.8,
        )

        engine = RecommendationEngine(db_session)
        score = await engine._calculate_venue_score(user, preferences, far_venue)

        # Should be 0 because it's too far (Times Square to Brooklyn is ~9km)
        assert score == 0.0

    @pytest.mark.layer1
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_nearby_venue_scores_higher(self, db_session, sample_user_with_preferences):
        """Nearby venues should score higher than distant ones (within range)."""
        user, preferences = sample_user_with_preferences
        preferences.max_distance = 20.0  # Allow both venues

        # Nearby venue (same location as user)
        nearby_venue = Venue(
            name="Nearby Place",
            latitude=user.latitude,
            longitude=user.longitude,
            category="restaurant",
            cuisine_type="italian",
            price_level=2,
            rating=4.5,
            popularity_score=0.8,
        )

        # Farther venue
        farther_venue = Venue(
            name="Farther Place",
            latitude=40.6782,  # Brooklyn
            longitude=-73.9442,
            category="restaurant",
            cuisine_type="italian",
            price_level=2,
            rating=4.5,
            popularity_score=0.8,
        )

        engine = RecommendationEngine(db_session)
        nearby_score = await engine._calculate_venue_score(user, preferences, nearby_venue)
        farther_score = await engine._calculate_venue_score(user, preferences, farther_venue)

        assert nearby_score > farther_score, "Nearby venue should score higher"

    @pytest.mark.layer1
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_preferred_cuisine_scores_higher(self, db_session, sample_user_with_preferences):
        """Venues with user's preferred cuisine should score higher."""
        user, preferences = sample_user_with_preferences
        preferences.cuisine_preferences = ["italian"]

        italian_venue = Venue(
            name="Italian Place",
            latitude=user.latitude,
            longitude=user.longitude,
            category="restaurant",
            cuisine_type="italian",
            price_level=2,
            rating=4.5,
            popularity_score=0.8,
        )

        french_venue = Venue(
            name="French Place",
            latitude=user.latitude,
            longitude=user.longitude,
            category="restaurant",
            cuisine_type="french",
            price_level=2,
            rating=4.5,
            popularity_score=0.8,
        )

        engine = RecommendationEngine(db_session)
        italian_score = await engine._calculate_venue_score(user, preferences, italian_venue)
        french_score = await engine._calculate_venue_score(user, preferences, french_venue)

        assert italian_score > french_score, "Preferred cuisine should score higher"

    @pytest.mark.layer1
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_price_range_within_preference(self, db_session, sample_user_with_preferences):
        """Venues within price range should score higher."""
        user, preferences = sample_user_with_preferences
        preferences.min_price_level = 2
        preferences.max_price_level = 3

        affordable_venue = Venue(
            name="Affordable Place",
            latitude=user.latitude,
            longitude=user.longitude,
            category="restaurant",
            cuisine_type="italian",
            price_level=2,  # Within range
            rating=4.5,
            popularity_score=0.8,
        )

        expensive_venue = Venue(
            name="Expensive Place",
            latitude=user.latitude,
            longitude=user.longitude,
            category="restaurant",
            cuisine_type="italian",
            price_level=4,  # Outside range
            rating=4.5,
            popularity_score=0.8,
        )

        engine = RecommendationEngine(db_session)
        affordable_score = await engine._calculate_venue_score(user, preferences, affordable_venue)
        expensive_score = await engine._calculate_venue_score(user, preferences, expensive_venue)

        assert affordable_score > expensive_score, "In-range price should score higher"

    @pytest.mark.layer1
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_higher_rating_scores_higher(self, db_session, sample_user_with_preferences):
        """Higher-rated venues should score higher."""
        user, preferences = sample_user_with_preferences

        high_rated_venue = Venue(
            name="High Rated",
            latitude=user.latitude,
            longitude=user.longitude,
            category="restaurant",
            cuisine_type="italian",
            price_level=2,
            rating=5.0,
            popularity_score=0.8,
        )

        low_rated_venue = Venue(
            name="Low Rated",
            latitude=user.latitude,
            longitude=user.longitude,
            category="restaurant",
            cuisine_type="italian",
            price_level=2,
            rating=3.0,
            popularity_score=0.8,
        )

        engine = RecommendationEngine(db_session)
        high_score = await engine._calculate_venue_score(user, preferences, high_rated_venue)
        low_score = await engine._calculate_venue_score(user, preferences, low_rated_venue)

        assert high_score > low_score, "Higher rating should score higher"

    @pytest.mark.layer1
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_trending_venue_bonus(self, db_session, sample_user_with_preferences):
        """Trending venues should get a score bonus."""
        user, preferences = sample_user_with_preferences

        trending_venue = Venue(
            name="Trending Place",
            latitude=user.latitude,
            longitude=user.longitude,
            category="restaurant",
            cuisine_type="italian",
            price_level=2,
            rating=4.0,
            popularity_score=0.8,
            trending=True,
        )

        non_trending_venue = Venue(
            name="Regular Place",
            latitude=user.latitude,
            longitude=user.longitude,
            category="restaurant",
            cuisine_type="italian",
            price_level=2,
            rating=4.0,
            popularity_score=0.8,
            trending=False,
        )

        engine = RecommendationEngine(db_session)
        trending_score = await engine._calculate_venue_score(user, preferences, trending_venue)
        non_trending_score = await engine._calculate_venue_score(user, preferences, non_trending_venue)

        assert trending_score > non_trending_score, "Trending venue should score higher"

    @pytest.mark.layer1
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_popularity_affects_score(self, db_session, sample_user_with_preferences):
        """More popular venues should score higher."""
        user, preferences = sample_user_with_preferences

        popular_venue = Venue(
            name="Popular Place",
            latitude=user.latitude,
            longitude=user.longitude,
            category="restaurant",
            cuisine_type="italian",
            price_level=2,
            rating=4.0,
            popularity_score=0.95,
        )

        unpopular_venue = Venue(
            name="Unknown Place",
            latitude=user.latitude,
            longitude=user.longitude,
            category="restaurant",
            cuisine_type="italian",
            price_level=2,
            rating=4.0,
            popularity_score=0.3,
        )

        engine = RecommendationEngine(db_session)
        popular_score = await engine._calculate_venue_score(user, preferences, popular_venue)
        unpopular_score = await engine._calculate_venue_score(user, preferences, unpopular_venue)

        assert popular_score > unpopular_score, "Popular venue should score higher"

    @pytest.mark.layer1
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_user_without_location(self, db_session):
        """Test scoring for user without location data."""
        user = User(
            email="noloc@test.com",
            username="noloc",
            latitude=None,
            longitude=None,
        )

        preferences = UserPreferences(
            user_id=1,
            cuisine_preferences=["italian"],
            min_price_level=2,
            max_price_level=3,
        )

        venue = Venue(
            name="Test Place",
            latitude=40.7128,
            longitude=-74.0060,
            category="restaurant",
            cuisine_type="italian",
            price_level=2,
            rating=4.5,
            popularity_score=0.8,
        )

        engine = RecommendationEngine(db_session)
        score = await engine._calculate_venue_score(user, preferences, venue)

        # Should still return a valid score (just without distance component)
        assert 0.0 <= score <= 1.0

    @pytest.mark.layer1
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_user_without_preferences(self, db_session, sample_user):
        """Test scoring for user without preferences."""
        venue = Venue(
            name="Test Place",
            latitude=sample_user.latitude,
            longitude=sample_user.longitude,
            category="restaurant",
            cuisine_type="italian",
            price_level=2,
            rating=4.5,
            popularity_score=0.8,
        )

        engine = RecommendationEngine(db_session)
        score = await engine._calculate_venue_score(sample_user, None, venue)

        # Should still return a valid score using defaults
        assert 0.0 <= score <= 1.0


class TestVenueRecommendations:
    """Test the full recommendation pipeline."""

    @pytest.mark.layer1
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_get_recommendations_returns_results(
        self, db_session, sample_user_with_preferences, multiple_venues
    ):
        """Get recommendations should return scored venues."""
        user, _ = sample_user_with_preferences

        engine = RecommendationEngine(db_session)
        recommendations = await engine.get_venue_recommendations(user.id, limit=5)

        assert len(recommendations) > 0
        assert len(recommendations) <= 5

    @pytest.mark.layer1
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_recommendations_sorted_by_score(
        self, db_session, sample_user_with_preferences, multiple_venues
    ):
        """Recommendations should be sorted by score descending."""
        user, _ = sample_user_with_preferences

        engine = RecommendationEngine(db_session)
        recommendations = await engine.get_venue_recommendations(user.id, limit=10)

        scores = [r["score"] for r in recommendations]
        assert scores == sorted(scores, reverse=True), "Results should be sorted by score"

    @pytest.mark.layer1
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_recommendations_include_required_fields(
        self, db_session, sample_user_with_preferences, multiple_venues
    ):
        """Recommendations should include all required fields."""
        user, _ = sample_user_with_preferences

        engine = RecommendationEngine(db_session)
        recommendations = await engine.get_venue_recommendations(user.id, limit=5)

        required_fields = [
            "id", "name", "category", "cuisine_type", "rating",
            "price_level", "score", "latitude", "longitude"
        ]

        for rec in recommendations:
            for field in required_fields:
                assert field in rec, f"Missing field: {field}"

    @pytest.mark.layer1
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_recommendations_with_category_filter(
        self, db_session, sample_user_with_preferences, multiple_venues
    ):
        """Filtering by category should work."""
        user, _ = sample_user_with_preferences

        engine = RecommendationEngine(db_session)
        recommendations = await engine.get_venue_recommendations(
            user.id,
            limit=10,
            filters={"category": "restaurant"}
        )

        for rec in recommendations:
            assert rec["category"] == "restaurant"

    @pytest.mark.layer1
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_recommendations_with_rating_filter(
        self, db_session, sample_user_with_preferences, multiple_venues
    ):
        """Filtering by minimum rating should work."""
        user, _ = sample_user_with_preferences

        engine = RecommendationEngine(db_session)
        recommendations = await engine.get_venue_recommendations(
            user.id,
            limit=10,
            filters={"min_rating": 4.5}
        )

        for rec in recommendations:
            assert rec["rating"] >= 4.5

    @pytest.mark.layer1
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_recommendations_for_nonexistent_user(self, db_session, multiple_venues):
        """Recommendations for nonexistent user should return empty list."""
        engine = RecommendationEngine(db_session)
        recommendations = await engine.get_venue_recommendations(user_id=99999, limit=5)

        assert recommendations == []

    @pytest.mark.layer1
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_limit_parameter(
        self, db_session, sample_user_with_preferences, multiple_venues
    ):
        """Limit parameter should be respected."""
        user, _ = sample_user_with_preferences

        engine = RecommendationEngine(db_session)

        for limit in [1, 2, 3]:
            recommendations = await engine.get_venue_recommendations(user.id, limit=limit)
            assert len(recommendations) <= limit
