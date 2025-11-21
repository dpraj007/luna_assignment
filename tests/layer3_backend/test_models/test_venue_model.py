"""
Layer 3: Backend Tests - Venue Model

Tests for venue-related database models.
"""
import pytest
from sqlalchemy import select
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..', 'backend'))

from backend.app.models.venue import Venue, VenueCategory


class TestVenueModel:
    """Test Venue model CRUD operations."""

    @pytest.mark.layer3
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_create_venue(self, db_session):
        """Should create a venue successfully."""
        venue = Venue(
            name="Test Restaurant",
            description="A test restaurant",
            latitude=40.7128,
            longitude=-74.0060,
            category="restaurant",
            cuisine_type="italian",
        )
        db_session.add(venue)
        await db_session.commit()
        await db_session.refresh(venue)

        assert venue.id is not None
        assert venue.name == "Test Restaurant"
        assert venue.created_at is not None

    @pytest.mark.layer3
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_venue_default_values(self, db_session):
        """Venue should have expected default values."""
        venue = Venue(
            name="Defaults Test",
            latitude=40.7128,
            longitude=-74.0060,
        )
        db_session.add(venue)
        await db_session.commit()
        await db_session.refresh(venue)

        assert venue.price_level == 2
        assert venue.rating == 4.0
        assert venue.review_count == 0
        assert venue.capacity == 50
        assert venue.current_occupancy == 0
        assert venue.accepts_reservations is True
        assert venue.popularity_score == 0.5
        assert venue.trending is False

    @pytest.mark.layer3
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_venue_json_fields(self, db_session):
        """JSON fields should store and retrieve correctly."""
        venue = Venue(
            name="JSON Test",
            latitude=40.7128,
            longitude=-74.0060,
            ambiance=["romantic", "upscale", "trendy"],
            features=["outdoor_seating", "live_music", "happy_hour"],
            photos=["photo1.jpg", "photo2.jpg"],
            operating_hours={"monday": {"open": "11:00", "close": "22:00"}},
        )
        db_session.add(venue)
        await db_session.commit()
        await db_session.refresh(venue)

        assert len(venue.ambiance) == 3
        assert "romantic" in venue.ambiance
        assert "outdoor_seating" in venue.features
        assert venue.operating_hours["monday"]["open"] == "11:00"

    @pytest.mark.layer3
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_venue_is_available_property(self, db_session):
        """is_available property should work correctly."""
        venue = Venue(
            name="Availability Test",
            latitude=40.7128,
            longitude=-74.0060,
            capacity=50,
            current_occupancy=40,
        )
        db_session.add(venue)
        await db_session.commit()

        assert venue.is_available is True

        venue.current_occupancy = 50
        assert venue.is_available is False

        venue.current_occupancy = 51
        assert venue.is_available is False

    @pytest.mark.layer3
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_read_venue(self, db_session, sample_venue):
        """Should read venue by ID."""
        query = select(Venue).where(Venue.id == sample_venue.id)
        result = await db_session.execute(query)
        venue = result.scalar_one()

        assert venue.name == sample_venue.name
        assert venue.latitude == sample_venue.latitude

    @pytest.mark.layer3
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_update_venue(self, db_session, sample_venue):
        """Should update venue fields."""
        sample_venue.rating = 4.9
        sample_venue.trending = True
        await db_session.commit()
        await db_session.refresh(sample_venue)

        assert sample_venue.rating == 4.9
        assert sample_venue.trending is True
        assert sample_venue.updated_at is not None

    @pytest.mark.layer3
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_venue_price_levels(self, db_session):
        """Price levels should be stored correctly."""
        for level in [1, 2, 3, 4]:
            venue = Venue(
                name=f"Price Level {level}",
                latitude=40.7128,
                longitude=-74.0060,
                price_level=level,
            )
            db_session.add(venue)

        await db_session.commit()

        query = select(Venue).where(Venue.name.like("Price Level%"))
        result = await db_session.execute(query)
        venues = result.scalars().all()

        assert len(venues) == 4
        price_levels = {v.price_level for v in venues}
        assert price_levels == {1, 2, 3, 4}

    @pytest.mark.layer3
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_venue_rating_range(self, db_session):
        """Rating should be stored with correct precision."""
        venue = Venue(
            name="Rating Test",
            latitude=40.7128,
            longitude=-74.0060,
            rating=4.75,
        )
        db_session.add(venue)
        await db_session.commit()
        await db_session.refresh(venue)

        assert venue.rating == 4.75

    @pytest.mark.layer3
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_venue_repr(self, sample_venue):
        """Venue repr should be informative."""
        repr_str = repr(sample_venue)
        assert "Venue" in repr_str
        assert str(sample_venue.id) in repr_str
        assert sample_venue.name in repr_str

    @pytest.mark.layer3
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_filter_venues_by_category(self, db_session, multiple_venues):
        """Should filter venues by category."""
        query = select(Venue).where(Venue.category == "restaurant")
        result = await db_session.execute(query)
        restaurants = result.scalars().all()

        assert len(restaurants) > 0
        for venue in restaurants:
            assert venue.category == "restaurant"

    @pytest.mark.layer3
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_filter_venues_by_city(self, db_session, multiple_venues):
        """Should filter venues by city."""
        query = select(Venue).where(Venue.city == "New York")
        result = await db_session.execute(query)
        ny_venues = result.scalars().all()

        assert len(ny_venues) == len(multiple_venues)

    @pytest.mark.layer3
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_filter_venues_by_rating(self, db_session, multiple_venues):
        """Should filter venues by minimum rating."""
        query = select(Venue).where(Venue.rating >= 4.5)
        result = await db_session.execute(query)
        high_rated = result.scalars().all()

        for venue in high_rated:
            assert venue.rating >= 4.5


class TestVenueCategoryConstants:
    """Test venue category constants."""

    @pytest.mark.layer3
    @pytest.mark.unit
    def test_venue_categories_defined(self):
        """All expected categories should be defined."""
        expected = [
            "RESTAURANT", "BAR", "CAFE", "CLUB", "LOUNGE",
            "BRUNCH_SPOT", "FINE_DINING", "CASUAL_DINING", "FAST_CASUAL"
        ]

        for category in expected:
            assert hasattr(VenueCategory, category)

    @pytest.mark.layer3
    @pytest.mark.unit
    def test_category_values_are_lowercase(self):
        """Category values should be lowercase strings."""
        assert VenueCategory.RESTAURANT == "restaurant"
        assert VenueCategory.BAR == "bar"
        assert VenueCategory.FINE_DINING == "fine_dining"
