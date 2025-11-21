"""
Layer 4: API Tests - Venue Endpoints

Full integration tests for venue-related API endpoints.
"""
import pytest
from httpx import AsyncClient
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'backend'))


class TestVenueListEndpoint:
    """Test GET /api/v1/venues endpoint."""

    @pytest.mark.layer4
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_list_venues(self, client: AsyncClient, api_v1_prefix, multiple_venues):
        """Should return list of venues."""
        response = await client.get(f"{api_v1_prefix}/venues")

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= len(multiple_venues)

    @pytest.mark.layer4
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_list_venues_with_category_filter(
        self, client: AsyncClient, api_v1_prefix, multiple_venues
    ):
        """Should filter venues by category."""
        response = await client.get(
            f"{api_v1_prefix}/venues",
            params={"category": "restaurant"}
        )

        assert response.status_code == 200
        data = response.json()
        for venue in data:
            assert venue["category"] == "restaurant"

    @pytest.mark.layer4
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_list_venues_pagination(
        self, client: AsyncClient, api_v1_prefix, multiple_venues
    ):
        """Should support pagination."""
        response = await client.get(
            f"{api_v1_prefix}/venues",
            params={"skip": 0, "limit": 2}
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data) <= 2


class TestVenueDetailEndpoint:
    """Test GET /api/v1/venues/{venue_id} endpoint."""

    @pytest.mark.layer4
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_get_venue_by_id(self, client: AsyncClient, api_v1_prefix, sample_venue):
        """Should return venue by ID."""
        response = await client.get(f"{api_v1_prefix}/venues/{sample_venue.id}")

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == sample_venue.name
        assert data["id"] == sample_venue.id

    @pytest.mark.layer4
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_get_venue_not_found(self, client: AsyncClient, api_v1_prefix):
        """Should return 404 for nonexistent venue."""
        response = await client.get(f"{api_v1_prefix}/venues/99999")

        assert response.status_code == 404

    @pytest.mark.layer4
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_venue_response_includes_fields(
        self, client: AsyncClient, api_v1_prefix, sample_venue
    ):
        """Response should include expected fields."""
        response = await client.get(f"{api_v1_prefix}/venues/{sample_venue.id}")

        assert response.status_code == 200
        data = response.json()

        expected_fields = [
            "id", "name", "category", "cuisine_type",
            "rating", "price_level", "latitude", "longitude"
        ]
        for field in expected_fields:
            assert field in data


class TestVenueTrendingEndpoint:
    """Test GET /api/v1/venues/trending endpoint."""

    @pytest.mark.layer4
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_get_trending_venues(self, client: AsyncClient, api_v1_prefix, multiple_venues):
        """Should return trending venues."""
        response = await client.get(f"{api_v1_prefix}/venues/trending")

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    @pytest.mark.layer4
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_trending_venues_limit(self, client: AsyncClient, api_v1_prefix, multiple_venues):
        """Should respect limit parameter."""
        response = await client.get(
            f"{api_v1_prefix}/venues/trending",
            params={"limit": 3}
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data) <= 3


class TestVenueInterestedUsersEndpoint:
    """Test GET /api/v1/venues/{venue_id}/interested endpoint."""

    @pytest.mark.layer4
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_get_interested_users(
        self, client: AsyncClient, api_v1_prefix, multiple_venues, venue_interests
    ):
        """Should return users interested in venue."""
        # Venue 2 (Sushi Palace) has users interested
        response = await client.get(f"{api_v1_prefix}/venues/2/interested")

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    @pytest.mark.layer4
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_interested_users_venue_not_found(
        self, client: AsyncClient, api_v1_prefix
    ):
        """Should handle nonexistent venue."""
        response = await client.get(f"{api_v1_prefix}/venues/99999/interested")

        # Should return 404 or empty list depending on implementation
        assert response.status_code in [200, 404]
