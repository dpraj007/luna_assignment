"""
Layer 3: Backend Tests - Database Operations

Tests for database connection, transactions, and queries.
"""
import pytest
from sqlalchemy import select, text
from sqlalchemy.exc import SQLAlchemyError
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'backend'))

from backend.app.models.user import User, UserPreferences
from backend.app.models.venue import Venue
from backend.app.models.booking import Booking


class TestDatabaseConnection:
    """Test database connection and session management."""

    @pytest.mark.layer3
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_session_is_async(self, db_session):
        """Session should be async."""
        from sqlalchemy.ext.asyncio import AsyncSession
        assert isinstance(db_session, AsyncSession)

    @pytest.mark.layer3
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_execute_raw_sql(self, db_session):
        """Should execute raw SQL queries."""
        result = await db_session.execute(text("SELECT 1 as value"))
        row = result.fetchone()
        assert row.value == 1

    @pytest.mark.layer3
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_session_commit(self, db_session):
        """Session commit should persist data."""
        user = User(email="commit@test.com", username="commituser")
        db_session.add(user)
        await db_session.commit()

        query = select(User).where(User.email == "commit@test.com")
        result = await db_session.execute(query)
        found = result.scalar_one_or_none()

        assert found is not None
        assert found.username == "commituser"

    @pytest.mark.layer3
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_session_rollback(self, db_session):
        """Session rollback should discard changes."""
        user = User(email="rollback@test.com", username="rollbackuser")
        db_session.add(user)
        await db_session.flush()

        # Check it's in session
        query = select(User).where(User.email == "rollback@test.com")
        result = await db_session.execute(query)
        found = result.scalar_one_or_none()
        assert found is not None

        # Rollback
        await db_session.rollback()

        # Should not be found after rollback
        result = await db_session.execute(query)
        found = result.scalar_one_or_none()
        assert found is None


class TestDatabaseTransactions:
    """Test transaction behavior."""

    @pytest.mark.layer3
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_transaction_atomicity(self, db_session):
        """Transactions should be atomic."""
        user = User(email="atomic1@test.com", username="atomic1")
        db_session.add(user)
        await db_session.commit()

        try:
            # Try to create another user with same email (should fail)
            duplicate = User(email="atomic1@test.com", username="atomic2")
            db_session.add(duplicate)
            await db_session.commit()
        except SQLAlchemyError:
            await db_session.rollback()

        # Original user should still exist
        query = select(User).where(User.username == "atomic1")
        result = await db_session.execute(query)
        found = result.scalar_one_or_none()
        assert found is not None

    @pytest.mark.layer3
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_nested_operations(self, db_session):
        """Nested operations should work correctly."""
        # Create user
        user = User(email="nested@test.com", username="nested")
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)

        # Create related preferences
        prefs = UserPreferences(
            user_id=user.id,
            cuisine_preferences=["italian"],
        )
        db_session.add(prefs)
        await db_session.commit()

        # Verify both exist
        user_query = select(User).where(User.id == user.id)
        user_result = await db_session.execute(user_query)
        found_user = user_result.scalar_one()

        prefs_query = select(UserPreferences).where(UserPreferences.user_id == user.id)
        prefs_result = await db_session.execute(prefs_query)
        found_prefs = prefs_result.scalar_one()

        assert found_user is not None
        assert found_prefs is not None


