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
    return venues


@router.get("/trending", response_model=List[VenueResponse])
async def get_trending_venues(
    limit: int = Query(10, le=50),
    db: AsyncSession = Depends(get_db)
):
    """Get trending venues."""
    query = select(Venue).where(Venue.trending == True).order_by(
        Venue.popularity_score.desc()
    ).limit(limit)

    result = await db.execute(query)
    venues = result.scalars().all()
    return venues


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
    query = select(VenueInterest, User).join(
        User, VenueInterest.user_id == User.id
    ).where(
        VenueInterest.venue_id == venue_id,
        VenueInterest.explicitly_interested == 1
    ).limit(limit)

    result = await db.execute(query)
    rows = result.all()

    return [
        InterestedUserResponse(
            user_id=user.id,
            username=user.username,
            full_name=user.full_name,
            avatar_url=user.avatar_url,
            preferred_time_slot=interest.preferred_time_slot,
            open_to_invites=bool(interest.open_to_invites)
        )
        for interest, user in rows
    ]
