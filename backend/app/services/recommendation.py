"""
Recommendation Engine with Spatial Analysis and Social Compatibility.
"""
from typing import List, Optional, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_
from datetime import datetime, timedelta
import math
import numpy as np

from ..models.user import User, UserPreferences, Friendship
from ..models.venue import Venue
from ..models.interaction import VenueInterest, UserInteraction, InteractionType
from ..core.config import settings


class RecommendationEngine:
    """
    AI-powered recommendation engine for venues and social connections.

    Features:
    - Spatial Analysis: Find optimal venues based on location and preferences
    - Social Compatibility: Match users with compatible dining companions
    - Interest-based Matching: Connect users with shared venue interests
    """

    def __init__(self, db: AsyncSession):
        self.db = db

    # ============== SPATIAL ANALYSIS ==============

    @staticmethod
    def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """Calculate distance between two points in kilometers."""
        R = 6371  # Earth's radius in kilometers

        lat1_rad = math.radians(lat1)
        lat2_rad = math.radians(lat2)
        delta_lat = math.radians(lat2 - lat1)
        delta_lon = math.radians(lon2 - lon1)

        a = math.sin(delta_lat / 2) ** 2 + \
            math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(delta_lon / 2) ** 2
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

        return R * c

    async def get_venue_recommendations(
        self,
        user_id: int,
        limit: int = 10,
        filters: Optional[dict] = None
    ) -> List[dict]:
        """
        Get personalized venue recommendations for a user.

        Considers:
        - User location and distance preferences
        - Cuisine and ambiance preferences
        - Price range
        - Venue popularity and ratings
        - Friends' activity at venues
        """
        # Get user with preferences
        user_query = select(User).where(User.id == user_id)
        result = await self.db.execute(user_query)
        user = result.scalar_one_or_none()

        if not user:
            return []

        # Get user preferences
        pref_query = select(UserPreferences).where(UserPreferences.user_id == user_id)
        pref_result = await self.db.execute(pref_query)
        preferences = pref_result.scalar_one_or_none()

        # Get all venues
        venue_query = select(Venue)
        if filters:
            if filters.get("category"):
                venue_query = venue_query.where(Venue.category == filters["category"])
            if filters.get("min_rating"):
                venue_query = venue_query.where(Venue.rating >= filters["min_rating"])

        venue_result = await self.db.execute(venue_query)
        venues = venue_result.scalars().all()

        # Score each venue
        scored_venues = []
        for venue in venues:
            score = await self._calculate_venue_score(user, preferences, venue)
            if score > 0:
                scored_venues.append({
                    "venue": venue,
                    "score": score,
                    "distance_km": self.haversine_distance(
                        user.latitude or 0, user.longitude or 0,
                        venue.latitude, venue.longitude
                    ) if user.latitude else None
                })

        # Sort by score and return top results
        scored_venues.sort(key=lambda x: x["score"], reverse=True)

        return [
            {
                "id": v["venue"].id,
                "name": v["venue"].name,
                "category": v["venue"].category,
                "cuisine_type": v["venue"].cuisine_type,
                "rating": v["venue"].rating,
                "price_level": v["venue"].price_level,
                "distance_km": round(v["distance_km"], 2) if v["distance_km"] else None,
                "score": round(v["score"], 3),
                "image_url": v["venue"].image_url,
                "latitude": v["venue"].latitude,
                "longitude": v["venue"].longitude,
                "ambiance": v["venue"].ambiance,
                "trending": v["venue"].trending,
            }
            for v in scored_venues[:limit]
        ]

    async def _calculate_venue_score(
        self,
        user: User,
        preferences: Optional[UserPreferences],
        venue: Venue
    ) -> float:
        """Calculate recommendation score for a venue (0-1)."""
        scores = []
        weights = []

        # Distance score (30% weight)
        if user.latitude and user.longitude:
            distance = self.haversine_distance(
                user.latitude, user.longitude,
                venue.latitude, venue.longitude
            )
            max_distance = preferences.max_distance if preferences else settings.MAX_DISTANCE_KM
            if distance > max_distance:
                return 0  # Too far
            distance_score = 1 - (distance / max_distance)
            scores.append(distance_score)
            weights.append(0.3)

        # Price score (15% weight)
        if preferences:
            if preferences.min_price_level <= venue.price_level <= preferences.max_price_level:
                price_score = 1.0
            else:
                price_score = 0.3  # Still show but lower score
            scores.append(price_score)
            weights.append(0.15)

        # Rating score (20% weight)
        rating_score = venue.rating / 5.0
        scores.append(rating_score)
        weights.append(0.2)

        # Popularity score (10% weight)
        scores.append(venue.popularity_score)
        weights.append(0.1)

        # Cuisine preference match (15% weight)
        if preferences and preferences.cuisine_preferences:
            if venue.cuisine_type in preferences.cuisine_preferences:
                cuisine_score = 1.0
            else:
                cuisine_score = 0.5
            scores.append(cuisine_score)
            weights.append(0.15)

        # Trending bonus (10% weight)
        trending_score = 1.0 if venue.trending else 0.5
        scores.append(trending_score)
        weights.append(0.1)

        # Calculate weighted average
        if not scores:
            return 0.5

        total_weight = sum(weights)
        weighted_sum = sum(s * w for s, w in zip(scores, weights))

        return weighted_sum / total_weight

    # ============== SOCIAL COMPATIBILITY ==============

    async def get_compatible_users(
        self,
        user_id: int,
        venue_id: Optional[int] = None,
        limit: int = 10
    ) -> List[dict]:
        """
        Find users with high compatibility for dining together.

        Considers:
        - Shared friends (mutual connections)
        - Similar preferences
        - Shared venue interests
        - Activity patterns
        - Openness to meeting new people
        """
        # Get the user
        user_query = select(User).where(User.id == user_id)
        result = await self.db.execute(user_query)
        user = result.scalar_one_or_none()

        if not user:
            return []

        # Get user's friends
        friends_query = select(Friendship.friend_id).where(Friendship.user_id == user_id)
        friends_result = await self.db.execute(friends_query)
        friend_ids = [f for f in friends_result.scalars().all()]

        # Get all other users
        other_users_query = select(User).where(
            and_(
                User.id != user_id,
                User.id.notin_([user_id])  # Exclude self
            )
        )
        other_result = await self.db.execute(other_users_query)
        other_users = other_result.scalars().all()

        # Score each user
        scored_users = []
        for other_user in other_users:
            score, reasons = await self._calculate_compatibility(
                user, other_user, friend_ids, venue_id
            )
            if score >= settings.COMPATIBILITY_THRESHOLD:
                scored_users.append({
                    "user": other_user,
                    "score": score,
                    "reasons": reasons
                })

        # Sort by score
        scored_users.sort(key=lambda x: x["score"], reverse=True)

        return [
            {
                "id": u["user"].id,
                "username": u["user"].username,
                "full_name": u["user"].full_name,
                "avatar_url": u["user"].avatar_url,
                "compatibility_score": round(u["score"], 3),
                "reasons": u["reasons"],
                "is_friend": u["user"].id in friend_ids,
                "activity_score": u["user"].activity_score,
            }
            for u in scored_users[:limit]
        ]

    async def _calculate_compatibility(
        self,
        user: User,
        other_user: User,
        friend_ids: List[int],
        venue_id: Optional[int]
    ) -> Tuple[float, List[str]]:
        """Calculate compatibility score between two users."""
        scores = []
        weights = []
        reasons = []

        # Friend connection (25% weight)
        if other_user.id in friend_ids:
            scores.append(1.0)
            reasons.append("Friend")
        else:
            # Check mutual friends
            mutual_query = select(func.count(Friendship.id)).where(
                and_(
                    Friendship.user_id == other_user.id,
                    Friendship.friend_id.in_(friend_ids)
                )
            )
            mutual_result = await self.db.execute(mutual_query)
            mutual_count = mutual_result.scalar() or 0
            if mutual_count > 0:
                scores.append(min(mutual_count / 5, 1.0))  # Cap at 5 mutuals
                reasons.append(f"{mutual_count} mutual friend(s)")
            else:
                scores.append(0.3)
        weights.append(0.25)

        # Preference similarity (25% weight)
        pref_score = await self._calculate_preference_similarity(user.id, other_user.id)
        scores.append(pref_score)
        weights.append(0.25)
        if pref_score > 0.7:
            reasons.append("Similar taste")

        # Shared venue interest (20% weight if venue specified)
        if venue_id:
            interest_query = select(VenueInterest).where(
                and_(
                    VenueInterest.venue_id == venue_id,
                    VenueInterest.user_id == other_user.id,
                    VenueInterest.explicitly_interested == 1
                )
            )
            interest_result = await self.db.execute(interest_query)
            shared_interest = interest_result.scalar_one_or_none()
            if shared_interest:
                scores.append(1.0)
                reasons.append("Interested in same venue")
            else:
                scores.append(0.3)
            weights.append(0.2)

        # Activity level match (15% weight)
        activity_diff = abs(user.activity_score - other_user.activity_score)
        activity_score = 1 - activity_diff
        scores.append(activity_score)
        weights.append(0.15)

        # Social openness (15% weight)
        other_prefs_query = select(UserPreferences).where(
            UserPreferences.user_id == other_user.id
        )
        other_prefs_result = await self.db.execute(other_prefs_query)
        other_prefs = other_prefs_result.scalar_one_or_none()

        if other_prefs and other_prefs.open_to_new_people:
            scores.append(1.0)
            reasons.append("Open to meeting")
        else:
            scores.append(0.5)
        weights.append(0.15)

        # Calculate weighted average
        total_weight = sum(weights)
        weighted_sum = sum(s * w for s, w in zip(scores, weights))

        return weighted_sum / total_weight, reasons

    async def _calculate_preference_similarity(
        self,
        user_id: int,
        other_user_id: int
    ) -> float:
        """Calculate similarity between two users' preferences."""
        # Get both users' preferences
        query = select(UserPreferences).where(
            UserPreferences.user_id.in_([user_id, other_user_id])
        )
        result = await self.db.execute(query)
        prefs = {p.user_id: p for p in result.scalars().all()}

        if len(prefs) < 2:
            return 0.5  # Default if preferences not set

        user_pref = prefs.get(user_id)
        other_pref = prefs.get(other_user_id)

        if not user_pref or not other_pref:
            return 0.5

        similarities = []

        # Cuisine overlap
        user_cuisines = set(user_pref.cuisine_preferences or [])
        other_cuisines = set(other_pref.cuisine_preferences or [])
        if user_cuisines and other_cuisines:
            overlap = len(user_cuisines & other_cuisines)
            union = len(user_cuisines | other_cuisines)
            similarities.append(overlap / union if union > 0 else 0)

        # Price range overlap (using intersection over union for range similarity)
        price_intersection = max(0, (
            min(user_pref.max_price_level, other_pref.max_price_level) -
            max(user_pref.min_price_level, other_pref.min_price_level)
        ))
        price_union = (
            max(user_pref.max_price_level, other_pref.max_price_level) -
            min(user_pref.min_price_level, other_pref.min_price_level)
        )
        price_similarity = price_intersection / price_union if price_union > 0 else 1.0
        similarities.append(price_similarity)

        # Ambiance overlap
        user_ambiance = set(user_pref.preferred_ambiance or [])
        other_ambiance = set(other_pref.preferred_ambiance or [])
        if user_ambiance and other_ambiance:
            overlap = len(user_ambiance & other_ambiance)
            union = len(user_ambiance | other_ambiance)
            similarities.append(overlap / union if union > 0 else 0)

        return sum(similarities) / len(similarities) if similarities else 0.5

    # ============== INTEREST-BASED MATCHING ==============

    async def get_users_interested_in_venue(
        self,
        venue_id: int,
        exclude_user_id: Optional[int] = None,
        limit: int = 20
    ) -> List[dict]:
        """Get users who have expressed interest in a venue."""
        query = select(VenueInterest, User).join(
            User, VenueInterest.user_id == User.id
        ).where(
            and_(
                VenueInterest.venue_id == venue_id,
                VenueInterest.explicitly_interested == 1
            )
        )

        if exclude_user_id:
            query = query.where(VenueInterest.user_id != exclude_user_id)

        query = query.order_by(VenueInterest.created_at.desc()).limit(limit)

        result = await self.db.execute(query)
        rows = result.all()

        return [
            {
                "user_id": interest.user_id,
                "username": user.username,
                "full_name": user.full_name,
                "avatar_url": user.avatar_url,
                "interest_score": interest.interest_score,
                "preferred_time_slot": interest.preferred_time_slot,
                "open_to_invites": bool(interest.open_to_invites),
            }
            for interest, user in rows
        ]

    async def find_optimal_venue_for_group(
        self,
        user_ids: List[int]
    ) -> List[dict]:
        """
        Find the best venue for a group of users.

        Considers all users' preferences and finds compromise venues.
        """
        if not user_ids:
            return []

        # Get all users with preferences
        users_query = select(User, UserPreferences).outerjoin(
            UserPreferences, User.id == UserPreferences.user_id
        ).where(User.id.in_(user_ids))

        result = await self.db.execute(users_query)
        user_data = result.all()

        if not user_data:
            return []

        # Calculate group centroid
        lats = [u.latitude for u, _ in user_data if u.latitude]
        lons = [u.longitude for u, _ in user_data if u.longitude]

        centroid_lat = sum(lats) / len(lats) if lats else 40.7128
        centroid_lon = sum(lons) / len(lons) if lons else -74.0060

        # Aggregate preferences
        all_cuisines = []
        min_prices = []
        max_prices = []
        max_distances = []

        for user, prefs in user_data:
            if prefs:
                all_cuisines.extend(prefs.cuisine_preferences or [])
                min_prices.append(prefs.min_price_level)
                max_prices.append(prefs.max_price_level)
                max_distances.append(prefs.max_distance)

        # Find common cuisines
        cuisine_counts = {}
        for c in all_cuisines:
            cuisine_counts[c] = cuisine_counts.get(c, 0) + 1

        # Calculate bounds for spatial query
        avg_max_distance = sum(max_distances) / len(max_distances) if max_distances else 10.0
        
        # 1 degree lat is ~111km
        lat_delta = avg_max_distance / 111.0
        # 1 degree lon is ~111km * cos(lat)
        # Use simple bounding box for pre-filtering
        # Handle pole case safely
        cos_lat = math.cos(math.radians(centroid_lat))
        lon_delta = avg_max_distance / (111.0 * cos_lat) if abs(cos_lat) > 0.0001 else 180.0

        # Get venues within rough range and sufficient capacity
        venues_query = select(Venue).where(
            and_(
                Venue.capacity >= len(user_ids),
                Venue.latitude.between(centroid_lat - lat_delta, centroid_lat + lat_delta),
                Venue.longitude.between(centroid_lon - abs(lon_delta), centroid_lon + abs(lon_delta))
            )
        )
        
        venues_result = await self.db.execute(venues_query)
        venues = venues_result.scalars().all()

        scored_venues = []
        for venue in venues:
            score = self._calculate_group_venue_score(
                venue,
                centroid_lat,
                centroid_lon,
                cuisine_counts,
                min_prices,
                max_prices,
                max_distances,
                len(user_ids)
            )
            if score > 0:
                scored_venues.append({
                    "venue": venue,
                    "score": score
                })

        scored_venues.sort(key=lambda x: x["score"], reverse=True)

        return [
            {
                "id": v["venue"].id,
                "name": v["venue"].name,
                "category": v["venue"].category,
                "cuisine_type": v["venue"].cuisine_type,
                "rating": v["venue"].rating,
                "price_level": v["venue"].price_level,
                "group_score": round(v["score"], 3),
                "image_url": v["venue"].image_url,
            }
            for v in scored_venues[:10]
        ]

    def _calculate_group_venue_score(
        self,
        venue: Venue,
        centroid_lat: float,
        centroid_lon: float,
        cuisine_counts: dict,
        min_prices: List[int],
        max_prices: List[int],
        max_distances: List[float],
        group_size: int
    ) -> float:
        """Calculate how well a venue fits a group."""
        scores = []

        # Distance from group centroid
        distance = self.haversine_distance(
            centroid_lat, centroid_lon,
            venue.latitude, venue.longitude
        )
        avg_max_distance = sum(max_distances) / len(max_distances) if max_distances else 10
        if distance > avg_max_distance:
            return 0
        scores.append(1 - (distance / avg_max_distance))

        # Price compatibility
        avg_min = sum(min_prices) / len(min_prices) if min_prices else 1
        avg_max = sum(max_prices) / len(max_prices) if max_prices else 4
        if avg_min <= venue.price_level <= avg_max:
            scores.append(1.0)
        else:
            scores.append(0.3)

        # Cuisine preference match
        if venue.cuisine_type in cuisine_counts:
            cuisine_popularity = cuisine_counts[venue.cuisine_type] / group_size
            scores.append(cuisine_popularity)
        else:
            scores.append(0.3)

        # Capacity check - insufficient capacity disqualifies the venue
        if venue.capacity < group_size:
            return 0
        scores.append(1.0)

        # Rating
        scores.append(venue.rating / 5.0)

        return sum(scores) / len(scores)