class TestDatabaseQueries:
    """Test various query patterns."""

    @pytest.mark.layer3
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_select_all(self, db_session, multiple_users):
        """Should select all records."""
        query = select(User)
        result = await db_session.execute(query)
        users = result.scalars().all()

        assert len(users) >= len(multiple_users)

    @pytest.mark.layer3
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_select_with_filter(self, db_session, multiple_users):
        """Should filter records correctly."""
        query = select(User).where(User.username == "alice")
        result = await db_session.execute(query)
        users = result.scalars().all()

        assert len(users) == 1
        assert users[0].username == "alice"

    @pytest.mark.layer3
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_select_with_multiple_filters(self, db_session, multiple_venues):
        """Should handle multiple filter conditions."""
        query = select(Venue).where(
            Venue.category == "restaurant",
            Venue.rating >= 4.5
        )
        result = await db_session.execute(query)
        venues = result.scalars().all()

        for venue in venues:
            assert venue.category == "restaurant"
            assert venue.rating >= 4.5

    @pytest.mark.layer3
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_select_with_order_by(self, db_session, multiple_venues):
        """Should order results correctly."""
        query = select(Venue).order_by(Venue.rating.desc())
        result = await db_session.execute(query)
        venues = result.scalars().all()

        ratings = [v.rating for v in venues]
        assert ratings == sorted(ratings, reverse=True)

    @pytest.mark.layer3
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_select_with_limit(self, db_session, multiple_venues):
        """Should limit results."""
        query = select(Venue).limit(2)
        result = await db_session.execute(query)
        venues = result.scalars().all()

        assert len(venues) == 2

    @pytest.mark.layer3
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_select_count(self, db_session, multiple_venues):
        """Should count records."""
        from sqlalchemy import func

        query = select(func.count(Venue.id))
        result = await db_session.execute(query)
        count = result.scalar()

        assert count == len(multiple_venues)

    @pytest.mark.layer3
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_select_with_in_clause(self, db_session, multiple_users):
        """Should handle IN clause."""
        usernames = ["alice", "bob"]
        query = select(User).where(User.username.in_(usernames))
        result = await db_session.execute(query)
        users = result.scalars().all()

        assert len(users) == 2
        for user in users:
            assert user.username in usernames

    @pytest.mark.layer3
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_select_with_like(self, db_session, multiple_users):
        """Should handle LIKE clause."""
        query = select(User).where(User.email.like("%@example.com"))
        result = await db_session.execute(query)
        users = result.scalars().all()

        for user in users:
            assert "@example.com" in user.email


class TestDatabasePerformance:
    """Test database performance characteristics."""

    @pytest.mark.layer3
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_bulk_insert(self, db_session):
        """Should handle bulk inserts efficiently."""
        import time

        users = [
            User(email=f"bulk{i}@test.com", username=f"bulkuser{i}")
            for i in range(100)
        ]

        start = time.time()
        db_session.add_all(users)
        await db_session.commit()
        elapsed = time.time() - start

        # Should complete in reasonable time
        assert elapsed < 5.0, f"Bulk insert took {elapsed}s"

        # Verify all inserted
        query = select(User).where(User.email.like("bulk%@test.com"))
        result = await db_session.execute(query)
        inserted = result.scalars().all()

        assert len(inserted) == 100

    @pytest.mark.layer3
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_indexed_query_performance(self, db_session, multiple_users):
        """Indexed columns should be fast to query."""
        import time

        # Email is indexed
        start = time.time()
        for _ in range(100):
            query = select(User).where(User.email == "alice@example.com")
            await db_session.execute(query)
        elapsed = time.time() - start

        # Should be very fast
        assert elapsed < 1.0, f"100 indexed queries took {elapsed}s"


class TestDatabaseRelationships:
    """Test relationship loading and cascades."""

    @pytest.mark.layer3
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_lazy_loading(self, db_session, sample_user_with_preferences):
        """Relationships should load correctly."""
        user, prefs = sample_user_with_preferences

        # Query user and access preferences
        query = select(User).where(User.id == user.id)
        result = await db_session.execute(query)
        loaded_user = result.scalar_one()

        # Preferences should be accessible
        prefs_query = select(UserPreferences).where(UserPreferences.user_id == loaded_user.id)
        prefs_result = await db_session.execute(prefs_query)
        loaded_prefs = prefs_result.scalar_one()

        assert loaded_prefs.cuisine_preferences is not None

    @pytest.mark.layer3
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_join_query(self, db_session, sample_user_with_preferences):
        """Should handle join queries."""
        user, prefs = sample_user_with_preferences

        query = select(User, UserPreferences).join(
            UserPreferences, User.id == UserPreferences.user_id
        ).where(User.id == user.id)

        result = await db_session.execute(query)
        rows = result.all()

        assert len(rows) == 1
        loaded_user, loaded_prefs = rows[0]
        assert loaded_user.id == user.id
        assert loaded_prefs.user_id == user.id
