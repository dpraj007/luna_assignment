"""
Layer 3: Backend Tests - User Model

Tests for user-related database models.
"""
import pytest
from datetime import datetime
from sqlalchemy import select
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..', 'backend'))

from backend.app.models.user import User, UserPreferences, Friendship, UserPersona


class TestUserModel:
    """Test User model CRUD operations."""

    @pytest.mark.layer3
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_create_user(self, db_session):
        """Should create a user successfully."""
        user = User(
            email="newuser@test.com",
            username="newuser",
            full_name="New User",
            latitude=40.7128,
            longitude=-74.0060,
        )
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)

        assert user.id is not None
        assert user.email == "newuser@test.com"
        assert user.created_at is not None

    @pytest.mark.layer3
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_user_default_values(self, db_session):
        """User should have expected default values."""
        user = User(
            email="defaults@test.com",
            username="defaults",
        )
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)

        assert user.is_simulated is False
        assert user.activity_score == 0.5
        assert user.social_score == 0.5
        assert user.persona is None

    @pytest.mark.layer3
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_user_with_persona(self, db_session):
        """User can be created with a persona."""
        user = User(
            email="persona@test.com",
            username="persona",
            persona=UserPersona.FOODIE_EXPLORER,
        )
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)

        assert user.persona == UserPersona.FOODIE_EXPLORER

    @pytest.mark.layer3
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_user_unique_email(self, db_session, sample_user):
        """Email should be unique."""
        duplicate = User(
            email=sample_user.email,
            username="different",
        )
        db_session.add(duplicate)

        with pytest.raises(Exception):  # IntegrityError
            await db_session.commit()
        await db_session.rollback()

    @pytest.mark.layer3
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_user_unique_username(self, db_session, sample_user):
        """Username should be unique."""
        duplicate = User(
            email="different@test.com",
            username=sample_user.username,
        )
        db_session.add(duplicate)

        with pytest.raises(Exception):  # IntegrityError
            await db_session.commit()
        await db_session.rollback()

    @pytest.mark.layer3
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_read_user(self, db_session, sample_user):
        """Should read user by ID."""
        query = select(User).where(User.id == sample_user.id)
        result = await db_session.execute(query)
        user = result.scalar_one()

        assert user.username == sample_user.username
        assert user.email == sample_user.email

    @pytest.mark.layer3
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_update_user(self, db_session, sample_user):
        """Should update user fields."""
        sample_user.full_name = "Updated Name"
        sample_user.activity_score = 0.9
        await db_session.commit()
        await db_session.refresh(sample_user)

        assert sample_user.full_name == "Updated Name"
        assert sample_user.activity_score == 0.9

    @pytest.mark.layer3
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_delete_user(self, db_session, sample_user):
        """Should delete user."""
        user_id = sample_user.id
        await db_session.delete(sample_user)
        await db_session.commit()

        query = select(User).where(User.id == user_id)
        result = await db_session.execute(query)
        user = result.scalar_one_or_none()

        assert user is None

    @pytest.mark.layer3
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_user_repr(self, sample_user):
        """User repr should be informative."""
        repr_str = repr(sample_user)
        assert "User" in repr_str
        assert str(sample_user.id) in repr_str
        assert sample_user.username in repr_str


