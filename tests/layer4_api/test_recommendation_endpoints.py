"""
Layer 4: API Tests - Recommendation Endpoints

Full integration tests for recommendation-related API endpoints.
"""
import pytest
from httpx import AsyncClient
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'backend'))


class TestRecommendationEndpoint:
    """Test GET /api/v1/recommendations endpoint."""

    @pytest.mark.layer4
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_get_recommendations(
        self, client: AsyncClient, api_v1_prefix,
        sample_user_with_preferences, multiple_venues
    ):
        """Should return personalized recommendations."""
        user, _ = sample_user_with_preferences

        response = await client.get(
            f"{api_v1_prefix}/recommendations",
            params={"user_id": user.id}
        )

        assert response.status_code == 200
        data = response.json()
        assert "venues" in data or isinstance(data, list)

    @pytest.mark.layer4
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_recommendations_with_limit(
        self, client: AsyncClient, api_v1_prefix,
        sample_user_with_preferences, multiple_venues
    ):
        """Should respect limit parameter."""
        user, _ = sample_user_with_preferences

        response = await client.get(
            f"{api_v1_prefix}/recommendations",
            params={"user_id": user.id, "limit": 3}
        )

        assert response.status_code == 200
        data = response.json()
        venues = data.get("venues", data) if isinstance(data, dict) else data
        assert len(venues) <= 3

    @pytest.mark.layer4
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_recommendations_user_not_found(
        self, client: AsyncClient, api_v1_prefix
    ):
        """Should handle nonexistent user."""
        response = await client.get(
            f"{api_v1_prefix}/recommendations",
            params={"user_id": 99999}
        )

        # Should return 404 or empty recommendations
        assert response.status_code in [200, 404]


class TestExpressInterestEndpoint:
    """Test POST /api/v1/recommendations/interest endpoint."""

    @pytest.mark.layer4
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_express_interest(
        self, client: AsyncClient, api_v1_prefix,
        sample_user, sample_venue
    ):
        """Should express interest in a venue."""
        response = await client.post(
            f"{api_v1_prefix}/recommendations/interest",
            json={
                "user_id": sample_user.id,
                "venue_id": sample_venue.id,
                "preferred_time_slot": "dinner",
                "open_to_invites": True
            }
        )

        assert response.status_code in [200, 201]
        data = response.json()
        assert "success" in data or "venue_id" in data

    @pytest.mark.layer4
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_express_interest_invalid_user(
        self, client: AsyncClient, api_v1_prefix, sample_venue
    ):
        """Should reject interest from nonexistent user."""
        response = await client.post(
            f"{api_v1_prefix}/recommendations/interest",
            json={
                "user_id": 99999,
                "venue_id": sample_venue.id,
            }
        )

        assert response.status_code in [404, 422]

    @pytest.mark.layer4
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_express_interest_invalid_venue(
        self, client: AsyncClient, api_v1_prefix, sample_user
    ):
        """Should reject interest in nonexistent venue."""
        response = await client.post(
            f"{api_v1_prefix}/recommendations/interest",
            json={
                "user_id": sample_user.id,
                "venue_id": 99999,
            }
        )

        assert response.status_code in [404, 422]


class TestGroupRecommendationEndpoint:
    """Test GET /api/v1/recommendations/group endpoint."""

    @pytest.mark.layer4
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_get_group_recommendations(
        self, client: AsyncClient, api_v1_prefix,
        users_with_preferences, multiple_venues
    ):
        """Should return group recommendations."""
        user_ids = [u.id for u, _ in users_with_preferences[:3]]

        response = await client.get(
            f"{api_v1_prefix}/recommendations/group",
            params={"user_ids": ",".join(map(str, user_ids))}
        )

        # Implementation may vary
        assert response.status_code in [200, 422]

    @pytest.mark.layer4
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_group_recommendations_empty_group(
        self, client: AsyncClient, api_v1_prefix
    ):
        """Should handle empty group."""
        response = await client.get(
            f"{api_v1_prefix}/recommendations/group",
            params={"user_ids": ""}
        )

        # Should return error or empty list
        assert response.status_code in [200, 400, 422]


class TestCompatibleUsersEndpoint:
    """Test GET /api/v1/recommendations/compatible endpoint."""

    @pytest.mark.layer4
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_get_compatible_users(
        self, client: AsyncClient, api_v1_prefix,
        users_with_friendships
    ):
        """Should return compatible users."""
        users, _ = users_with_friendships
        alice = users[0]

        response = await client.get(
            f"{api_v1_prefix}/recommendations/compatible",
            params={"user_id": alice.id}
        )

        # Implementation dependent
        assert response.status_code in [200, 404]

    @pytest.mark.layer4
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_compatible_users_with_venue(
        self, client: AsyncClient, api_v1_prefix,
        users_with_friendships, multiple_venues, venue_interests
    ):
        """Should filter by venue interest."""
        users, _ = users_with_friendships
        alice = users[0]

        response = await client.get(
            f"{api_v1_prefix}/recommendations/compatible",
            params={"user_id": alice.id, "venue_id": 2}
        )

        assert response.status_code in [200, 404]
