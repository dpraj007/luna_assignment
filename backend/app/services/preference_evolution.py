"""
Preference Evolution Service.

Implements dynamic preference updates based on:
- User actions (browse, express interest, make booking)
- Social influence from friends
- Seasonal changes
- Review feedback
"""
from typing import Dict, Any, Optional, List
from datetime import datetime
from dataclasses import dataclass
import logging
import random

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from ..models.user import User, UserPreferences, Friendship

logger = logging.getLogger(__name__)


@dataclass
class EvolutionConfig:
    """Configuration for preference evolution."""
    # Learning rates (how quickly preferences change)
    browse_learning_rate: float = 0.02  # 2% shift per browse
    interest_learning_rate: float = 0.05  # 5% shift per interest expression
    booking_learning_rate: float = 0.10  # 10% shift per booking
    cancel_learning_rate: float = -0.03  # -3% for cancellations

    # Social influence
    social_influence_rate: float = 0.02  # 2% influence per interaction
    max_social_influence: float = 0.15  # Max 15% total social influence

    # Seasonal drift
    seasonal_drift_rate: float = 0.01  # 1% per season change

    # Bounds
    min_preference: float = 0.0
    max_preference: float = 1.0
    max_change_per_action: float = 0.15  # Max 15% change per action


class PreferenceEvolutionService:
    """
    Service for evolving user preferences over time.

    Preferences evolve based on:
    1. User actions (browsing, expressing interest, booking)
    2. Social influence from friends
    3. Seasonal changes
    4. Review feedback
    """

    def __init__(self, config: Optional[EvolutionConfig] = None):
        """Initialize the preference evolution service."""
        self.config = config or EvolutionConfig()

    async def evolve_from_action(
        self,
        user_id: int,
        action_type: str,
        action_data: Dict[str, Any],
        db: AsyncSession
    ) -> Dict[str, Any]:
        """
        Evolve preferences based on user action.

        Args:
            user_id: The user ID
            action_type: Type of action (browse, express_interest, make_booking, cancel_booking)
            action_data: Data about the action (venue_id, cuisine, price_range, etc.)
            db: Database session

        Returns:
            Dict with updated preferences and changes made
        """
        # Get user preferences
        query = select(UserPreferences).where(UserPreferences.user_id == user_id)
        result = await db.execute(query)
        prefs = result.scalar_one_or_none()

        if not prefs:
            logger.warning(f"No preferences found for user {user_id}")
            return {"error": "No preferences found"}

        # Determine learning rate based on action
        learning_rates = {
            "browse": self.config.browse_learning_rate,
            "express_interest": self.config.interest_learning_rate,
            "make_booking": self.config.booking_learning_rate,
            "cancel_booking": self.config.cancel_learning_rate,
        }
        learning_rate = learning_rates.get(action_type, 0.01)

        changes = {}

        # Update cuisine preferences
        cuisine = action_data.get("cuisine")
        if cuisine and prefs.cuisine_preferences:
            cuisine_prefs = prefs.cuisine_preferences.copy()
            if cuisine in cuisine_prefs:
                old_value = cuisine_prefs[cuisine]
                new_value = self._apply_change(old_value, learning_rate)
                cuisine_prefs[cuisine] = new_value
                changes["cuisine"] = {cuisine: {"old": old_value, "new": new_value}}
            else:
                # New cuisine discovered
                cuisine_prefs[cuisine] = max(0.3, learning_rate * 5)
                changes["cuisine"] = {cuisine: {"old": 0, "new": cuisine_prefs[cuisine]}}

            prefs.cuisine_preferences = cuisine_prefs

        # Update price range preference
        price_range = action_data.get("price_range")
        if price_range:
            # Shift preferred price range toward actioned price
            current_range = prefs.price_range or {"min": 20, "max": 60}
            if isinstance(price_range, dict):
                action_mid = (price_range.get("min", 0) + price_range.get("max", 100)) / 2
            else:
                action_mid = price_range

            current_mid = (current_range["min"] + current_range["max"]) / 2
            shift = (action_mid - current_mid) * abs(learning_rate)

            new_range = {
                "min": max(0, current_range["min"] + shift * 0.5),
                "max": min(500, current_range["max"] + shift * 0.5),
            }
            prefs.price_range = new_range
            changes["price_range"] = {"old": current_range, "new": new_range}

        # Update ambiance preferences
        ambiance = action_data.get("ambiance")
        if ambiance and prefs.ambiance_preferences:
            ambiance_prefs = prefs.ambiance_preferences.copy()
            if ambiance in ambiance_prefs:
                old_value = ambiance_prefs[ambiance]
                new_value = self._apply_change(old_value, learning_rate)
                ambiance_prefs[ambiance] = new_value
                changes["ambiance"] = {ambiance: {"old": old_value, "new": new_value}}

            prefs.ambiance_preferences = ambiance_prefs

        # Apply random drift (small noise)
        drift = random.uniform(-0.01, 0.01)
        if prefs.cuisine_preferences:
            for cuisine_key in random.sample(
                list(prefs.cuisine_preferences.keys()),
                min(2, len(prefs.cuisine_preferences))
            ):
                prefs.cuisine_preferences[cuisine_key] = self._clamp(
                    prefs.cuisine_preferences[cuisine_key] + drift
                )

        # Commit changes
        await db.commit()

        return {
            "user_id": user_id,
            "action_type": action_type,
            "learning_rate": learning_rate,
            "changes": changes,
        }

    async def apply_social_influence(
        self,
        user_id: int,
        friend_id: int,
        interaction_type: str,
        db: AsyncSession
    ) -> Dict[str, Any]:
        """
        Apply social influence from a friend.

        Called when user interacts with friend (accepts invite, dines together).

        Args:
            user_id: The user being influenced
            friend_id: The influencing friend
            interaction_type: Type of interaction
            db: Database session

        Returns:
            Dict with influence applied
        """
        # Get both users' preferences
        user_query = select(UserPreferences).where(UserPreferences.user_id == user_id)
        friend_query = select(UserPreferences).where(UserPreferences.user_id == friend_id)

        user_result = await db.execute(user_query)
        friend_result = await db.execute(friend_query)

        user_prefs = user_result.scalar_one_or_none()
        friend_prefs = friend_result.scalar_one_or_none()

        if not user_prefs or not friend_prefs:
            return {"error": "Preferences not found"}

        influence_rate = self.config.social_influence_rate
        changes = {}

        # Influence cuisine preferences
        if friend_prefs.cuisine_preferences and user_prefs.cuisine_preferences:
            user_cuisines = user_prefs.cuisine_preferences.copy()

            for cuisine, friend_value in friend_prefs.cuisine_preferences.items():
                if cuisine in user_cuisines:
                    # Pull toward friend's preference
                    user_value = user_cuisines[cuisine]
                    influence = (friend_value - user_value) * influence_rate
                    influence = max(-self.config.max_social_influence,
                                  min(self.config.max_social_influence, influence))
                    new_value = self._clamp(user_value + influence)
                    user_cuisines[cuisine] = new_value

                    if abs(influence) > 0.01:
                        changes[f"cuisine_{cuisine}"] = {
                            "old": user_value,
                            "new": new_value,
                            "influence": influence
                        }

            user_prefs.cuisine_preferences = user_cuisines

        # Influence price range (slight pull toward friend's range)
        if friend_prefs.price_range and user_prefs.price_range:
            user_range = user_prefs.price_range
            friend_range = friend_prefs.price_range

            user_mid = (user_range["min"] + user_range["max"]) / 2
            friend_mid = (friend_range["min"] + friend_range["max"]) / 2

            shift = (friend_mid - user_mid) * influence_rate
            new_range = {
                "min": max(0, user_range["min"] + shift * 0.3),
                "max": min(500, user_range["max"] + shift * 0.3),
            }
            user_prefs.price_range = new_range
            changes["price_range"] = {"old": user_range, "new": new_range}

        await db.commit()

        return {
            "user_id": user_id,
            "friend_id": friend_id,
            "interaction_type": interaction_type,
            "changes": changes,
        }

    async def apply_seasonal_changes(
        self,
        user_id: int,
        current_season: str,
        db: AsyncSession
    ) -> Dict[str, Any]:
        """
        Apply seasonal preference changes.

        Args:
            user_id: The user ID
            current_season: Current season (spring, summer, fall, winter)
            db: Database session

        Returns:
            Dict with changes applied
        """
        query = select(UserPreferences).where(UserPreferences.user_id == user_id)
        result = await db.execute(query)
        prefs = result.scalar_one_or_none()

        if not prefs:
            return {"error": "Preferences not found"}

        drift_rate = self.config.seasonal_drift_rate
        changes = {}

        # Seasonal cuisine preferences
        seasonal_boosts = {
            "summer": ["salad", "seafood", "mediterranean", "asian"],
            "winter": ["italian", "american", "steakhouse", "comfort"],
            "spring": ["asian", "mediterranean", "brunch"],
            "fall": ["american", "steakhouse", "comfort"],
        }

        seasonal_decreases = {
            "summer": ["steakhouse", "comfort"],
            "winter": ["salad", "seafood"],
            "spring": ["comfort"],
            "fall": ["salad"],
        }

        if prefs.cuisine_preferences:
            cuisine_prefs = prefs.cuisine_preferences.copy()

            # Boost seasonal cuisines
            for cuisine in seasonal_boosts.get(current_season, []):
                if cuisine in cuisine_prefs:
                    old_value = cuisine_prefs[cuisine]
                    cuisine_prefs[cuisine] = self._clamp(old_value + drift_rate)

            # Decrease off-season cuisines
            for cuisine in seasonal_decreases.get(current_season, []):
                if cuisine in cuisine_prefs:
                    old_value = cuisine_prefs[cuisine]
                    cuisine_prefs[cuisine] = self._clamp(old_value - drift_rate * 0.5)

            prefs.cuisine_preferences = cuisine_prefs
            changes["seasonal_cuisine_adjustment"] = current_season

        # Seasonal ambiance preferences
        if prefs.ambiance_preferences:
            ambiance_prefs = prefs.ambiance_preferences.copy()

            if current_season == "summer":
                if "outdoor" in ambiance_prefs:
                    ambiance_prefs["outdoor"] = self._clamp(
                        ambiance_prefs["outdoor"] + drift_rate * 2
                    )
                if "rooftop" in ambiance_prefs:
                    ambiance_prefs["rooftop"] = self._clamp(
                        ambiance_prefs["rooftop"] + drift_rate * 2
                    )
            elif current_season == "winter":
                if "cozy" in ambiance_prefs:
                    ambiance_prefs["cozy"] = self._clamp(
                        ambiance_prefs["cozy"] + drift_rate * 2
                    )
                if "outdoor" in ambiance_prefs:
                    ambiance_prefs["outdoor"] = self._clamp(
                        ambiance_prefs["outdoor"] - drift_rate
                    )

            prefs.ambiance_preferences = ambiance_prefs

        await db.commit()

        return {
            "user_id": user_id,
            "season": current_season,
            "changes": changes,
        }

    async def apply_review_feedback(
        self,
        user_id: int,
        venue_id: int,
        rating: float,
        venue_data: Dict[str, Any],
        db: AsyncSession
    ) -> Dict[str, Any]:
        """
        Apply preference changes based on review feedback.

        Args:
            user_id: The user ID
            venue_id: The reviewed venue
            rating: Rating given (1-5)
            venue_data: Venue attributes (cuisine, price_range, ambiance)
            db: Database session

        Returns:
            Dict with changes applied
        """
        query = select(UserPreferences).where(UserPreferences.user_id == user_id)
        result = await db.execute(query)
        prefs = result.scalar_one_or_none()

        if not prefs:
            return {"error": "Preferences not found"}

        # Convert rating to learning signal
        # 5 = strong positive, 3 = neutral, 1 = strong negative
        signal = (rating - 3) / 2  # -1 to 1
        learning_rate = self.config.booking_learning_rate * signal

        changes = {}

        # Update based on venue attributes
        cuisine = venue_data.get("cuisine")
        if cuisine and prefs.cuisine_preferences:
            cuisine_prefs = prefs.cuisine_preferences.copy()
            if cuisine in cuisine_prefs:
                old_value = cuisine_prefs[cuisine]
                new_value = self._apply_change(old_value, learning_rate)
                cuisine_prefs[cuisine] = new_value
                changes["cuisine"] = {
                    cuisine: {"old": old_value, "new": new_value, "rating": rating}
                }
            prefs.cuisine_preferences = cuisine_prefs

        await db.commit()

        return {
            "user_id": user_id,
            "venue_id": venue_id,
            "rating": rating,
            "signal": signal,
            "changes": changes,
        }

    def _apply_change(self, current: float, change: float) -> float:
        """Apply a change to a preference value with bounds."""
        new_value = current + change
        # Clamp change to max per action
        if abs(new_value - current) > self.config.max_change_per_action:
            if change > 0:
                new_value = current + self.config.max_change_per_action
            else:
                new_value = current - self.config.max_change_per_action
        return self._clamp(new_value)

    def _clamp(self, value: float) -> float:
        """Clamp value to valid preference range."""
        return max(
            self.config.min_preference,
            min(self.config.max_preference, value)
        )


# Singleton instance
_evolution_service: Optional[PreferenceEvolutionService] = None


def get_preference_evolution_service() -> PreferenceEvolutionService:
    """Get the singleton preference evolution service instance."""
    global _evolution_service
    if _evolution_service is None:
        _evolution_service = PreferenceEvolutionService()
    return _evolution_service
