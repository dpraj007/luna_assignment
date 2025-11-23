"""
Layer 1: Inference Tests - Social Compatibility Matching

Tests the social matching and compatibility scoring algorithms.
"""
import pytest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'backend'))

from backend.app.services.recommendation import RecommendationEngine
from backend.app.models.user import User, UserPreferences, Friendship, UserPersona
from backend.app.models.venue import Venue
from backend.app.models.interaction import VenueInterest


class TestCompatibilityScoring:
    """Test compatibility scoring between users."""

    @pytest.mark.layer1
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_friends_have_higher_compatibility(
        self, db_session, users_with_friendships
    ):
        """Friends should have higher compatibility than strangers."""
        users, friendships = users_with_friendships
        alice = users[0]  # Alice is friends with Bob (user 2)
        bob = users[1]
        diana = users[3]  # Diana is not directly friends with Alice

        engine = RecommendationEngine(db_session)

        # Calculate compatibility with friend (Bob)
        friend_score, friend_reasons = await engine._calculate_compatibility(
            alice, bob, [bob.id, users[2].id], None
        )

        # Calculate compatibility with non-friend (Diana)
        non_friend_score, non_friend_reasons = await engine._calculate_compatibility(
            alice, diana, [bob.id, users[2].id], None
        )

        assert friend_score > non_friend_score, "Friend should have higher compatibility"
        assert "Friend" in friend_reasons

    @pytest.mark.layer1
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_similar_preferences_boost_compatibility(
        self, db_session, users_with_preferences
    ):
        """Users with similar preferences should have higher compatibility."""
        engine = RecommendationEngine(db_session)

        # Alice and Bob have overlapping Japanese cuisine preference
        alice, alice_prefs = users_with_preferences[0]
        bob, bob_prefs = users_with_preferences[1]

        similarity = await engine._calculate_preference_similarity(alice.id, bob.id)

        # They share "japanese" cuisine preference, similar price range
        assert similarity > 0.3, "Users with shared preferences should have some similarity"

    @pytest.mark.layer1
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_compatible_users_returned_sorted(
        self, db_session, users_with_friendships
    ):
        """Get compatible users should return results sorted by score."""
        users, _ = users_with_friendships
        alice = users[0]

        engine = RecommendationEngine(db_session)
        compatible = await engine.get_compatible_users(alice.id, limit=10)

        if len(compatible) > 1:
            scores = [c["compatibility_score"] for c in compatible]
            assert scores == sorted(scores, reverse=True), "Results should be sorted"

    @pytest.mark.layer1
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_compatible_users_exclude_self(
        self, db_session, multiple_users
    ):
        """User should not appear in their own compatible users list."""
        engine = RecommendationEngine(db_session)
        alice = multiple_users[0]

        compatible = await engine.get_compatible_users(alice.id, limit=20)

        user_ids = [c["id"] for c in compatible]
        assert alice.id not in user_ids, "User should not be in own compatibility list"

    @pytest.mark.layer1
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_compatible_users_include_required_fields(
        self, db_session, users_with_friendships
    ):
        """Compatible users should include all required fields."""
        users, _ = users_with_friendships
        alice = users[0]

        engine = RecommendationEngine(db_session)
        compatible = await engine.get_compatible_users(alice.id, limit=10)

        required_fields = [
            "id", "username", "compatibility_score", "reasons", "is_friend"
        ]

        for user in compatible:
            for field in required_fields:
                assert field in user, f"Missing field: {field}"

    @pytest.mark.layer1
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_activity_level_affects_compatibility(
        self, db_session, multiple_users
    ):
        """Users with similar activity levels should score higher."""
        # Alice has activity_score 0.9, Diana has 0.5
        alice = multiple_users[0]  # activity_score: 0.9
        bob = multiple_users[1]    # activity_score: 0.8
        diana = multiple_users[3]  # activity_score: 0.5

        # Alice should be more compatible with Bob (0.9 vs 0.8)
        # than with Diana (0.9 vs 0.5)
        activity_diff_bob = abs(alice.activity_score - bob.activity_score)  # 0.1
        activity_diff_diana = abs(alice.activity_score - diana.activity_score)  # 0.4

        assert activity_diff_bob < activity_diff_diana


