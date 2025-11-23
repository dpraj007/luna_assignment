"""
Global test fixtures and configuration for Luna Social tests.
"""
import pytest
import asyncio
from typing import AsyncGenerator, Generator
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.pool import StaticPool
from httpx import AsyncClient, ASGITransport
from unittest.mock import AsyncMock, patch
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from backend.app.core.database import Base
from backend.app.main import app
from backend.app.core.database import get_db
from backend.app.models.user import User, UserPreferences, Friendship, UserPersona
from backend.app.models.venue import Venue
from backend.app.models.booking import Booking, BookingInvitation
from backend.app.models.interaction import VenueInterest, UserInteraction


# ============== DATABASE FIXTURES ==============

@pytest.fixture(scope="function")
async def async_engine():
    """Create a test database engine (in-memory SQLite)."""
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        echo=False,
        poolclass=StaticPool,
    )

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await engine.dispose()


@pytest.fixture(scope="function")
async def db_session(async_engine) -> AsyncGenerator[AsyncSession, None]:
    """Create a test database session."""
    async_session_factory = async_sessionmaker(
        async_engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autocommit=False,
        autoflush=False
    )

    async with async_session_factory() as session:
        yield session
        await session.rollback()


@pytest.fixture(scope="function", autouse=True)
def mock_llm_client():
    """Mock LLM client to prevent real API calls during tests."""
    from backend.app.services.llm_client import OpenRouterClient, LLMResponse
    
    mock_client = AsyncMock(spec=OpenRouterClient)
    mock_client.is_configured = False  # This triggers fallback behavior
    mock_client.generate_recommendation_explanation = AsyncMock(
        return_value="Great venue recommendation based on your preferences!"
    )
    mock_client.generate_social_match_reason = AsyncMock(
        return_value="Great compatibility match!"
    )
    mock_client.complete = AsyncMock(
        return_value=LLMResponse(
            content="Mocked LLM response",
            model="test-model",
            usage={"prompt_tokens": 10, "completion_tokens": 20},
            finish_reason="stop"
        )
    )
    mock_client.chat = AsyncMock(
        return_value=LLMResponse(
            content="Mocked LLM response",
            model="test-model",
            usage={"prompt_tokens": 10, "completion_tokens": 20},
            finish_reason="stop"
        )
    )
    
    # Patch all places where get_llm_client is used
    patches = [
        patch("backend.app.services.llm_client.get_llm_client", return_value=mock_client),
        patch("backend.app.agents.recommendation_agent.get_llm_client", return_value=mock_client),
        patch("backend.app.api.routes.admin.get_llm_client", return_value=mock_client),
    ]
    
    # Start all patches
    for p in patches:
        p.start()
    
    yield mock_client
    
    # Stop all patches
    for p in patches:
        p.stop()


