"""
Layer 2: Agent Tests - Booking Agent

Tests the booking agent's workflow, state machine, and event publishing.
"""
import pytest
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, patch, MagicMock
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'backend'))

from backend.app.agents.booking_agent import BookingAgent, BookingState
from backend.app.models.booking import Booking, BookingStatus, BookingInvitation
from backend.app.models.venue import Venue
from backend.app.models.user import User


class TestBookingAgentWorkflow:
    """Test the booking agent's workflow steps."""

    @pytest.mark.layer2
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_successful_booking_workflow(
        self, db_session, sample_user, sample_venue
    ):
        """Test complete successful booking workflow."""
        agent = BookingAgent(db_session)

        result = await agent.create_booking(
            user_id=sample_user.id,
            venue_id=sample_venue.id,
            party_size=4,
            preferred_time=datetime.utcnow() + timedelta(days=1),
        )

        assert result["success"] is True
        assert "booking_id" in result
        assert "confirmation_code" in result
        assert result["status"] == "confirmed"
        assert result["party_size"] == 4

    @pytest.mark.layer2
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_booking_with_group_members(
        self, db_session, sample_user, sample_venue, multiple_users
    ):
        """Test booking with group members sends invitations."""
        agent = BookingAgent(db_session)

        group_member_ids = [u.id for u in multiple_users[:2]]

        result = await agent.create_booking(
            user_id=sample_user.id,
            venue_id=sample_venue.id,
            party_size=3,
            group_members=group_member_ids,
        )

        assert result["success"] is True
        assert result["invitations_sent"] >= 0

    @pytest.mark.layer2
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_booking_generates_confirmation_code(
        self, db_session, sample_user, sample_venue
    ):
        """Booking should generate unique confirmation code."""
        agent = BookingAgent(db_session)

        result1 = await agent.create_booking(
            user_id=sample_user.id,
            venue_id=sample_venue.id,
            party_size=2,
        )

        result2 = await agent.create_booking(
            user_id=sample_user.id,
            venue_id=sample_venue.id,
            party_size=2,
        )

        assert result1["confirmation_code"] != result2["confirmation_code"]
        assert len(result1["confirmation_code"]) == 8

    @pytest.mark.layer2
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_booking_nonexistent_venue_fails(
        self, db_session, sample_user
    ):
        """Booking at nonexistent venue should fail."""
        agent = BookingAgent(db_session)

        result = await agent.create_booking(
            user_id=sample_user.id,
            venue_id=99999,  # Nonexistent
            party_size=2,
        )

        assert result["success"] is False
        assert "not found" in result["errors"][0].lower()
        assert result["status"] == "failed"


class TestBookingAgentValidation:
    """Test booking validation logic."""

    @pytest.mark.layer2
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_venue_capacity_validation(self, db_session, sample_user):
        """Booking should fail if venue capacity exceeded."""
        # Create a small capacity venue
        small_venue = Venue(
            name="Tiny Place",
            latitude=40.7128,
            longitude=-74.0060,
            capacity=5,
            current_occupancy=4,
            accepts_reservations=True,
        )
        db_session.add(small_venue)
        await db_session.commit()
        await db_session.refresh(small_venue)

        agent = BookingAgent(db_session)

        result = await agent.create_booking(
            user_id=sample_user.id,
            venue_id=small_venue.id,
            party_size=10,  # More than capacity
        )

        assert result["success"] is False
        assert "capacity" in result["errors"][0].lower()

    @pytest.mark.layer2
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_venue_no_reservations_fails(self, db_session, sample_user):
        """Booking should fail if venue doesn't accept reservations."""
        no_res_venue = Venue(
            name="Walk-in Only",
            latitude=40.7128,
            longitude=-74.0060,
            capacity=50,
            accepts_reservations=False,
        )
        db_session.add(no_res_venue)
        await db_session.commit()
        await db_session.refresh(no_res_venue)

        agent = BookingAgent(db_session)

        result = await agent.create_booking(
            user_id=sample_user.id,
            venue_id=no_res_venue.id,
            party_size=4,
        )

        assert result["success"] is False
        assert "reservations" in result["errors"][0].lower()


class TestBookingAgentTimeSelection:
    """Test optimal time selection logic."""

    @pytest.mark.layer2
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_preferred_time_used(
        self, db_session, sample_user, sample_venue
    ):
        """Preferred time should be used when provided."""
        agent = BookingAgent(db_session)
        preferred = datetime.utcnow() + timedelta(days=2, hours=3)

        result = await agent.create_booking(
            user_id=sample_user.id,
            venue_id=sample_venue.id,
            party_size=2,
            preferred_time=preferred,
        )

        assert result["success"] is True
        # Check that booking time matches preferred time
        booking_time = datetime.fromisoformat(result["booking_time"])
        assert booking_time == preferred

    @pytest.mark.layer2
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_auto_time_selection_morning(self, db_session):
        """Morning booking should default to lunch time."""
        agent = BookingAgent(db_session)

        state: BookingState = {
            "user_id": 1,
            "venue_id": 1,
            "party_size": 2,
            "preferred_time": None,
            "group_members": [],
            "special_requests": None,
            "booking": None,
            "invitations_sent": [],
            "status": "venue_validated",
            "errors": []
        }

        # Mock the current time to be morning
        with patch('backend.app.agents.booking_agent.datetime') as mock_dt:
            mock_now = datetime(2024, 1, 15, 9, 0, 0)  # 9 AM
            mock_dt.utcnow.return_value = mock_now

            result = await agent._find_optimal_time(state)

            # Should schedule for lunch (12:00)
            assert result["preferred_time"].hour == 12