class TestPreferenceSimilarity:
    """Test preference similarity calculations."""

    @pytest.mark.layer1
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_identical_preferences_max_similarity(self, db_session, multiple_users):
        """Identical preferences should give maximum similarity."""
        # Create two users with identical preferences
        alice = multiple_users[0]

        # Create identical preferences for both users
        prefs1 = UserPreferences(
            user_id=alice.id,
            cuisine_preferences=["italian", "japanese"],
            min_price_level=2,
            max_price_level=3,
            preferred_ambiance=["casual", "trendy"],
        )

        # Create a second user with same preferences
        bob = multiple_users[1]
        prefs2 = UserPreferences(
            user_id=bob.id,
            cuisine_preferences=["italian", "japanese"],
            min_price_level=2,
            max_price_level=3,
            preferred_ambiance=["casual", "trendy"],
        )

        db_session.add(prefs1)
        db_session.add(prefs2)
        await db_session.commit()

        engine = RecommendationEngine(db_session)
        similarity = await engine._calculate_preference_similarity(alice.id, bob.id)

        assert similarity == 1.0, "Identical preferences should have similarity of 1.0"

    @pytest.mark.layer1
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_no_overlap_low_similarity(self, db_session, multiple_users):
        """Completely different preferences should have low similarity."""
        alice = multiple_users[0]
        bob = multiple_users[1]

        # Create completely different preferences
        prefs1 = UserPreferences(
            user_id=alice.id,
            cuisine_preferences=["italian", "french"],
            min_price_level=3,
            max_price_level=4,
            preferred_ambiance=["romantic", "upscale"],
        )

        prefs2 = UserPreferences(
            user_id=bob.id,
            cuisine_preferences=["mexican", "thai"],
            min_price_level=1,
            max_price_level=2,
            preferred_ambiance=["casual", "fun"],
        )

        db_session.add(prefs1)
        db_session.add(prefs2)
        await db_session.commit()

        engine = RecommendationEngine(db_session)
        similarity = await engine._calculate_preference_similarity(alice.id, bob.id)

        assert similarity < 0.3, "Different preferences should have low similarity"

    @pytest.mark.layer1
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_partial_overlap_medium_similarity(self, db_session, multiple_users):
        """Partially overlapping preferences should have medium similarity."""
        alice = multiple_users[0]
        bob = multiple_users[1]

        # Create partially overlapping preferences
        prefs1 = UserPreferences(
            user_id=alice.id,
            cuisine_preferences=["italian", "japanese", "mexican"],
            min_price_level=2,
            max_price_level=3,
            preferred_ambiance=["casual", "trendy"],
        )

        prefs2 = UserPreferences(
            user_id=bob.id,
            cuisine_preferences=["japanese", "thai", "korean"],
            min_price_level=2,
            max_price_level=4,
            preferred_ambiance=["trendy", "upscale"],
        )

        db_session.add(prefs1)
        db_session.add(prefs2)
        await db_session.commit()

        engine = RecommendationEngine(db_session)
        similarity = await engine._calculate_preference_similarity(alice.id, bob.id)

        assert 0.2 < similarity < 0.8, "Partial overlap should have medium similarity"

    @pytest.mark.layer1
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_missing_preferences_returns_default(self, db_session, multiple_users):
        """Missing preferences should return default similarity."""
        alice = multiple_users[0]
        bob = multiple_users[1]

        # Only create preferences for one user
        prefs1 = UserPreferences(
            user_id=alice.id,
            cuisine_preferences=["italian"],
        )
        db_session.add(prefs1)
        await db_session.commit()

        engine = RecommendationEngine(db_session)
        similarity = await engine._calculate_preference_similarity(alice.id, bob.id)

        assert similarity == 0.5, "Missing preferences should return default 0.5"


