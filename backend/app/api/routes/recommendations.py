"""
Recommendation API routes.
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel

from ...core.database import get_db
from ...agents.recommendation_agent import RecommendationAgent
from ...services.recommendation import RecommendationEngine

router = APIRouter()


class VenueRecommendation(BaseModel):
    id: int
    name: str
    category: Optional[str]
    cuisine_type: Optional[str]
    rating: float
    price_level: int
    distance_km: Optional[float]
    score: float
    image_url: Optional[str]
    latitude: float
    longitude: float
    ambiance: List[str]
    trending: bool


class PersonRecommendation(BaseModel):
    id: int
    username: str
    full_name: Optional[str]
    avatar_url: Optional[str]
    compatibility_score: float
    reasons: List[str]
    is_friend: bool
    activity_score: float


class RecommendationResponse(BaseModel):
    user_id: int
    venues: List[VenueRecommendation]
    people: List[PersonRecommendation]
    context: dict
    explanations: List[str]
    generated_at: str


class InterestRequest(BaseModel):
    user_id: int
    venue_id: int
    preferred_time_slot: Optional[str] = None
    open_to_invites: bool = True


class InterestResponse(BaseModel):
    success: bool
    venue_id: int
    others_interested: List[dict]
    message: str


@router.get("", response_model=RecommendationResponse)
async def get_recommendations(
    user_id: int = Query(...),
    include_people: bool = True,
    db: AsyncSession = Depends(get_db)
):
    """Get personalized recommendations for a user."""
    agent = RecommendationAgent(db)
    try:
        result = await agent.get_recommendations(
            user_id=user_id,
            include_people=include_people
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/user/{user_id}/people")
async def get_user_people_recommendations(
    user_id: int,
    venue_id: Optional[int] = Query(None),
    limit: int = Query(10, le=50),
    db: AsyncSession = Depends(get_db)
):
    """Get compatible people recommendations for a specific user."""
    engine = RecommendationEngine(db)
    try:
        people = await engine.get_compatible_users(
            user_id=user_id,
            venue_id=venue_id,
            limit=limit
        )
        # Transform to match frontend SocialMatch format
        result = []
        for person in people:
            result.append({
                "user": {
                    "id": person["id"],
                    "username": person["username"],
                    "full_name": person.get("full_name"),
                    "avatar_url": person.get("avatar_url"),
                },
                "compatibility_score": person["compatibility_score"],
                "shared_interests": person.get("reasons", []),
                "reasoning": ", ".join(person.get("reasons", [])) if person.get("reasons") else None
            })
        return result
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/user/{user_id}", response_model=RecommendationResponse)
async def get_user_recommendations(
    user_id: int,
    include_people: bool = True,
    db: AsyncSession = Depends(get_db)
):
    """Get personalized recommendations for a specific user (path parameter version)."""
    agent = RecommendationAgent(db)
    try:
        result = await agent.get_recommendations(
            user_id=user_id,
            include_people=include_people
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/{user_id}/venues")
async def get_venue_recommendations(
    user_id: int,
    limit: int = Query(10, le=50),
    category: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    """Get venue recommendations for a user."""
    engine = RecommendationEngine(db)
    filters = {}
    if category:
        filters["category"] = category

    venues = await engine.get_venue_recommendations(
        user_id=user_id,
        limit=limit,
        filters=filters if filters else None
    )
    return {"venues": venues}


@router.get("/compatible")
async def get_people_recommendations(
    user_id: int = Query(...),
    venue_id: Optional[int] = None,
    limit: int = Query(10, le=50),
    db: AsyncSession = Depends(get_db)
):
    """Get compatible people recommendations."""
    engine = RecommendationEngine(db)
    people = await engine.get_compatible_users(
        user_id=user_id,
        venue_id=venue_id,
        limit=limit
    )
    return {"people": people}


@router.post("/interest", response_model=InterestResponse)
async def express_interest(
    request: InterestRequest,
    db: AsyncSession = Depends(get_db)
):
    """Express interest in a venue."""
    agent = RecommendationAgent(db)
    try:
        result = await agent.express_interest(
            user_id=request.user_id,
            venue_id=request.venue_id,
            preferred_time_slot=request.preferred_time_slot,
            open_to_invites=request.open_to_invites
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/group")
async def get_group_venue_recommendations(
    user_ids: str = Query(...),
    db: AsyncSession = Depends(get_db)
):
    """Get optimal venue for a group of users."""
    try:
        ids = [int(uid.strip()) for uid in user_ids.split(",")]
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid user IDs format")

    engine = RecommendationEngine(db)
    venues = await engine.find_optimal_venue_for_group(ids)
    return {"group_venues": venues, "group_size": len(ids)}
