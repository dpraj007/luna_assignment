"""
Temporal Event Generator Service.

Simulates real-world time patterns including:
- Breakfast/Lunch/Dinner rush hours
- Weekend vs weekday behaviors
- Holiday and special event surges
- Weather-influenced decisions
"""
from typing import Dict, Any, Optional, List
from datetime import datetime, date
from dataclasses import dataclass
import json
import os
import logging

logger = logging.getLogger(__name__)


@dataclass
class TimeContext:
    """Context information about a point in time."""
    hour: int
    minute: int
    day_of_week: int  # 0=Monday, 6=Sunday
    day_of_month: int
    month: int
    year: int
    meal_period: str  # breakfast, lunch, dinner, late_night, off_peak
    is_weekend: bool
    is_holiday: bool
    holiday_name: Optional[str]
    season: str  # spring, summer, fall, winter


class TemporalEventGenerator:
    """
    Generates time-based modifiers for simulation behavior.

    This service analyzes simulation time and returns modifiers
    that affect user action probabilities based on:
    - Time of day (meal periods)
    - Day of week (weekend vs weekday)
    - Holidays
    - Seasons
    """

    # Major US holidays
    HOLIDAYS = {
        (1, 1): {"name": "New Year's Day", "impact": "high", "type": "national"},
        (2, 14): {"name": "Valentine's Day", "impact": "high", "type": "cultural"},
        (7, 4): {"name": "Independence Day", "impact": "medium", "type": "national"},
        (10, 31): {"name": "Halloween", "impact": "medium", "type": "cultural"},
        (11, 25): {"name": "Thanksgiving", "impact": "high", "type": "national"},
        (12, 25): {"name": "Christmas", "impact": "high", "type": "national"},
        (12, 31): {"name": "New Year's Eve", "impact": "high", "type": "cultural"},
    }

    # Meal period definitions (hour ranges)
    MEAL_PERIODS = {
        "breakfast": (6, 11),
        "lunch": (11, 15),
        "afternoon": (15, 18),
        "dinner": (18, 22),
        "late_night": (22, 24),
        "early_morning": (0, 6),
    }

    def __init__(self):
        """Initialize the temporal event generator."""
        self._load_custom_holidays()

    def _load_custom_holidays(self):
        """Load custom holidays from JSON file if available."""
        holidays_path = os.path.join(
            os.path.dirname(__file__),
            "..",
            "data",
            "holidays.json"
        )

        if os.path.exists(holidays_path):
            try:
                with open(holidays_path, 'r') as f:
                    custom_holidays = json.load(f)
                    for holiday in custom_holidays:
                        month = holiday.get("month")
                        day = holiday.get("day")
                        if month and day:
                            self.HOLIDAYS[(month, day)] = {
                                "name": holiday.get("name", "Custom Holiday"),
                                "impact": holiday.get("impact", "medium"),
                                "type": holiday.get("type", "custom"),
                            }
            except Exception as e:
                logger.warning(f"Failed to load custom holidays: {e}")

    def get_time_context(self, simulation_time: datetime) -> TimeContext:
        """
        Extract time context from simulation time.

        Args:
            simulation_time: The current simulation datetime

        Returns:
            TimeContext with all relevant time information
        """
        hour = simulation_time.hour
        minute = simulation_time.minute
        day_of_week = simulation_time.weekday()
        day_of_month = simulation_time.day
        month = simulation_time.month
        year = simulation_time.year

        # Determine meal period
        meal_period = self._get_meal_period(hour)

        # Check if weekend
        is_weekend = day_of_week >= 5  # Saturday=5, Sunday=6

        # Check if holiday
        is_holiday, holiday_name = self._check_holiday(month, day_of_month)

        # Determine season
        season = self._get_season(month)

        return TimeContext(
            hour=hour,
            minute=minute,
            day_of_week=day_of_week,
            day_of_month=day_of_month,
            month=month,
            year=year,
            meal_period=meal_period,
            is_weekend=is_weekend,
            is_holiday=is_holiday,
            holiday_name=holiday_name,
            season=season,
        )

    def _get_meal_period(self, hour: int) -> str:
        """Determine the meal period for a given hour."""
        for period, (start, end) in self.MEAL_PERIODS.items():
            if start <= hour < end:
                return period
        return "off_peak"

    def _check_holiday(self, month: int, day: int) -> tuple:
        """Check if date is a holiday."""
        key = (month, day)
        if key in self.HOLIDAYS:
            return True, self.HOLIDAYS[key]["name"]
        return False, None

    def _get_season(self, month: int) -> str:
        """Determine the season for a given month."""
        if month in [12, 1, 2]:
            return "winter"
        elif month in [3, 4, 5]:
            return "spring"
        elif month in [6, 7, 8]:
            return "summer"
        else:
            return "fall"

    def get_action_modifiers(
        self,
        context: TimeContext,
        scenario: Optional[str] = None,
        weather: Optional[Dict[str, Any]] = None
    ) -> Dict[str, float]:
        """
        Get action probability modifiers based on time context.

        Args:
            context: TimeContext for current simulation time
            scenario: Optional scenario override
            weather: Optional weather context

        Returns:
            Dictionary of action -> modifier multiplier
        """
        modifiers = {
            "browse": 1.0,
            "check_friends": 1.0,
            "express_interest": 1.0,
            "send_invite": 1.0,
            "respond_invite": 1.0,
            "make_booking": 1.0,
        }

        # Apply meal period modifiers
        modifiers = self._apply_meal_period_modifiers(modifiers, context)

        # Apply weekend modifiers
        if context.is_weekend:
            modifiers = self._apply_weekend_modifiers(modifiers, context)

        # Apply holiday modifiers
        if context.is_holiday:
            modifiers = self._apply_holiday_modifiers(modifiers, context)

        # Apply seasonal modifiers
        modifiers = self._apply_seasonal_modifiers(modifiers, context)

        # Apply weather modifiers if provided
        if weather:
            modifiers = self._apply_weather_modifiers(modifiers, weather)

        # Apply scenario overrides
        if scenario:
            modifiers = self._apply_scenario_overrides(modifiers, scenario, context)

        return modifiers

    def _apply_meal_period_modifiers(
        self,
        modifiers: Dict[str, float],
        context: TimeContext
    ) -> Dict[str, float]:
        """Apply modifiers based on meal period."""
        meal_mods = {
            "breakfast": {
                "browse": 1.1,
                "check_friends": 0.8,
                "send_invite": 0.7,
                "make_booking": 0.9,
            },
            "lunch": {
                "browse": 1.5,
                "make_booking": 1.5,
                "send_invite": 0.9,
                "express_interest": 1.2,
            },
            "afternoon": {
                "browse": 1.2,
                "check_friends": 1.1,
                "express_interest": 1.1,
            },
            "dinner": {
                "browse": 1.3,
                "send_invite": 1.3,
                "make_booking": 1.4,
                "express_interest": 1.2,
                "check_friends": 1.2,
            },
            "late_night": {
                "browse": 0.8,
                "check_friends": 1.3,
                "send_invite": 1.2,
                "make_booking": 0.6,
            },
            "early_morning": {
                "browse": 0.5,
                "check_friends": 0.4,
                "send_invite": 0.3,
                "make_booking": 0.3,
                "express_interest": 0.4,
                "respond_invite": 0.5,
            },
        }

        period_mods = meal_mods.get(context.meal_period, {})
        for action, mod in period_mods.items():
            modifiers[action] *= mod

        return modifiers

    def _apply_weekend_modifiers(
        self,
        modifiers: Dict[str, float],
        context: TimeContext
    ) -> Dict[str, float]:
        """Apply weekend-specific modifiers."""
        # Weekends have more social activity
        modifiers["send_invite"] *= 1.3
        modifiers["check_friends"] *= 1.2
        modifiers["make_booking"] *= 1.15

        # Saturday brunch is popular
        if context.day_of_week == 5 and context.meal_period in ["breakfast", "lunch"]:
            modifiers["browse"] *= 1.4
            modifiers["express_interest"] *= 1.3
            modifiers["make_booking"] *= 1.5

        # Sunday is more relaxed
        if context.day_of_week == 6:
            modifiers["browse"] *= 1.2
            modifiers["express_interest"] *= 1.1

        return modifiers

    def _apply_holiday_modifiers(
        self,
        modifiers: Dict[str, float],
        context: TimeContext
    ) -> Dict[str, float]:
        """Apply holiday-specific modifiers."""
        holiday_key = (context.month, context.day_of_month)
        holiday_info = self.HOLIDAYS.get(holiday_key, {})
        impact = holiday_info.get("impact", "medium")

        impact_multipliers = {
            "low": 1.1,
            "medium": 1.3,
            "high": 1.5,
        }
        base_mult = impact_multipliers.get(impact, 1.2)

        # Holidays increase social activity
        modifiers["send_invite"] *= base_mult
        modifiers["check_friends"] *= base_mult * 0.9
        modifiers["express_interest"] *= base_mult * 0.8

        # Special holidays have specific patterns
        if context.holiday_name == "Valentine's Day":
            modifiers["send_invite"] *= 1.3
            modifiers["make_booking"] *= 1.5
        elif context.holiday_name in ["Thanksgiving", "Christmas"]:
            modifiers["check_friends"] *= 1.4
            modifiers["browse"] *= 0.8  # Less browsing, more family time
        elif context.holiday_name == "New Year's Eve":
            modifiers["send_invite"] *= 1.6
            modifiers["make_booking"] *= 1.4

        return modifiers

    def _apply_seasonal_modifiers(
        self,
        modifiers: Dict[str, float],
        context: TimeContext
    ) -> Dict[str, float]:
        """Apply seasonal modifiers."""
        season_mods = {
            "summer": {
                "browse": 1.15,  # More outdoor dining interest
                "send_invite": 1.1,
                "express_interest": 1.1,
            },
            "winter": {
                "browse": 1.05,
                "make_booking": 1.1,  # More indoor dining
            },
            "spring": {
                "browse": 1.1,
                "express_interest": 1.05,
            },
            "fall": {
                "browse": 1.05,
                "make_booking": 1.05,
            },
        }

        season_mod = season_mods.get(context.season, {})
        for action, mod in season_mod.items():
            modifiers[action] *= mod

        return modifiers

    def _apply_weather_modifiers(
        self,
        modifiers: Dict[str, float],
        weather: Dict[str, Any]
    ) -> Dict[str, float]:
        """Apply weather-based modifiers."""
        condition = weather.get("condition", "sunny")
        temperature = weather.get("temperature", 70)

        if condition == "rainy":
            modifiers["browse"] *= 0.9
            modifiers["send_invite"] *= 0.8
            modifiers["make_booking"] *= 1.1  # Prefer indoor
        elif condition == "snow":
            modifiers["browse"] *= 0.7
            modifiers["send_invite"] *= 0.6
            modifiers["make_booking"] *= 0.8
        elif condition == "sunny" and 65 <= temperature <= 85:
            modifiers["browse"] *= 1.1
            modifiers["send_invite"] *= 1.1
            modifiers["express_interest"] *= 1.15

        # Extreme temperatures reduce activity
        if temperature > 95 or temperature < 20:
            for action in modifiers:
                modifiers[action] *= 0.8

        return modifiers

    def _apply_scenario_overrides(
        self,
        modifiers: Dict[str, float],
        scenario: str,
        context: TimeContext
    ) -> Dict[str, float]:
        """Apply scenario-specific overrides."""
        scenario_overrides = {
            "lunch_rush": {
                "browse": 1.5,
                "make_booking": 2.0,
                "express_interest": 1.3,
            },
            "friday_night": {
                "send_invite": 2.0,
                "check_friends": 1.5,
                "make_booking": 1.3,
            },
            "weekend_brunch": {
                "browse": 1.4,
                "express_interest": 1.5,
                "send_invite": 1.2,
            },
            "concert_night": {
                "send_invite": 1.5,
                "make_booking": 1.5,
                "browse": 1.3,
            },
            "new_user_onboarding": {
                "browse": 2.0,
                "check_friends": 1.5,
                "express_interest": 1.3,
            },
        }

        if scenario in scenario_overrides:
            for action, mod in scenario_overrides[scenario].items():
                # Scenario overrides replace, not multiply
                modifiers[action] = mod

        return modifiers

    def get_venue_availability_modifiers(
        self,
        context: TimeContext,
        weather: Optional[Dict[str, Any]] = None
    ) -> Dict[str, float]:
        """
        Get venue availability modifiers based on context.

        Returns modifiers for venue availability (slots_remaining, wait_time).
        """
        modifiers = {
            "availability_factor": 1.0,  # 1.0 = normal, <1.0 = fewer slots
            "wait_time_factor": 1.0,  # 1.0 = normal, >1.0 = longer waits
            "price_factor": 1.0,  # 1.0 = normal, >1.0 = higher prices
        }

        # Peak hours reduce availability
        if context.meal_period in ["lunch", "dinner"]:
            modifiers["availability_factor"] *= 0.7
            modifiers["wait_time_factor"] *= 1.3

        # Weekends are busier
        if context.is_weekend:
            modifiers["availability_factor"] *= 0.8
            modifiers["wait_time_factor"] *= 1.2

        # Holidays are very busy
        if context.is_holiday:
            modifiers["availability_factor"] *= 0.5
            modifiers["wait_time_factor"] *= 1.5
            modifiers["price_factor"] *= 1.2

        # Weather affects outdoor venues differently
        if weather:
            if weather.get("condition") == "rainy":
                # Outdoor venues less available (closed patios)
                # Indoor venues more crowded
                modifiers["availability_factor"] *= 0.9
            elif weather.get("condition") == "sunny":
                # More outdoor seating available
                modifiers["availability_factor"] *= 1.1

        return modifiers

    def get_recommended_scenarios(self, context: TimeContext) -> List[str]:
        """
        Get recommended scenarios based on current time context.

        Returns list of scenario names that would be appropriate.
        """
        scenarios = []

        # Lunch rush during lunch hours on weekdays
        if context.meal_period == "lunch" and not context.is_weekend:
            scenarios.append("lunch_rush")

        # Friday night
        if context.day_of_week == 4 and context.hour >= 17:
            scenarios.append("friday_night")

        # Weekend brunch
        if context.is_weekend and context.meal_period in ["breakfast", "lunch"]:
            scenarios.append("weekend_brunch")

        # Default to normal if nothing specific
        if not scenarios:
            scenarios.append("normal")

        return scenarios


# Singleton instance
_temporal_generator: Optional[TemporalEventGenerator] = None


def get_temporal_generator() -> TemporalEventGenerator:
    """Get the singleton temporal event generator instance."""
    global _temporal_generator
    if _temporal_generator is None:
        _temporal_generator = TemporalEventGenerator()
    return _temporal_generator