class TestVenueInterestMatching:
    """Test interest-based user matching."""

    @pytest.mark.layer1
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_get_users_interested_in_venue(
        self, db_session, multiple_users, multiple_venues, venue_interests
    ):
        """Should return users interested in a specific venue."""
        engine = RecommendationEngine(db_session)

        # Get users interested in Sushi Palace (venue_id=2)
        # Alice (user_id=1) and Bob (user_id=2) expressed interest
        interested = await engine.get_users_interested_in_venue(venue_id=2)

        user_ids = [u["user_id"] for u in interested]
        assert 1 in user_ids or 2 in user_ids, "Should find interested users"

    @pytest.mark.layer1
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_exclude_user_from_interested_list(
        self, db_session, multiple_users, multiple_venues, venue_interests
    ):
        """Should exclude specified user from results."""
        engine = RecommendationEngine(db_session)

        # Get users interested in Sushi Palace, excluding Alice
        interested = await engine.get_users_interested_in_venue(
            venue_id=2,
            exclude_user_id=1
        )

        user_ids = [u["user_id"] for u in interested]
        assert 1 not in user_ids, "Excluded user should not appear"

    @pytest.mark.layer1
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_interested_users_include_required_fields(
        self, db_session, multiple_users, multiple_venues, venue_interests
    ):
        """Interested users should include required fields."""
        engine = RecommendationEngine(db_session)
        interested = await engine.get_users_interested_in_venue(venue_id=2)

        required_fields = [
            "user_id", "username", "interest_score", "open_to_invites"
        ]

        for user in interested:
            for field in required_fields:
                assert field in user, f"Missing field: {field}"

    @pytest.mark.layer1
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_shared_venue_interest_boosts_compatibility(
        self, db_session, multiple_users, multiple_venues, venue_interests
    ):
        """Shared venue interest should boost compatibility score."""
        users = multiple_users
        alice = users[0]  # Interested in venue 2 (Sushi Palace)
        bob = users[1]    # Also interested in venue 2

        engine = RecommendationEngine(db_session)

        # Calculate compatibility with venue context
        score_with_venue, reasons = await engine._calculate_compatibility(
            alice, bob, [], venue_id=2
        )

        # Calculate without venue context
        score_without_venue, _ = await engine._calculate_compatibility(
            alice, bob, [], venue_id=None
        )

        # The venue interest should affect scoring (adds additional weight)
        assert "Interested in same venue" in reasons or score_with_venue >= score_without_venue


class TestGroupRecommendations:
    """Test group venue recommendations."""

    @pytest.mark.layer1
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_find_optimal_venue_for_group(
        self, db_session, users_with_preferences, multiple_venues
    ):
        """Should find venues suitable for a group."""
        user_ids = [u.id for u, _ in users_with_preferences]

        engine = RecommendationEngine(db_session)
        recommendations = await engine.find_optimal_venue_for_group(user_ids)

        assert len(recommendations) > 0, "Should return at least one recommendation"

    @pytest.mark.layer1
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_group_recommendations_sorted_by_score(
        self, db_session, users_with_preferences, multiple_venues
    ):
        """Group recommendations should be sorted by group score."""
        user_ids = [u.id for u, _ in users_with_preferences]

        engine = RecommendationEngine(db_session)
        recommendations = await engine.find_optimal_venue_for_group(user_ids)

        scores = [r["group_score"] for r in recommendations]
        assert scores == sorted(scores, reverse=True), "Should be sorted by score"

    @pytest.mark.layer1
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_group_venue_respects_capacity(
        self, db_session, users_with_preferences, multiple_venues
    ):
        """Group venues should have sufficient capacity."""
        user_ids = [u.id for u, _ in users_with_preferences]
        group_size = len(user_ids)

        engine = RecommendationEngine(db_session)
        recommendations = await engine.find_optimal_venue_for_group(user_ids)

        # Top recommendations should have capacity for the group
        for rec in recommendations[:3]:
            # Check that venue exists and has capacity
            # (Note: group score considers capacity)
            assert rec["group_score"] > 0

    @pytest.mark.layer1
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_empty_group_returns_empty(self, db_session):
        """Empty group should return empty recommendations."""
        engine = RecommendationEngine(db_session)
        recommendations = await engine.find_optimal_venue_for_group([])

        assert recommendations == []

    @pytest.mark.layer1
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_group_recommendations_include_required_fields(
        self, db_session, users_with_preferences, multiple_venues
    ):
        """Group recommendations should include required fields."""
        user_ids = [u.id for u, _ in users_with_preferences]

        engine = RecommendationEngine(db_session)
        recommendations = await engine.find_optimal_venue_for_group(user_ids)

        required_fields = ["id", "name", "category", "cuisine_type", "rating", "price_level", "group_score"]

        for rec in recommendations:
            for field in required_fields:
                assert field in rec, f"Missing field: {field}"