@pytest.fixture(scope="function")
async def client(async_engine, mock_llm_client) -> AsyncGenerator[AsyncClient, None]:
    """Create a test HTTP client with test database."""
    async_session_factory = async_sessionmaker(
        async_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    async def override_get_db():
        async with async_session_factory() as session:
            yield session

    # Patch init_db to avoid touching real database file during tests
    with patch("backend.app.main.init_db", new_callable=AsyncMock) as mock_init:
        # Reset simulation orchestrator singleton to avoid stale DB sessions
        from backend.app.api.routes import simulation
        simulation._orchestrator = None

        app.dependency_overrides[get_db] = override_get_db

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            yield ac

        app.dependency_overrides.clear()


# ============== USER FIXTURES ==============

@pytest.fixture
def sample_user_data():
    """Sample user data for testing."""
    return {
        "email": "testuser@example.com",
        "username": "testuser",
        "full_name": "Test User",
        "latitude": 40.7580,  # NYC - Times Square
        "longitude": -73.9855,
        "persona": UserPersona.SOCIAL_BUTTERFLY,
        "activity_score": 0.7,
        "social_score": 0.8,
    }


@pytest.fixture
async def sample_user(db_session, sample_user_data) -> User:
    """Create a sample user in the database."""
    user = User(**sample_user_data)
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest.fixture
async def sample_user_with_preferences(db_session, sample_user) -> tuple[User, UserPreferences]:
    """Create a user with preferences."""
    preferences = UserPreferences(
        user_id=sample_user.id,
        cuisine_preferences=["italian", "japanese", "mexican"],
        min_price_level=2,
        max_price_level=3,
        preferred_ambiance=["casual", "trendy"],
        dietary_restrictions=["vegetarian"],
        preferred_group_size=4,
        open_to_new_people=True,
        max_distance=10.0,
        preferred_dining_times=["lunch", "dinner"],
    )
    db_session.add(preferences)
    await db_session.commit()
    await db_session.refresh(preferences)
    return sample_user, preferences


@pytest.fixture
async def multiple_users(db_session) -> list[User]:
    """Create multiple users with different personas."""
    users_data = [
        {
            "email": "alice@example.com",
            "username": "alice",
            "full_name": "Alice Smith",
            "latitude": 40.7580,
            "longitude": -73.9855,
            "persona": UserPersona.SOCIAL_BUTTERFLY,
            "activity_score": 0.9,
            "social_score": 0.95,
        },
        {
            "email": "bob@example.com",
            "username": "bob",
            "full_name": "Bob Jones",
            "latitude": 40.7484,
            "longitude": -73.9857,
            "persona": UserPersona.FOODIE_EXPLORER,
            "activity_score": 0.8,
            "social_score": 0.6,
        },
        {
            "email": "charlie@example.com",
            "username": "charlie",
            "full_name": "Charlie Brown",
            "latitude": 40.7614,
            "longitude": -73.9776,
            "persona": UserPersona.EVENT_ORGANIZER,
            "activity_score": 0.7,
            "social_score": 0.85,
        },
        {
            "email": "diana@example.com",
            "username": "diana",
            "full_name": "Diana Prince",
            "latitude": 40.7527,
            "longitude": -73.9772,
            "persona": UserPersona.BUSY_PROFESSIONAL,
            "activity_score": 0.5,
            "social_score": 0.5,
        },
    ]

    users = []
    for data in users_data:
        user = User(**data)
        db_session.add(user)
        users.append(user)

    await db_session.commit()

    for user in users:
        await db_session.refresh(user)

    return users


# ============== VENUE FIXTURES ==============

@pytest.fixture
def sample_venue_data():
    """Sample venue data for testing."""
    return {
        "name": "Italian Bistro",
        "description": "Authentic Italian cuisine in Manhattan",
        "address": "123 Main St, New York, NY",
        "city": "New York",
        "latitude": 40.7589,
        "longitude": -73.9851,
        "category": "restaurant",
        "cuisine_type": "italian",
        "price_level": 2,
        "rating": 4.5,
        "review_count": 150,
        "ambiance": ["romantic", "casual"],
        "capacity": 50,
        "current_occupancy": 20,
        "accepts_reservations": True,
        "features": ["outdoor_seating", "wine_bar"],
        "popularity_score": 0.8,
        "trending": True,
    }


@pytest.fixture
async def sample_venue(db_session, sample_venue_data) -> Venue:
    """Create a sample venue in the database."""
    venue = Venue(**sample_venue_data)
    db_session.add(venue)
    await db_session.commit()
    await db_session.refresh(venue)
    return venue


@pytest.fixture
async def multiple_venues(db_session) -> list[Venue]:
    """Create multiple venues with different characteristics."""
    venues_data = [
        {
            "name": "Italian Bistro",
            "description": "Authentic Italian cuisine",
            "address": "123 Main St",
            "city": "New York",
            "latitude": 40.7589,
            "longitude": -73.9851,
            "category": "restaurant",
            "cuisine_type": "italian",
            "price_level": 2,
            "rating": 4.5,
            "review_count": 150,
            "ambiance": ["romantic", "casual"],
            "capacity": 50,
            "popularity_score": 0.8,
            "trending": True,
        },
        {
            "name": "Sushi Palace",
            "description": "Fresh Japanese sushi",
            "address": "456 Broadway",
            "city": "New York",
            "latitude": 40.7505,
            "longitude": -73.9934,
            "category": "restaurant",
            "cuisine_type": "japanese",
            "price_level": 3,
            "rating": 4.8,
            "review_count": 200,
            "ambiance": ["upscale", "trendy"],
            "capacity": 40,
            "popularity_score": 0.9,
            "trending": True,
        },
        {
            "name": "Taco Stand",
            "description": "Authentic Mexican street food",
            "address": "789 Lexington Ave",
            "city": "New York",
            "latitude": 40.7614,
            "longitude": -73.9680,
            "category": "fast_casual",
            "cuisine_type": "mexican",
            "price_level": 1,
            "rating": 4.2,
            "review_count": 300,
            "ambiance": ["casual", "fun"],
            "capacity": 30,
            "popularity_score": 0.7,
            "trending": False,
        },
        {
            "name": "French Brasserie",
            "description": "Classic French dining",
            "address": "321 Park Ave",
            "city": "New York",
            "latitude": 40.7549,
            "longitude": -73.9840,
            "category": "fine_dining",
            "cuisine_type": "french",
            "price_level": 4,
            "rating": 4.7,
            "review_count": 100,
            "ambiance": ["romantic", "upscale"],
            "capacity": 60,
            "popularity_score": 0.85,
            "trending": False,
        },
        {
            "name": "Budget Diner",
            "description": "Affordable American classics",
            "address": "555 5th Ave",
            "city": "New York",
            "latitude": 40.7800,
            "longitude": -73.9650,
            "category": "casual_dining",
            "cuisine_type": "american",
            "price_level": 1,
            "rating": 3.8,
            "review_count": 500,
            "ambiance": ["casual", "family"],
            "capacity": 100,
            "popularity_score": 0.6,
            "trending": False,
        },
    ]

    venues = []
    for data in venues_data:
        venue = Venue(**data)
        db_session.add(venue)
        venues.append(venue)

    await db_session.commit()

    for venue in venues:
        await db_session.refresh(venue)

    return venues


# ============== RELATIONSHIP FIXTURES ==============

@pytest.fixture
async def users_with_friendships(db_session, multiple_users) -> tuple[list[User], list[Friendship]]:
    """Create users with friendship relationships."""
    friendships_data = [
        # Alice and Bob are friends
        {"user_id": 1, "friend_id": 2, "compatibility_score": 0.85, "interaction_count": 10},
        {"user_id": 2, "friend_id": 1, "compatibility_score": 0.85, "interaction_count": 10},
        # Alice and Charlie are friends
        {"user_id": 1, "friend_id": 3, "compatibility_score": 0.75, "interaction_count": 5},
        {"user_id": 3, "friend_id": 1, "compatibility_score": 0.75, "interaction_count": 5},
        # Bob and Diana are friends
        {"user_id": 2, "friend_id": 4, "compatibility_score": 0.65, "interaction_count": 3},
        {"user_id": 4, "friend_id": 2, "compatibility_score": 0.65, "interaction_count": 3},
    ]

    friendships = []
    for data in friendships_data:
        friendship = Friendship(**data)
        db_session.add(friendship)
        friendships.append(friendship)

    await db_session.commit()

    return multiple_users, friendships


@pytest.fixture
async def users_with_preferences(db_session, multiple_users) -> list[tuple[User, UserPreferences]]:
    """Create users with their preferences."""
    preferences_data = [
        {
            "user_id": 1,
            "cuisine_preferences": ["italian", "japanese"],
            "min_price_level": 2,
            "max_price_level": 3,
            "preferred_ambiance": ["trendy", "romantic"],
            "open_to_new_people": True,
            "max_distance": 10.0,
        },
        {
            "user_id": 2,
            "cuisine_preferences": ["japanese", "korean", "thai"],
            "min_price_level": 2,
            "max_price_level": 4,
            "preferred_ambiance": ["upscale", "trendy"],
            "open_to_new_people": True,
            "max_distance": 15.0,
        },
        {
            "user_id": 3,
            "cuisine_preferences": ["mexican", "american", "italian"],
            "min_price_level": 1,
            "max_price_level": 3,
            "preferred_ambiance": ["casual", "fun"],
            "open_to_new_people": True,
            "max_distance": 20.0,
        },
        {
            "user_id": 4,
            "cuisine_preferences": ["french", "italian"],
            "min_price_level": 3,
            "max_price_level": 4,
            "preferred_ambiance": ["upscale", "romantic"],
            "open_to_new_people": False,
            "max_distance": 5.0,
        },
    ]

    results = []
    for i, data in enumerate(preferences_data):
        prefs = UserPreferences(**data)
        db_session.add(prefs)
        results.append((multiple_users[i], prefs))

    await db_session.commit()

    return results


# ============== BOOKING FIXTURES ==============

@pytest.fixture
async def sample_booking(db_session, sample_user, sample_venue) -> Booking:
    """Create a sample booking."""
    from datetime import datetime, timedelta

    booking = Booking(
        user_id=sample_user.id,
        venue_id=sample_venue.id,
        booking_time=datetime.utcnow() + timedelta(days=1),
        party_size=4,
        status="confirmed",
        confirmation_code="TEST123",
    )
    db_session.add(booking)
    await db_session.commit()
    await db_session.refresh(booking)
    return booking


# ============== INTEREST FIXTURES ==============

@pytest.fixture
async def venue_interests(db_session, multiple_users, multiple_venues) -> list[VenueInterest]:
    """Create venue interests for users."""
    interests_data = [
        # Alice is interested in Italian Bistro and Sushi Palace
        {"user_id": 1, "venue_id": 1, "interest_score": 0.9, "explicitly_interested": True, "open_to_invites": True},
        {"user_id": 1, "venue_id": 2, "interest_score": 0.8, "explicitly_interested": True, "open_to_invites": True},
        # Bob is interested in Sushi Palace
        {"user_id": 2, "venue_id": 2, "interest_score": 0.95, "explicitly_interested": True, "open_to_invites": True},
        # Charlie is interested in Taco Stand
        {"user_id": 3, "venue_id": 3, "interest_score": 0.85, "explicitly_interested": True, "open_to_invites": True},
        # Diana is interested in French Brasserie
        {"user_id": 4, "venue_id": 4, "interest_score": 0.9, "explicitly_interested": True, "open_to_invites": False},
    ]

    interests = []
    for data in interests_data:
        interest = VenueInterest(**data)
        db_session.add(interest)
        interests.append(interest)

    await db_session.commit()

    return interests


# ============== UTILITY FIXTURES ==============

@pytest.fixture
def coordinates():
    """Common test coordinates."""
    return {
        "nyc_times_square": (40.7580, -73.9855),
        "nyc_central_park": (40.7829, -73.9654),
        "nyc_brooklyn": (40.6782, -73.9442),
        "los_angeles": (34.0522, -118.2437),
        "london": (51.5074, -0.1278),
    }


@pytest.fixture
def api_v1_prefix():
    """API v1 prefix."""
    return "/api/v1"
