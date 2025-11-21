"""
Recommendation Agent - Intelligent venue and social recommendations.

This agent orchestrates the recommendation engine and provides
personalized suggestions with explanations.

Uses OpenRouter API for LLM-powered personalized explanations.
"""
from typing import TypedDict, List, Optional, Dict, Any
from datetime import datetime
import logging
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from ..models.user import User, UserPreferences
from ..models.venue import Venue
from ..models.interaction import UserInteraction, InteractionType, VenueInterest
from ..services.recommendation import RecommendationEngine
from ..services.streaming import get_streaming_service
from ..services.llm_client import get_llm_client, LLMClientError

logger = logging.getLogger(__name__)


class RecommendationState(TypedDict):
    """State for the recommendation agent."""
    user_id: int
    context: Dict[str, Any]  # Time of day, location, etc.
    venue_recommendations: List[dict]
    people_recommendations: List[dict]
    explanations: List[str]
    status: str


class RecommendationAgent:
    """
    AI Agent for generating intelligent recommendations.

    Workflow:
    1. Analyze user context (time, location, history)
    2. Get venue recommendations
    3. Find compatible people
    4. Generate LLM-powered personalized explanations via OpenRouter
    5. Track and learn from interactions
    """

    def __init__(self, db: AsyncSession):
        self.db = db
        self.engine = RecommendationEngine(db)
        self.streaming = get_streaming_service()
        self.llm_client = get_llm_client()

    async def _analyze_context(self, state: RecommendationState) -> RecommendationState:
        """Analyze user context for recommendations."""
        user_id = state["user_id"]

        # Get user
        query = select(User).where(User.id == user_id)
        result = await self.db.execute(query)
        user = result.scalar_one_or_none()

        if not user:
            state["status"] = "user_not_found"
            return state

        # Get preferences
        pref_query = select(UserPreferences).where(UserPreferences.user_id == user_id)
        pref_result = await self.db.execute(pref_query)
        preferences = pref_result.scalar_one_or_none()

        # Analyze time context
        now = datetime.utcnow()
        hour = now.hour

        if 6 <= hour < 11:
            meal_context = "breakfast"
        elif 11 <= hour < 15:
            meal_context = "lunch"
        elif 15 <= hour < 18:
            meal_context = "afternoon"
        elif 18 <= hour < 22:
            meal_context = "dinner"
        else:
            meal_context = "late_night"

        # Weekend vs weekday
        is_weekend = now.weekday() >= 5

        state["context"] = {
            "meal_time": meal_context,
            "is_weekend": is_weekend,
            "hour": hour,
            "user_location": {
                "lat": user.latitude,
                "lon": user.longitude
            },
            "user_persona": user.persona.value if user.persona else None,
            "preferences": {
                "cuisines": preferences.cuisine_preferences if preferences else [],
                "price_range": [
                    preferences.min_price_level if preferences else 1,
                    preferences.max_price_level if preferences else 4
                ],
                "max_distance": preferences.max_distance if preferences else 10
            }
        }

        state["status"] = "context_analyzed"
        return state

    async def _get_venue_recommendations(self, state: RecommendationState) -> RecommendationState:
        """Get venue recommendations based on context."""
        if state["status"] == "user_not_found":
            return state

        # Apply context-based filters
        filters = {}
        meal_time = state["context"].get("meal_time")

        if meal_time == "breakfast":
            filters["category"] = "cafe"
        elif meal_time == "late_night":
            filters["category"] = "bar"

        # Get recommendations
        venues = await self.engine.get_venue_recommendations(
            user_id=state["user_id"],
            limit=10,
            filters=filters if filters else None
        )

        state["venue_recommendations"] = venues

        # Generate LLM-powered explanations for top venues
        explanations = []
        user_preferences = state["context"].get("preferences", {}).get("cuisines", [])

        if venues:
            # Try to generate LLM-powered explanation for top venue
            top_venue = venues[0]
            try:
                llm_explanation = await self.llm_client.generate_recommendation_explanation(
                    venue_name=top_venue.get("name", ""),
                    venue_cuisine=top_venue.get("cuisine", ""),
                    user_preferences=user_preferences,
                    context=state["context"]
                )
                if llm_explanation:
                    explanations.append(llm_explanation)
            except LLMClientError as e:
                logger.warning(f"LLM explanation failed, using fallback: {e}")
                # Fallback to template-based explanations
                if top_venue.get("trending"):
                    explanations.append(f"'{top_venue['name']}' is trending right now!")
                if top_venue.get("distance_km") and top_venue["distance_km"] < 1:
                    explanations.append(f"'{top_venue['name']}' is just {top_venue['distance_km']:.1f}km away")
                if meal_time:
                    explanations.append(f"Perfect for {meal_time}!")

        state["explanations"].extend(explanations)
        state["status"] = "venues_recommended"
        return state

    async def _get_people_recommendations(self, state: RecommendationState) -> RecommendationState:
        """Get compatible people recommendations."""
        if state["status"] == "user_not_found":
            return state

        # Get top venue to find people interested in it
        top_venue_id = None
        if state["venue_recommendations"]:
            top_venue_id = state["venue_recommendations"][0]["id"]

        # Get compatible users
        people = await self.engine.get_compatible_users(
            user_id=state["user_id"],
            venue_id=top_venue_id,
            limit=5
        )

        state["people_recommendations"] = people

        # Generate LLM-powered social match explanations
        for person in people[:2]:
            reasons = person.get("reasons", [])
            compatibility = person.get("compatibility_score", 0.7)

            try:
                llm_reason = await self.llm_client.generate_social_match_reason(
                    user_name=person.get("username", "This user"),
                    shared_interests=reasons,
                    compatibility_score=compatibility
                )
                if llm_reason:
                    state["explanations"].append(f"{person['username']}: {llm_reason}")
            except LLMClientError:
                # Fallback to simple explanation
                if reasons:
                    state["explanations"].append(
                        f"{person['username']}: {', '.join(reasons)}"
                    )

        state["status"] = "people_recommended"
        return state

    async def _publish_recommendation_event(self, state: RecommendationState) -> RecommendationState:
        """Publish recommendation event for tracking."""
        await self.streaming.publish_event(
            event_type="recommendation_generated",
            channel="recommendations",
            payload={
                "user_id": state["user_id"],
                "venue_count": len(state["venue_recommendations"]),
                "people_count": len(state["people_recommendations"]),
                "context": state["context"],
            },
            simulation_time=datetime.utcnow(),
            user_id=state["user_id"]
        )

        state["status"] = "completed"
        return state

    async def get_recommendations(
        self,
        user_id: int,
        include_people: bool = True
    ) -> dict:
        """
        Get personalized recommendations for a user.

        Returns venues and optionally compatible people.
        """
        # Initialize state
        state: RecommendationState = {
            "user_id": user_id,
            "context": {},
            "venue_recommendations": [],
            "people_recommendations": [],
            "explanations": [],
            "status": "initiated"
        }

        # Execute workflow
        state = await self._analyze_context(state)
        state = await self._get_venue_recommendations(state)

        if include_people:
            state = await self._get_people_recommendations(state)

        state = await self._publish_recommendation_event(state)

        return {
            "user_id": user_id,
            "venues": state["venue_recommendations"],
            "people": state["people_recommendations"] if include_people else [],
            "context": state["context"],
            "explanations": state["explanations"],
            "generated_at": datetime.utcnow().isoformat()
        }

    async def track_interaction(
        self,
        user_id: int,
        interaction_type: InteractionType,
        venue_id: Optional[int] = None,
        target_user_id: Optional[int] = None,
        duration_seconds: Optional[int] = None,
        metadata: Optional[dict] = None
    ):
        """Track user interaction for recommendation learning."""
        interaction = UserInteraction(
            user_id=user_id,
            interaction_type=interaction_type,
            venue_id=venue_id,
            target_user_id=target_user_id,
            duration_seconds=duration_seconds,
            metadata=metadata or {}
        )

        self.db.add(interaction)
        await self.db.commit()

        # Publish interaction event
        await self.streaming.publish_event(
            event_type=interaction_type.value,
            channel="user_actions",
            payload={
                "interaction_type": interaction_type.value,
                "venue_id": venue_id,
                "target_user_id": target_user_id,
                "duration_seconds": duration_seconds,
            },
            simulation_time=datetime.utcnow(),
            user_id=user_id,
            venue_id=venue_id
        )

    async def express_interest(
        self,
        user_id: int,
        venue_id: int,
        preferred_time_slot: Optional[str] = None,
        open_to_invites: bool = True
    ) -> dict:
        """
        Express user interest in a venue.

        This signals the user wants to go and is open to being matched.
        """
        # Check if interest already exists
        query = select(VenueInterest).where(
            VenueInterest.user_id == user_id,
            VenueInterest.venue_id == venue_id
        )
        result = await self.db.execute(query)
        existing = result.scalar_one_or_none()

        if existing:
            # Update existing interest
            existing.explicitly_interested = 1
            existing.interest_score = min(existing.interest_score + 0.1, 1.0)
            existing.preferred_time_slot = preferred_time_slot or existing.preferred_time_slot
            existing.open_to_invites = 1 if open_to_invites else 0
        else:
            # Create new interest
            interest = VenueInterest(
                user_id=user_id,
                venue_id=venue_id,
                interest_score=0.8,
                explicitly_interested=1,
                preferred_time_slot=preferred_time_slot,
                open_to_invites=1 if open_to_invites else 0
            )
            self.db.add(interest)

        await self.db.commit()

        # Track interaction
        await self.track_interaction(
            user_id=user_id,
            interaction_type=InteractionType.SAVE,
            venue_id=venue_id,
            metadata={"preferred_time_slot": preferred_time_slot}
        )

        # Publish interest event
        await self.streaming.publish_event(
            event_type="user_interest",
            channel="user_actions",
            payload={
                "venue_id": venue_id,
                "preferred_time_slot": preferred_time_slot,
                "open_to_invites": open_to_invites,
            },
            simulation_time=datetime.utcnow(),
            user_id=user_id,
            venue_id=venue_id
        )

        # Get others interested in same venue
        others_interested = await self.engine.get_users_interested_in_venue(
            venue_id=venue_id,
            exclude_user_id=user_id,
            limit=5
        )

        return {
            "success": True,
            "venue_id": venue_id,
            "others_interested": others_interested,
            "message": f"Interest recorded! {len(others_interested)} others are also interested."
        }