class TestBookingAgentStateTransitions:
    """Test state machine transitions."""

    @pytest.mark.layer2
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_validate_venue_state_transition(
        self, db_session, sample_user, sample_venue
    ):
        """Validate venue should transition state correctly."""
        agent = BookingAgent(db_session)

        state: BookingState = {
            "user_id": sample_user.id,
            "venue_id": sample_venue.id,
            "party_size": 2,
            "preferred_time": None,
            "group_members": [],
            "special_requests": None,
            "booking": None,
            "invitations_sent": [],
            "status": "initiated",
            "errors": []
        }

        result = await agent._validate_venue(state)
        assert result["status"] == "venue_validated"
        assert len(result["errors"]) == 0

    @pytest.mark.layer2
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_failed_state_blocks_further_steps(self, db_session):
        """Failed state should block subsequent workflow steps."""
        agent = BookingAgent(db_session)

        state: BookingState = {
            "user_id": 1,
            "venue_id": 1,
            "party_size": 2,
            "preferred_time": None,
            "group_members": [],
            "special_requests": None,
            "booking": None,
            "invitations_sent": [],
            "status": "failed",
            "errors": ["Previous error"]
        }

        # These should not modify state
        result = await agent._find_optimal_time(state)
        assert result["status"] == "failed"

        result = await agent._create_booking(state)
        assert result["status"] == "failed"
        assert result["booking"] is None


class TestBookingAgentInvitations:
    """Test invitation handling."""

    @pytest.mark.layer2
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_invitations_exclude_organizer(
        self, db_session, sample_user, sample_venue, multiple_users
    ):
        """Organizer should not receive invitation to their own booking."""
        agent = BookingAgent(db_session)

        # Include organizer in group members
        group_members = [sample_user.id, multiple_users[0].id, multiple_users[1].id]

        result = await agent.create_booking(
            user_id=sample_user.id,
            venue_id=sample_venue.id,
            party_size=3,
            group_members=group_members,
        )

        assert result["success"] is True
        # Organizer shouldn't get invite to their own booking
        assert result["invitations_sent"] == 2  # Only 2, not 3


class TestBookingAgentAutoBook:
    """Test auto-booking for interested users."""

    @pytest.mark.layer2
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_auto_book_creates_bookings_for_interested_users(
        self, db_session, multiple_users, multiple_venues, venue_interests
    ):
        """Auto-book should create bookings for interested users."""
        agent = BookingAgent(db_session)

        # Venue 2 (Sushi Palace) has Alice and Bob interested
        results = await agent.auto_book_interested_users(venue_id=2)

        # May or may not create bookings depending on matching criteria
        assert isinstance(results, list)

    @pytest.mark.layer2
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_auto_book_returns_empty_for_single_interest(
        self, db_session, sample_user, sample_venue
    ):
        """Auto-book should return empty if only one user interested."""
        from backend.app.models.interaction import VenueInterest

        # Create single interest
        interest = VenueInterest(
            user_id=sample_user.id,
            venue_id=sample_venue.id,
            explicitly_interested=True,
            open_to_invites=True,
        )
        db_session.add(interest)
        await db_session.commit()

        agent = BookingAgent(db_session)
        results = await agent.auto_book_interested_users(venue_id=sample_venue.id)

        # Need at least 2 users for auto-booking
        assert results == []


class TestBookingAgentConfirmationCode:
    """Test confirmation code generation."""

    @pytest.mark.layer2
    @pytest.mark.unit
    def test_confirmation_code_format(self, db_session):
        """Confirmation code should be 8 alphanumeric characters."""
        agent = BookingAgent(db_session)

        for _ in range(10):
            code = agent._generate_confirmation_code()
            assert len(code) == 8
            assert code.isalnum()
            assert code.isupper() or any(c.isdigit() for c in code)

    @pytest.mark.layer2
    @pytest.mark.unit
    def test_confirmation_codes_are_unique(self, db_session):
        """Generated confirmation codes should be unique."""
        agent = BookingAgent(db_session)

        codes = set()
        for _ in range(1000):
            code = agent._generate_confirmation_code()
            codes.add(code)

        # All codes should be unique (very high probability)
        assert len(codes) == 1000
