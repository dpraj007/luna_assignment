"""
Layer 4: API Tests - Booking Endpoints

Full integration tests for booking-related API endpoints.
"""
import pytest
from datetime import datetime, timedelta
from httpx import AsyncClient
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'backend'))


class TestCreateBookingEndpoint:
    """Test POST /api/v1/bookings endpoint."""

    @pytest.mark.layer4
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_create_booking(
        self, client: AsyncClient, api_v1_prefix,
        sample_user, sample_venue
    ):
        """Should create a booking successfully."""
        booking_time = (datetime.utcnow() + timedelta(days=1)).isoformat()

        response = await client.post(
            f"{api_v1_prefix}/bookings/{sample_user.id}/create",
            json={
                "venue_id": sample_venue.id,
                "party_size": 4,
                "preferred_time": booking_time,
            }
        )

        assert response.status_code in [200, 201]
        data = response.json()
        assert "booking_id" in data or "id" in data or "success" in data

    @pytest.mark.layer4
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_create_booking_invalid_user(
        self, client: AsyncClient, api_v1_prefix, sample_venue
    ):
        """Should reject booking for nonexistent user."""
        booking_time = (datetime.utcnow() + timedelta(days=1)).isoformat()

        response = await client.post(
            f"{api_v1_prefix}/bookings/99999/create",
            json={
                "venue_id": sample_venue.id,
                "party_size": 4,
                "preferred_time": booking_time,
            }
        )

        assert response.status_code in [404, 422, 400]

    @pytest.mark.layer4
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_create_booking_invalid_venue(
        self, client: AsyncClient, api_v1_prefix, sample_user
    ):
        """Should reject booking for nonexistent venue."""
        booking_time = (datetime.utcnow() + timedelta(days=1)).isoformat()

        response = await client.post(
            f"{api_v1_prefix}/bookings/{sample_user.id}/create",
            json={
                "venue_id": 99999,
                "party_size": 4,
                "preferred_time": booking_time,
            }
        )

        assert response.status_code in [404, 422, 400]

    @pytest.mark.layer4
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_create_booking_with_group(
        self, client: AsyncClient, api_v1_prefix,
        sample_user, sample_venue, multiple_users
    ):
        """Should create booking with group members."""
        booking_time = (datetime.utcnow() + timedelta(days=1)).isoformat()
        group_ids = [u.id for u in multiple_users[:2]]

        response = await client.post(
            f"{api_v1_prefix}/bookings/{sample_user.id}/create",
            json={
                "venue_id": sample_venue.id,
                "party_size": 3,
                "preferred_time": booking_time,
                "group_members": group_ids,
            }
        )

        assert response.status_code in [200, 201]


class TestListBookingsEndpoint:
    """Test GET /api/v1/bookings endpoint."""

    @pytest.mark.layer4
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_list_bookings(
        self, client: AsyncClient, api_v1_prefix, sample_booking
    ):
        """Should return list of bookings."""
        response = await client.get(f"{api_v1_prefix}/bookings/")

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    @pytest.mark.layer4
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_list_bookings_by_user(
        self, client: AsyncClient, api_v1_prefix, sample_booking
    ):
        """Should filter bookings by user."""
        response = await client.get(
            f"{api_v1_prefix}/bookings/user/{sample_booking.user_id}"
        )

        assert response.status_code == 200
        data = response.json()
        for booking in data:
            assert booking["user_id"] == sample_booking.user_id


class TestBookingDetailEndpoint:
    """Test GET /api/v1/bookings/{booking_id} endpoint."""

    @pytest.mark.layer4
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_get_booking_by_id(
        self, client: AsyncClient, api_v1_prefix, sample_booking
    ):
        """Should return booking by ID."""
        response = await client.get(f"{api_v1_prefix}/bookings/{sample_booking.id}")

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == sample_booking.id

    @pytest.mark.layer4
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_get_booking_not_found(
        self, client: AsyncClient, api_v1_prefix
    ):
        """Should return 404 for nonexistent booking."""
        response = await client.get(f"{api_v1_prefix}/bookings/99999")

        assert response.status_code == 404


class TestCancelBookingEndpoint:
    """Test POST /api/v1/bookings/{booking_id}/cancel endpoint."""

    @pytest.mark.layer4
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_cancel_booking(
        self, client: AsyncClient, api_v1_prefix, sample_booking
    ):
        """Should cancel booking."""
        response = await client.post(f"{api_v1_prefix}/bookings/{sample_booking.id}/cancel")

        assert response.status_code in [200, 204]

    @pytest.mark.layer4
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_cancel_nonexistent_booking(
        self, client: AsyncClient, api_v1_prefix
    ):
        """Should return 404 for nonexistent booking."""
        response = await client.post(f"{api_v1_prefix}/bookings/99999/cancel")

        assert response.status_code == 404


class TestAutoBookEndpoint:
    """Test POST /api/v1/bookings/venue/{venue_id}/auto-book endpoint."""

    @pytest.mark.layer4
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_auto_book_interested_users(
        self, client: AsyncClient, api_v1_prefix,
        multiple_venues, venue_interests
    ):
        """Should auto-book interested users."""
        # Venue 2 has multiple users interested
        response = await client.post(
            f"{api_v1_prefix}/bookings/venue/2/auto-book"
        )

        assert response.status_code in [200, 201]
        data = response.json()
        assert isinstance(data, (list, dict))

    @pytest.mark.layer4
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_auto_book_no_interested_users(
        self, client: AsyncClient, api_v1_prefix, sample_venue
    ):
        """Should handle venue with no interested users."""
        response = await client.post(
            f"{api_v1_prefix}/bookings/venue/{sample_venue.id}/auto-book"
        )

        assert response.status_code in [200, 201]
        data = response.json()
        # Should return empty list or indicate no bookings created
        assert isinstance(data, (list, dict))