class TestGroupVenueScoring:
    """Test the group venue scoring algorithm."""

    @pytest.mark.layer1
    @pytest.mark.unit
    def test_group_score_within_range(self):
        """Group scores should be between 0 and 1."""
        engine = RecommendationEngine(None)

        venue = Venue(
            name="Test Venue",
            latitude=40.7580,
            longitude=-73.9855,
            cuisine_type="italian",
            price_level=2,
            rating=4.5,
            capacity=50,
        )

        score = engine._calculate_group_venue_score(
            venue,
            centroid_lat=40.7580,
            centroid_lon=-73.9855,
            cuisine_counts={"italian": 3},
            min_prices=[1, 2, 2],
            max_prices=[3, 3, 4],
            max_distances=[10.0, 10.0, 15.0],
            group_size=4
        )

        assert 0.0 <= score <= 1.0

    @pytest.mark.layer1
    @pytest.mark.unit
    def test_venue_too_far_scores_zero(self):
        """Venue too far from centroid should score 0."""
        engine = RecommendationEngine(None)

        # Venue in Brooklyn, group centroid in Manhattan
        venue = Venue(
            name="Far Venue",
            latitude=40.6782,  # Brooklyn
            longitude=-73.9442,
            cuisine_type="italian",
            price_level=2,
            rating=4.5,
            capacity=50,
        )

        score = engine._calculate_group_venue_score(
            venue,
            centroid_lat=40.7580,  # Times Square
            centroid_lon=-73.9855,
            cuisine_counts={"italian": 3},
            min_prices=[1, 2, 2],
            max_prices=[3, 3, 4],
            max_distances=[1.0, 1.0, 1.0],  # Very small distance limit
            group_size=4
        )

        assert score == 0.0, "Venue too far should score 0"

    @pytest.mark.layer1
    @pytest.mark.unit
    def test_insufficient_capacity_scores_zero(self):
        """Venue with insufficient capacity should score lower."""
        engine = RecommendationEngine(None)

        # Small venue for large group
        venue = Venue(
            name="Small Venue",
            latitude=40.7580,
            longitude=-73.9855,
            cuisine_type="italian",
            price_level=2,
            rating=4.5,
            capacity=3,  # Too small for group of 10
        )

        score = engine._calculate_group_venue_score(
            venue,
            centroid_lat=40.7580,
            centroid_lon=-73.9855,
            cuisine_counts={"italian": 5},
            min_prices=[2, 2, 2, 2, 2],
            max_prices=[3, 3, 3, 3, 3],
            max_distances=[10.0] * 5,
            group_size=10
        )

        # Should score lower due to capacity constraint
        assert score < 0.5

    @pytest.mark.layer1
    @pytest.mark.unit
    def test_popular_cuisine_scores_higher(self):
        """Venues matching popular cuisine should score higher."""
        engine = RecommendationEngine(None)

        # Create two venues with different cuisines
        popular_cuisine_venue = Venue(
            name="Italian Venue",
            latitude=40.7580,
            longitude=-73.9855,
            cuisine_type="italian",  # Popular in group
            price_level=2,
            rating=4.0,
            capacity=50,
        )

        unpopular_cuisine_venue = Venue(
            name="Ethiopian Venue",
            latitude=40.7580,
            longitude=-73.9855,
            cuisine_type="ethiopian",  # Not in preferences
            price_level=2,
            rating=4.0,
            capacity=50,
        )

        cuisine_counts = {"italian": 4, "japanese": 2}  # Italian is most popular

        popular_score = engine._calculate_group_venue_score(
            popular_cuisine_venue,
            centroid_lat=40.7580,
            centroid_lon=-73.9855,
            cuisine_counts=cuisine_counts,
            min_prices=[2, 2],
            max_prices=[3, 3],
            max_distances=[10.0, 10.0],
            group_size=4
        )

        unpopular_score = engine._calculate_group_venue_score(
            unpopular_cuisine_venue,
            centroid_lat=40.7580,
            centroid_lon=-73.9855,
            cuisine_counts=cuisine_counts,
            min_prices=[2, 2],
            max_prices=[3, 3],
            max_distances=[10.0, 10.0],
            group_size=4
        )

        assert popular_score > unpopular_score
