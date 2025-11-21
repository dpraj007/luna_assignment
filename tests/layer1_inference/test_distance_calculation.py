"""
Layer 1: Inference Tests - Distance Calculation (Haversine Formula)

Tests the spatial analysis component of the recommendation engine.
"""
import pytest
import math

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'backend'))

from backend.app.services.recommendation import RecommendationEngine


class TestHaversineDistance:
    """Test the Haversine distance calculation."""

    @pytest.mark.layer1
    @pytest.mark.unit
    def test_same_location_returns_zero(self):
        """Distance between same point should be 0."""
        distance = RecommendationEngine.haversine_distance(
            40.7128, -74.0060,  # NYC
            40.7128, -74.0060   # Same location
        )
        assert distance == 0.0

    @pytest.mark.layer1
    @pytest.mark.unit
    def test_known_distance_nyc_to_brooklyn(self):
        """Test known distance: Manhattan to Brooklyn (~9-10 km)."""
        distance = RecommendationEngine.haversine_distance(
            40.7580, -73.9855,  # Times Square
            40.6782, -73.9442   # Brooklyn (Downtown)
        )
        # Distance should be approximately 9-10 km
        assert 8.0 <= distance <= 11.0, f"Expected ~9-10km, got {distance}km"

    @pytest.mark.layer1
    @pytest.mark.unit
    def test_known_distance_nyc_to_la(self):
        """Test known distance: NYC to LA (~3940 km)."""
        distance = RecommendationEngine.haversine_distance(
            40.7128, -74.0060,  # NYC
            34.0522, -118.2437  # LA
        )
        # Distance should be approximately 3940 km
        assert 3900 <= distance <= 4000, f"Expected ~3940km, got {distance}km"

    @pytest.mark.layer1
    @pytest.mark.unit
    def test_known_distance_london_to_paris(self):
        """Test known distance: London to Paris (~344 km)."""
        distance = RecommendationEngine.haversine_distance(
            51.5074, -0.1278,  # London
            48.8566, 2.3522    # Paris
        )
        # Distance should be approximately 340-350 km
        assert 340 <= distance <= 350, f"Expected ~344km, got {distance}km"

    @pytest.mark.layer1
    @pytest.mark.unit
    def test_distance_symmetry(self):
        """Distance from A to B should equal distance from B to A."""
        lat1, lon1 = 40.7128, -74.0060  # NYC
        lat2, lon2 = 34.0522, -118.2437  # LA

        distance_ab = RecommendationEngine.haversine_distance(lat1, lon1, lat2, lon2)
        distance_ba = RecommendationEngine.haversine_distance(lat2, lon2, lat1, lon1)

        assert abs(distance_ab - distance_ba) < 0.001

    @pytest.mark.layer1
    @pytest.mark.unit
    def test_equator_crossing(self):
        """Test distance calculation across the equator."""
        distance = RecommendationEngine.haversine_distance(
            10.0, 0.0,   # 10 degrees north
            -10.0, 0.0   # 10 degrees south
        )
        # 20 degrees of latitude ≈ 2222 km
        assert 2200 <= distance <= 2250, f"Expected ~2222km, got {distance}km"

    @pytest.mark.layer1
    @pytest.mark.unit
    def test_international_date_line(self):
        """Test distance calculation across the international date line."""
        distance = RecommendationEngine.haversine_distance(
            0.0, 179.0,   # Just west of date line
            0.0, -179.0   # Just east of date line
        )
        # Should be about 222 km (2 degrees of longitude at equator)
        assert 200 <= distance <= 250, f"Expected ~222km, got {distance}km"

    @pytest.mark.layer1
    @pytest.mark.unit
    def test_short_distance_accuracy(self):
        """Test accuracy for very short distances (within city)."""
        # Times Square to Empire State Building (~1 km)
        distance = RecommendationEngine.haversine_distance(
            40.7580, -73.9855,  # Times Square
            40.7484, -73.9857   # Empire State Building
        )
        assert 1.0 <= distance <= 1.5, f"Expected ~1km, got {distance}km"

    @pytest.mark.layer1
    @pytest.mark.unit
    def test_antipodal_points(self):
        """Test distance between antipodal points (opposite sides of Earth)."""
        distance = RecommendationEngine.haversine_distance(
            0.0, 0.0,
            0.0, 180.0
        )
        # Half Earth circumference ≈ 20,015 km
        assert 20000 <= distance <= 20050, f"Expected ~20015km, got {distance}km"

    @pytest.mark.layer1
    @pytest.mark.unit
    def test_negative_coordinates(self):
        """Test with negative latitude and longitude."""
        # Sydney to São Paulo
        distance = RecommendationEngine.haversine_distance(
            -33.8688, 151.2093,  # Sydney
            -23.5505, -46.6333   # São Paulo
        )
        # Distance should be approximately 13,500 km
        assert 13000 <= distance <= 14000, f"Expected ~13500km, got {distance}km"

    @pytest.mark.layer1
    @pytest.mark.unit
    def test_polar_distance(self):
        """Test distance near the poles."""
        # North Pole to a point 1 degree away
        distance = RecommendationEngine.haversine_distance(
            90.0, 0.0,    # North Pole
            89.0, 0.0     # 1 degree south
        )
        # 1 degree of latitude ≈ 111 km
        assert 110 <= distance <= 112, f"Expected ~111km, got {distance}km"

    @pytest.mark.layer1
    @pytest.mark.unit
    @pytest.mark.parametrize("lat1,lon1,lat2,lon2,expected_min,expected_max", [
        (40.7128, -74.0060, 40.7128, -74.0060, 0, 0.001),  # Same point
        (40.7580, -73.9855, 40.7484, -73.9857, 0.9, 1.5),  # ~1km
        (40.7128, -74.0060, 34.0522, -118.2437, 3900, 4000),  # NYC-LA
    ])
    def test_parametrized_distances(self, lat1, lon1, lat2, lon2, expected_min, expected_max):
        """Parametrized test for various known distances."""
        distance = RecommendationEngine.haversine_distance(lat1, lon1, lat2, lon2)
        assert expected_min <= distance <= expected_max


