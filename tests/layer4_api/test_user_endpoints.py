"""
Layer 4: API Tests - User Endpoints

Full integration tests for user-related API endpoints.
"""
import pytest
from httpx import AsyncClient
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'backend'))


class TestUserListEndpoint:
    """Test GET /api/v1/users endpoint."""

    @pytest.mark.layer4
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_list_users_empty(self, client: AsyncClient, api_v1_prefix):
        """Should return empty list when no users."""
        response = await client.get(f"{api_v1_prefix}/users")

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    @pytest.mark.layer4
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_list_users_with_data(self, client: AsyncClient, api_v1_prefix, multiple_users):
        """Should return list of users."""
        response = await client.get(f"{api_v1_prefix}/users")

        assert response.status_code == 200
        data = response.json()
        assert len(data) >= len(multiple_users)

    @pytest.mark.layer4
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_list_users_pagination(self, client: AsyncClient, api_v1_prefix, multiple_users):
        """Should support pagination parameters."""
        response = await client.get(
            f"{api_v1_prefix}/users",
            params={"skip": 0, "limit": 2}
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data) <= 2


class TestUserDetailEndpoint:
    """Test GET /api/v1/users/{user_id} endpoint."""

    @pytest.mark.layer4
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_get_user_by_id(self, client: AsyncClient, api_v1_prefix, sample_user):
        """Should return user by ID."""
        response = await client.get(f"{api_v1_prefix}/users/{sample_user.id}")

        assert response.status_code == 200
        data = response.json()
        assert data["username"] == sample_user.username
        assert data["email"] == sample_user.email

    @pytest.mark.layer4
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_get_user_not_found(self, client: AsyncClient, api_v1_prefix):
        """Should return 404 for nonexistent user."""
        response = await client.get(f"{api_v1_prefix}/users/99999")

        assert response.status_code == 404

    @pytest.mark.layer4
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_get_user_response_fields(self, client: AsyncClient, api_v1_prefix, sample_user):
        """Response should include expected fields."""
        response = await client.get(f"{api_v1_prefix}/users/{sample_user.id}")

        assert response.status_code == 200
        data = response.json()

        expected_fields = ["id", "email", "username"]
        for field in expected_fields:
            assert field in data


class TestUserPreferencesEndpoint:
    """Test /api/v1/users/{user_id}/preferences endpoints."""

    @pytest.mark.layer4
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_get_user_preferences(
        self, client: AsyncClient, api_v1_prefix, sample_user_with_preferences
    ):
        """Should return user preferences."""
        user, prefs = sample_user_with_preferences

        response = await client.get(f"{api_v1_prefix}/users/{user.id}/preferences")

        assert response.status_code == 200
        data = response.json()
        assert "cuisine_preferences" in data

    @pytest.mark.layer4
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_get_preferences_user_not_found(self, client: AsyncClient, api_v1_prefix):
        """Should return 404 for nonexistent user."""
        response = await client.get(f"{api_v1_prefix}/users/99999/preferences")

        assert response.status_code == 404


class TestUserFriendsEndpoint:
    """Test /api/v1/users/{user_id}/friends endpoint."""

    @pytest.mark.layer4
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_get_user_friends(
        self, client: AsyncClient, api_v1_prefix, users_with_friendships
    ):
        """Should return user's friends."""
        users, _ = users_with_friendships
        alice = users[0]

        response = await client.get(f"{api_v1_prefix}/users/{alice.id}/friends")

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    @pytest.mark.layer4
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_get_friends_empty_list(self, client: AsyncClient, api_v1_prefix, sample_user):
        """Should return empty list for user without friends."""
        response = await client.get(f"{api_v1_prefix}/users/{sample_user.id}/friends")

        assert response.status_code == 200
        data = response.json()
        assert data == [] or isinstance(data, list)
