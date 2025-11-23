"""
Layer 3: Backend Tests - Booking Model

Tests for booking-related database models.
"""
import pytest
from datetime import datetime, timedelta
from sqlalchemy import select
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..', 'backend'))

from backend.app.models.booking import Booking, BookingStatus, BookingInvitation


class TestBookingModel:
    """Test Booking model CRUD operations."""

    @pytest.mark.layer3
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_create_booking(self, db_session, sample_user, sample_venue):
        """Should create a booking successfully."""
        booking = Booking(
            user_id=sample_user.id,
            venue_id=sample_venue.id,
            booking_time=datetime.utcnow() + timedelta(days=1),
            party_size=4,
            confirmation_code="TEST1234",
        )
        db_session.add(booking)
        await db_session.commit()
        await db_session.refresh(booking)

        assert booking.id is not None
        assert booking.confirmation_code == "TEST1234"
        assert booking.created_at is not None

    @pytest.mark.layer3
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_booking_default_values(self, db_session, sample_user, sample_venue):
        """Booking should have expected default values."""
        booking = Booking(
            user_id=sample_user.id,
            venue_id=sample_venue.id,
            booking_time=datetime.utcnow() + timedelta(days=1),
            party_size=2,
        )
        db_session.add(booking)
        await db_session.commit()
        await db_session.refresh(booking)

        assert booking.status == BookingStatus.PENDING
        assert booking.duration_minutes == 90

    @pytest.mark.layer3
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_booking_status_transitions(self, db_session, sample_user, sample_venue):
        """Booking status should be updatable."""
        booking = Booking(
            user_id=sample_user.id,
            venue_id=sample_venue.id,
            booking_time=datetime.utcnow() + timedelta(days=1),
            party_size=2,
            status=BookingStatus.PENDING,
        )
        db_session.add(booking)
        await db_session.commit()

        # Confirm booking
        booking.status = BookingStatus.CONFIRMED
        await db_session.commit()
        await db_session.refresh(booking)
        assert booking.status == BookingStatus.CONFIRMED

        # Cancel booking
        booking.status = BookingStatus.CANCELLED
        await db_session.commit()
        await db_session.refresh(booking)
        assert booking.status == BookingStatus.CANCELLED

    @pytest.mark.layer3
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_booking_with_group_members(self, db_session, sample_user, sample_venue, multiple_users):
        """Booking should store group members as JSON."""
        group_ids = [u.id for u in multiple_users[:3]]

        booking = Booking(
            user_id=sample_user.id,
            venue_id=sample_venue.id,
            booking_time=datetime.utcnow() + timedelta(days=1),
            party_size=4,
            group_members=group_ids,
        )
        db_session.add(booking)
        await db_session.commit()
        await db_session.refresh(booking)

        assert booking.group_members == group_ids
        assert len(booking.group_members) == 3

    @pytest.mark.layer3
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_booking_special_requests(self, db_session, sample_user, sample_venue):
        """Booking should store special requests."""
        booking = Booking(
            user_id=sample_user.id,
            venue_id=sample_venue.id,
            booking_time=datetime.utcnow() + timedelta(days=1),
            party_size=2,
            special_requests="Window seat please, celebrating anniversary",
        )
        db_session.add(booking)
        await db_session.commit()
        await db_session.refresh(booking)

        assert "Window seat" in booking.special_requests
        assert "anniversary" in booking.special_requests

    @pytest.mark.layer3
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_booking_relationships(self, db_session, sample_user, sample_venue):
        """Booking should have user and venue relationships."""
        booking = Booking(
            user_id=sample_user.id,
            venue_id=sample_venue.id,
            booking_time=datetime.utcnow() + timedelta(days=1),
            party_size=2,
        )
        db_session.add(booking)
        await db_session.commit()

        # Query with relationships
        query = select(Booking).where(Booking.id == booking.id)
        result = await db_session.execute(query)
        loaded_booking = result.scalar_one()

        assert loaded_booking.user_id == sample_user.id
        assert loaded_booking.venue_id == sample_venue.id

    @pytest.mark.layer3
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_filter_bookings_by_user(self, db_session, sample_user, sample_venue):
        """Should filter bookings by user."""
        # Create multiple bookings
        for i in range(3):
            booking = Booking(
                user_id=sample_user.id,
                venue_id=sample_venue.id,
                booking_time=datetime.utcnow() + timedelta(days=i+1),
                party_size=2,
            )
            db_session.add(booking)

        await db_session.commit()

        query = select(Booking).where(Booking.user_id == sample_user.id)
        result = await db_session.execute(query)
        bookings = result.scalars().all()

        assert len(bookings) == 3

    @pytest.mark.layer3
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_filter_bookings_by_status(self, db_session, sample_user, sample_venue):
        """Should filter bookings by status."""
        statuses = [BookingStatus.PENDING, BookingStatus.CONFIRMED, BookingStatus.CANCELLED]

        for status in statuses:
            booking = Booking(
                user_id=sample_user.id,
                venue_id=sample_venue.id,
                booking_time=datetime.utcnow() + timedelta(days=1),
                party_size=2,
                status=status,
            )
            db_session.add(booking)

        await db_session.commit()

        query = select(Booking).where(Booking.status == BookingStatus.CONFIRMED)
        result = await db_session.execute(query)
        confirmed = result.scalars().all()

        assert len(confirmed) == 1
        assert confirmed[0].status == BookingStatus.CONFIRMED