class TestDistanceEdgeCases:
    """Test edge cases and boundary conditions."""

    @pytest.mark.layer1
    @pytest.mark.unit
    def test_zero_latitude(self):
        """Test with zero latitude (equator)."""
        distance = RecommendationEngine.haversine_distance(
            0.0, -74.0060,
            0.0, -73.0060
        )
        # 1 degree of longitude at equator ≈ 111 km
        assert 105 <= distance <= 115

    @pytest.mark.layer1
    @pytest.mark.unit
    def test_zero_longitude(self):
        """Test with zero longitude (prime meridian)."""
        distance = RecommendationEngine.haversine_distance(
            40.0, 0.0,
            41.0, 0.0
        )
        # 1 degree of latitude ≈ 111 km
        assert 110 <= distance <= 112

    @pytest.mark.layer1
    @pytest.mark.unit
    def test_max_latitude(self):
        """Test with maximum latitude values."""
        distance = RecommendationEngine.haversine_distance(
            90.0, 0.0,   # North Pole
            -90.0, 0.0   # South Pole
        )
        # Distance should be approximately 20,015 km (half circumference)
        assert 20000 <= distance <= 20050

    @pytest.mark.layer1
    @pytest.mark.unit
    def test_max_longitude(self):
        """Test with maximum longitude values."""
        distance = RecommendationEngine.haversine_distance(
            0.0, 180.0,
            0.0, -180.0
        )
        # Same point (180 and -180 are the same)
        assert distance < 1  # Should be essentially 0


class TestDistancePerformance:
    """Performance tests for distance calculation."""

    @pytest.mark.layer1
    @pytest.mark.unit
    def test_many_calculations(self):
        """Test that many calculations complete quickly."""
        import time

        start = time.time()
        for _ in range(10000):
            RecommendationEngine.haversine_distance(
                40.7128, -74.0060,
                34.0522, -118.2437
            )
        elapsed = time.time() - start

        # Should complete 10000 calculations in under 1 second
        assert elapsed < 1.0, f"10000 calculations took {elapsed}s"
