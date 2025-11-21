"""
Environment Service.

Simulates environmental factors including:
- Weather conditions
- Traffic conditions
- Venue availability
- Special events (concerts, sports, festivals)
"""
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from dataclasses import dataclass
import random
import math
import logging

logger = logging.getLogger(__name__)


@dataclass
class WeatherCondition:
    """Weather condition data."""
    condition: str  # sunny, cloudy, rainy, snow, windy
    temperature: float  # Fahrenheit
    humidity: float  # 0-100
    precipitation: float  # 0-1 probability
    wind_speed: float  # mph


@dataclass
class TrafficCondition:
    """Traffic condition data."""
    level: str  # low, medium, high, severe
    delay_minutes: float
    congestion_factor: float  # 1.0 = normal, >1.0 = slower


@dataclass
class SpecialEvent:
    """Special event data."""
    event_type: str  # concert, sports, festival, convention
    name: str
    location: Dict[str, float]  # lat, lon
    impact_radius_km: float
    start_time: datetime
    end_time: datetime
    expected_attendance: int


class EnvironmentService:
    """
    Service for simulating environmental conditions.

    Provides deterministic or seeded random environmental data
    for simulation purposes.
    """

    # Weather patterns by season
    SEASONAL_WEATHER = {
        "winter": {
            "conditions": ["sunny", "cloudy", "snow", "cloudy"],
            "temp_range": (25, 45),
            "humidity_range": (30, 60),
        },
        "spring": {
            "conditions": ["sunny", "cloudy", "rainy", "sunny"],
            "temp_range": (45, 70),
            "humidity_range": (40, 70),
        },
        "summer": {
            "conditions": ["sunny", "sunny", "cloudy", "rainy"],
            "temp_range": (70, 95),
            "humidity_range": (50, 80),
        },
        "fall": {
            "conditions": ["sunny", "cloudy", "rainy", "cloudy"],
            "temp_range": (45, 70),
            "humidity_range": (40, 65),
        },
    }

    # Traffic patterns by hour (0-23)
    TRAFFIC_PATTERNS = {
        # Rush hours
        7: {"level": "high", "factor": 1.8},
        8: {"level": "high", "factor": 2.0},
        9: {"level": "medium", "factor": 1.5},
        17: {"level": "high", "factor": 2.0},
        18: {"level": "high", "factor": 1.8},
        19: {"level": "medium", "factor": 1.4},
        # Lunch
        12: {"level": "medium", "factor": 1.3},
        13: {"level": "medium", "factor": 1.2},
        # Late night
        22: {"level": "low", "factor": 0.8},
        23: {"level": "low", "factor": 0.7},
        0: {"level": "low", "factor": 0.6},
        1: {"level": "low", "factor": 0.5},
    }

    # Sample special events
    SAMPLE_EVENTS = [
        {
            "event_type": "concert",
            "name": "Summer Music Festival",
            "location": {"lat": 40.7580, "lon": -73.9855},  # Times Square area
            "impact_radius_km": 2.0,
            "duration_hours": 4,
            "expected_attendance": 5000,
        },
        {
            "event_type": "sports",
            "name": "Basketball Game",
            "location": {"lat": 40.7505, "lon": -73.9934},  # MSG area
            "impact_radius_km": 1.5,
            "duration_hours": 3,
            "expected_attendance": 20000,
        },
        {
            "event_type": "festival",
            "name": "Food & Wine Festival",
            "location": {"lat": 40.7128, "lon": -74.0060},  # Downtown
            "impact_radius_km": 1.0,
            "duration_hours": 6,
            "expected_attendance": 3000,
        },
    ]

    def __init__(self, seed: Optional[int] = None):
        """
        Initialize the environment service.

        Args:
            seed: Optional random seed for reproducible results
        """
        self.seed = seed
        if seed:
            random.seed(seed)

        self._active_events: List[SpecialEvent] = []

    def get_weather(
        self,
        location: Dict[str, float],
        time: datetime
    ) -> WeatherCondition:
        """
        Get weather conditions for a location and time.

        Args:
            location: Dict with 'lat' and 'lon' keys
            time: The datetime to get weather for

        Returns:
            WeatherCondition with current weather data
        """
        # Determine season
        month = time.month
        if month in [12, 1, 2]:
            season = "winter"
        elif month in [3, 4, 5]:
            season = "spring"
        elif month in [6, 7, 8]:
            season = "summer"
        else:
            season = "fall"

        seasonal = self.SEASONAL_WEATHER[season]

        # Use time-based seed for consistency within the same hour
        hour_seed = int(time.timestamp() // 3600)
        random.seed(hour_seed)

        # Select condition
        condition = random.choice(seasonal["conditions"])

        # Generate temperature (varies by hour)
        temp_min, temp_max = seasonal["temp_range"]
        hour = time.hour

        # Temperature peaks around 2-3 PM
        temp_modifier = math.sin((hour - 6) * math.pi / 12) * 10
        base_temp = (temp_min + temp_max) / 2
        temperature = base_temp + temp_modifier + random.uniform(-5, 5)
        temperature = max(temp_min, min(temp_max, temperature))

        # Humidity
        humidity_min, humidity_max = seasonal["humidity_range"]
        humidity = random.uniform(humidity_min, humidity_max)

        # Precipitation probability
        precipitation = 0.0
        if condition == "rainy":
            precipitation = random.uniform(0.3, 0.8)
        elif condition == "snow":
            precipitation = random.uniform(0.2, 0.6)
        elif condition == "cloudy":
            precipitation = random.uniform(0.0, 0.2)

        # Wind speed
        wind_speed = random.uniform(0, 15)
        if condition in ["rainy", "snow"]:
            wind_speed += random.uniform(5, 15)

        # Reset random if we had a seed
        if self.seed:
            random.seed(self.seed)

        return WeatherCondition(
            condition=condition,
            temperature=round(temperature, 1),
            humidity=round(humidity, 1),
            precipitation=round(precipitation, 2),
            wind_speed=round(wind_speed, 1),
        )

    def get_traffic(
        self,
        location: Dict[str, float],
        time: datetime
    ) -> TrafficCondition:
        """
        Get traffic conditions for a location and time.

        Args:
            location: Dict with 'lat' and 'lon' keys
            time: The datetime to get traffic for

        Returns:
            TrafficCondition with current traffic data
        """
        hour = time.hour
        day_of_week = time.weekday()

        # Get base traffic pattern
        pattern = self.TRAFFIC_PATTERNS.get(
            hour,
            {"level": "medium", "factor": 1.0}
        )

        level = pattern["level"]
        factor = pattern["factor"]

        # Weekends have less traffic
        if day_of_week >= 5:  # Saturday, Sunday
            if level == "high":
                level = "medium"
            factor *= 0.7

        # Calculate delay
        base_delay = 5  # 5 minutes base
        delay_minutes = base_delay * factor

        # Add some randomness
        delay_minutes += random.uniform(-2, 5)
        delay_minutes = max(0, delay_minutes)

        return TrafficCondition(
            level=level,
            delay_minutes=round(delay_minutes, 1),
            congestion_factor=round(factor, 2),
        )

    def get_venue_availability(
        self,
        venue_id: int,
        time: datetime,
        base_capacity: int = 50
    ) -> Dict[str, Any]:
        """
        Get venue availability for a specific venue and time.

        Args:
            venue_id: The venue ID
            time: The datetime to check
            base_capacity: Base venue capacity

        Returns:
            Dict with availability info
        """
        hour = time.hour
        day_of_week = time.weekday()
        is_weekend = day_of_week >= 5

        # Base occupancy varies by time
        if 11 <= hour <= 14:  # Lunch
            occupancy_rate = 0.7 + random.uniform(0, 0.2)
        elif 18 <= hour <= 21:  # Dinner
            occupancy_rate = 0.8 + random.uniform(0, 0.15)
        elif 7 <= hour <= 10:  # Breakfast
            occupancy_rate = 0.4 + random.uniform(0, 0.2)
        else:
            occupancy_rate = 0.3 + random.uniform(0, 0.3)

        # Weekends are busier
        if is_weekend:
            occupancy_rate *= 1.2

        occupancy_rate = min(0.95, occupancy_rate)

        # Calculate available slots
        occupied = int(base_capacity * occupancy_rate)
        available = base_capacity - occupied

        # Estimate wait time
        if available > 10:
            wait_time = 0
        elif available > 5:
            wait_time = random.randint(5, 15)
        elif available > 0:
            wait_time = random.randint(15, 30)
        else:
            wait_time = random.randint(30, 60)

        return {
            "venue_id": venue_id,
            "available": available > 0,
            "slots_remaining": available,
            "capacity": base_capacity,
            "occupancy_rate": round(occupancy_rate, 2),
            "wait_time_minutes": wait_time,
            "checked_at": time.isoformat(),
        }

    def get_special_events(
        self,
        location: Dict[str, float],
        time: datetime,
        radius_km: float = 5.0
    ) -> List[SpecialEvent]:
        """
        Get special events near a location.

        Args:
            location: Dict with 'lat' and 'lon' keys
            time: The datetime to check
            radius_km: Search radius in kilometers

        Returns:
            List of SpecialEvent objects
        """
        # Generate events based on day
        events = []

        # Check for randomly generated events
        day_seed = int(time.timestamp() // 86400)  # Day-based seed
        random.seed(day_seed)

        # Probability of event happening
        if random.random() < 0.3:  # 30% chance of event
            event_template = random.choice(self.SAMPLE_EVENTS)

            # Random start time in the evening
            start_hour = random.randint(17, 20)
            event_start = time.replace(
                hour=start_hour,
                minute=0,
                second=0,
                microsecond=0
            )
            event_end = event_start + timedelta(
                hours=event_template["duration_hours"]
            )

            # Only include if event is ongoing or upcoming (within 2 hours)
            if event_start <= time <= event_end or (
                event_start > time and
                (event_start - time).total_seconds() < 7200
            ):
                event = SpecialEvent(
                    event_type=event_template["event_type"],
                    name=event_template["name"],
                    location=event_template["location"],
                    impact_radius_km=event_template["impact_radius_km"],
                    start_time=event_start,
                    end_time=event_end,
                    expected_attendance=event_template["expected_attendance"],
                )

                # Check if within radius
                dist = self._haversine_distance(
                    location["lat"], location["lon"],
                    event.location["lat"], event.location["lon"]
                )

                if dist <= radius_km:
                    events.append(event)

        # Reset random
        if self.seed:
            random.seed(self.seed)

        return events

    def _haversine_distance(
        self,
        lat1: float,
        lon1: float,
        lat2: float,
        lon2: float
    ) -> float:
        """Calculate distance between two points in km."""
        R = 6371  # Earth's radius in km

        lat1_rad = math.radians(lat1)
        lat2_rad = math.radians(lat2)
        delta_lat = math.radians(lat2 - lat1)
        delta_lon = math.radians(lon2 - lon1)

        a = (
            math.sin(delta_lat / 2) ** 2 +
            math.cos(lat1_rad) * math.cos(lat2_rad) *
            math.sin(delta_lon / 2) ** 2
        )
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

        return R * c

    def get_environment_context(
        self,
        location: Dict[str, float],
        time: datetime
    ) -> Dict[str, Any]:
        """
        Get complete environment context for a location and time.

        This is the main method to get all environmental factors at once.

        Args:
            location: Dict with 'lat' and 'lon' keys
            time: The datetime to check

        Returns:
            Dict with weather, traffic, and events data
        """
        weather = self.get_weather(location, time)
        traffic = self.get_traffic(location, time)
        events = self.get_special_events(location, time)

        return {
            "weather": {
                "condition": weather.condition,
                "temperature": weather.temperature,
                "humidity": weather.humidity,
                "precipitation": weather.precipitation,
                "wind_speed": weather.wind_speed,
            },
            "traffic": {
                "level": traffic.level,
                "delay_minutes": traffic.delay_minutes,
                "congestion_factor": traffic.congestion_factor,
            },
            "special_events": [
                {
                    "type": e.event_type,
                    "name": e.name,
                    "location": e.location,
                    "start_time": e.start_time.isoformat(),
                    "end_time": e.end_time.isoformat(),
                    "expected_attendance": e.expected_attendance,
                }
                for e in events
            ],
            "timestamp": time.isoformat(),
        }


# Singleton instance
_environment_service: Optional[EnvironmentService] = None


def get_environment_service() -> EnvironmentService:
    """Get the singleton environment service instance."""
    global _environment_service
    if _environment_service is None:
        _environment_service = EnvironmentService()
    return _environment_service
