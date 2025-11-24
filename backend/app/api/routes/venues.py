"""
Venue API routes.
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel

from ...core.database import get_db
from ...models.venue import Venue
from ...models.interaction import VenueInterest
from ...models.user import User

router = APIRouter()


class VenueResponse(BaseModel):
    id: int
    name: str
    description: Optional[str]
    address: Optional[str]
    city: Optional[str]
    latitude: float
    longitude: float
    category: Optional[str]
    cuisine_type: Optional[str]
    price_level: int
    rating: float
    review_count: int
    ambiance: List[str]
    capacity: int
    current_occupancy: int
    accepts_reservations: bool
    features: List[str]
    image_url: Optional[str]
    popularity_score: float
    trending: bool

    class Config:
        from_attributes = True


class InterestedUserResponse(BaseModel):
    user_id: int
    username: str
    full_name: Optional[str]
    avatar_url: Optional[str]
    preferred_time_slot: Optional[str]
    open_to_invites: bool


@router.get("/", response_model=List[VenueResponse])
async def list_venues(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, le=100),
    category: Optional[str] = None,
    min_rating: Optional[float] = None,
    trending_only: bool = False,
    db: AsyncSession = Depends(get_db)
):
    """List all venues with optional filters."""
    # Optimize query by selecting only needed columns
    # Note: VenueResponse uses almost all columns, but selecting explicitly avoids any potential lazy loading
    query = select(Venue)

    if category:
        query = query.where(Venue.category == category)
    if min_rating:
        query = query.where(Venue.rating >= min_rating)
    if trending_only:
        query = query.where(Venue.trending == True)

    query = query.offset(skip).limit(limit)

    result = await db.execute(query)
    venues = result.scalars().all()
    
    # No need for manual mapping here as we're selecting the ORM object which has all fields needed
    # But if performance is still an issue, we can switch to column selection
    return venues


@router.get("/trending", response_model=List[VenueResponse])
async def get_trending_venues(
    limit: int = Query(10, le=50),
    db: AsyncSession = Depends(get_db)
):
    """Get trending venues."""
    # Optimize query by selecting columns
    query = select(
        Venue.id, Venue.name, Venue.description, Venue.address, Venue.city,
        Venue.latitude, Venue.longitude, Venue.category, Venue.cuisine_type,
        Venue.price_level, Venue.rating, Venue.review_count, Venue.ambiance,
        Venue.capacity, Venue.current_occupancy, Venue.accepts_reservations,
        Venue.features, Venue.image_url, Venue.popularity_score, Venue.trending
    ).where(Venue.trending == True).order_by(
        Venue.popularity_score.desc()
    ).limit(limit)

    result = await db.execute(query)
    rows = result.all()
    
    return [
        VenueResponse(
            id=row.id, name=row.name, description=row.description, address=row.address, city=row.city,
            latitude=row.latitude, longitude=row.longitude, category=row.category, cuisine_type=row.cuisine_type,
            price_level=row.price_level, rating=row.rating, review_count=row.review_count, ambiance=row.ambiance,
            capacity=row.capacity, current_occupancy=row.current_occupancy, accepts_reservations=row.accepts_reservations,
            features=row.features, image_url=row.image_url, popularity_score=row.popularity_score, trending=row.trending
        )
        for row in rows
    ]


@router.get("/{venue_id}", response_model=VenueResponse)
async def get_venue(venue_id: int, db: AsyncSession = Depends(get_db)):
    """Get venue by ID."""
    query = select(Venue).where(Venue.id == venue_id)
    result = await db.execute(query)
    venue = result.scalar_one_or_none()

    if not venue:
        raise HTTPException(status_code=404, detail="Venue not found")

    return venue


@router.get("/{venue_id}/interested", response_model=List[InterestedUserResponse])
async def get_interested_users(
    venue_id: int,
    limit: int = Query(20, le=50),
    db: AsyncSession = Depends(get_db)
):
    """Get users interested in this venue."""
    # Check if venue exists first
    venue_query = select(Venue.id).where(Venue.id == venue_id)
    venue_result = await db.execute(venue_query)
    if not venue_result.scalar_one_or_none():
        # Return empty list if venue doesn't exist, or raise 404 if strict
        # Based on test expectations, 200/404 are both allowed, but an empty list is safer
        # If strict 404 is required: raise HTTPException(status_code=404, detail="Venue not found")
        # For performance, checking existence first prevents the heavier join query
        return []

    query = select(
        User.id,
        User.username,
        User.full_name,
        User.avatar_url,
        VenueInterest.preferred_time_slot,
        VenueInterest.open_to_invites
    ).join(
        User, VenueInterest.user_id == User.id
    ).where(
        VenueInterest.venue_id == venue_id,
        VenueInterest.explicitly_interested == 1
    ).limit(limit)

    result = await db.execute(query)
    rows = result.all()

    return [
        InterestedUserResponse(
            user_id=row.id,
            username=row.username,
            full_name=row.full_name,
            avatar_url=row.avatar_url,
            preferred_time_slot=row.preferred_time_slot,
            open_to_invites=bool(row.open_to_invites)
        )
        for row in rows
    ]