class TestUserPreferencesModel:
    """Test UserPreferences model."""

    @pytest.mark.layer3
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_create_preferences(self, db_session, sample_user):
        """Should create user preferences."""
        prefs = UserPreferences(
            user_id=sample_user.id,
            cuisine_preferences=["italian", "japanese"],
            min_price_level=2,
            max_price_level=3,
            max_distance=10.0,
        )
        db_session.add(prefs)
        await db_session.commit()
        await db_session.refresh(prefs)

        assert prefs.id is not None
        assert prefs.cuisine_preferences == ["italian", "japanese"]

    @pytest.mark.layer3
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_preferences_default_values(self, db_session, sample_user):
        """Preferences should have expected defaults."""
        prefs = UserPreferences(user_id=sample_user.id)
        db_session.add(prefs)
        await db_session.commit()
        await db_session.refresh(prefs)

        assert prefs.min_price_level == 1
        assert prefs.max_price_level == 4
        assert prefs.preferred_group_size == 4
        assert prefs.open_to_new_people is True
        assert prefs.max_distance == 10.0

    @pytest.mark.layer3
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_preferences_json_fields(self, db_session, sample_user):
        """JSON fields should store and retrieve correctly."""
        prefs = UserPreferences(
            user_id=sample_user.id,
            cuisine_preferences=["mexican", "thai", "korean"],
            preferred_ambiance=["casual", "trendy", "romantic"],
            dietary_restrictions=["vegetarian", "gluten-free"],
            preferred_dining_times=["lunch", "dinner"],
        )
        db_session.add(prefs)
        await db_session.commit()
        await db_session.refresh(prefs)

        assert len(prefs.cuisine_preferences) == 3
        assert "thai" in prefs.cuisine_preferences
        assert "casual" in prefs.preferred_ambiance
        assert "vegetarian" in prefs.dietary_restrictions

    @pytest.mark.layer3
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_preferences_one_per_user(self, db_session, sample_user_with_preferences):
        """Each user should have at most one preferences record."""
        user, prefs = sample_user_with_preferences

        duplicate = UserPreferences(user_id=user.id)
        db_session.add(duplicate)

        with pytest.raises(Exception):  # IntegrityError (unique constraint)
            await db_session.commit()
        await db_session.rollback()


class TestFriendshipModel:
    """Test Friendship model."""

    @pytest.mark.layer3
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_create_friendship(self, db_session, multiple_users):
        """Should create friendship between users."""
        user1, user2 = multiple_users[0], multiple_users[1]

        friendship = Friendship(
            user_id=user1.id,
            friend_id=user2.id,
            compatibility_score=0.85,
        )
        db_session.add(friendship)
        await db_session.commit()
        await db_session.refresh(friendship)

        assert friendship.id is not None
        assert friendship.compatibility_score == 0.85
        assert friendship.status == "active"

    @pytest.mark.layer3
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_friendship_default_values(self, db_session, multiple_users):
        """Friendship should have expected defaults."""
        user1, user2 = multiple_users[0], multiple_users[1]

        friendship = Friendship(
            user_id=user1.id,
            friend_id=user2.id,
        )
        db_session.add(friendship)
        await db_session.commit()
        await db_session.refresh(friendship)

        assert friendship.compatibility_score == 0.5
        assert friendship.interaction_count == 0
        assert friendship.status == "active"

    @pytest.mark.layer3
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_friendship_relationships(self, db_session, users_with_friendships):
        """Friendship should have user relationships."""
        users, friendships = users_with_friendships

        # Query first friendship
        query = select(Friendship).where(Friendship.user_id == users[0].id).limit(1)
        result = await db_session.execute(query)
        friendship = result.scalar_one()

        assert friendship.user_id == users[0].id
        assert friendship.friend_id in [u.id for u in users]


class TestUserPersonaEnum:
    """Test UserPersona enum."""

    @pytest.mark.layer3
    @pytest.mark.unit
    def test_all_personas_defined(self):
        """All expected personas should be defined."""
        expected = [
            "SOCIAL_BUTTERFLY", "FOODIE_EXPLORER", "ROUTINE_REGULAR",
            "EVENT_ORGANIZER", "SPONTANEOUS_DINER", "BUSY_PROFESSIONAL",
            "BUDGET_CONSCIOUS"
        ]

        for persona in expected:
            assert hasattr(UserPersona, persona)

    @pytest.mark.layer3
    @pytest.mark.unit
    def test_persona_values_are_lowercase(self):
        """Persona values should be lowercase strings."""
        for persona in UserPersona:
            assert persona.value.islower()