class TestBookingInvitationModel:
    """Test BookingInvitation model."""

    @pytest.mark.layer3
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_create_invitation(self, db_session, sample_booking, multiple_users):
        """Should create a booking invitation."""
        invitation = BookingInvitation(
            booking_id=sample_booking.id,
            inviter_id=sample_booking.user_id,
            invitee_id=multiple_users[0].id,
            message="Join us for dinner!",
        )
        db_session.add(invitation)
        await db_session.commit()
        await db_session.refresh(invitation)

        assert invitation.id is not None
        assert invitation.status == "pending"
        assert invitation.message == "Join us for dinner!"

    @pytest.mark.layer3
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_invitation_response(self, db_session, sample_booking, multiple_users):
        """Should update invitation response."""
        invitation = BookingInvitation(
            booking_id=sample_booking.id,
            inviter_id=sample_booking.user_id,
            invitee_id=multiple_users[0].id,
        )
        db_session.add(invitation)
        await db_session.commit()

        # Accept invitation
        invitation.status = "accepted"
        invitation.responded_at = datetime.utcnow()
        await db_session.commit()
        await db_session.refresh(invitation)

        assert invitation.status == "accepted"
        assert invitation.responded_at is not None

    @pytest.mark.layer3
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_invitation_decline(self, db_session, sample_booking, multiple_users):
        """Should handle declined invitation."""
        invitation = BookingInvitation(
            booking_id=sample_booking.id,
            inviter_id=sample_booking.user_id,
            invitee_id=multiple_users[0].id,
        )
        db_session.add(invitation)
        await db_session.commit()

        # Decline invitation
        invitation.status = "declined"
        invitation.responded_at = datetime.utcnow()
        await db_session.commit()
        await db_session.refresh(invitation)

        assert invitation.status == "declined"

    @pytest.mark.layer3
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_multiple_invitations_per_booking(self, db_session, sample_booking, multiple_users):
        """Booking can have multiple invitations."""
        for user in multiple_users[:3]:
            invitation = BookingInvitation(
                booking_id=sample_booking.id,
                inviter_id=sample_booking.user_id,
                invitee_id=user.id,
            )
            db_session.add(invitation)

        await db_session.commit()

        query = select(BookingInvitation).where(
            BookingInvitation.booking_id == sample_booking.id
        )
        result = await db_session.execute(query)
        invitations = result.scalars().all()

        assert len(invitations) == 3


class TestBookingStatusEnum:
    """Test BookingStatus enum."""

    @pytest.mark.layer3
    @pytest.mark.unit
    def test_all_statuses_defined(self):
        """All expected statuses should be defined."""
        expected = ["PENDING", "CONFIRMED", "CANCELLED", "COMPLETED", "NO_SHOW"]

        for status in expected:
            assert hasattr(BookingStatus, status)

    @pytest.mark.layer3
    @pytest.mark.unit
    def test_status_values_are_lowercase(self):
        """Status values should be lowercase strings."""
        assert BookingStatus.PENDING.value == "pending"
        assert BookingStatus.CONFIRMED.value == "confirmed"
        assert BookingStatus.CANCELLED.value == "cancelled"
