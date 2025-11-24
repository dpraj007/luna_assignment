"""
Reviews API routes.
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel
from datetime import datetime

from ...core.database import get_db
from ...models.interaction import UserInteraction, InteractionType
from ...models.user import User
from ...models.venue import Venue
from ...models.user import Friendship

router = APIRouter()


class ReviewResponse(BaseModel):
    id: int
    user_id: int
    username: str
    avatar_url: Optional[str]
    venue_id: int
    venue_name: str
    venue_cuisine: Optional[str]
    rating: Optional[float]
    review_text: Optional[str]
    created_at: str
    is_friend: bool

    class Config:
        from_attributes = True


@router.get("/", response_model=List[ReviewResponse])
async def list_reviews(
    user_id: Optional[int] = Query(None, description="Filter by user ID"),
    venue_id: Optional[int] = Query(None, description="Filter by venue ID"),
    friends_only: bool = Query(False, description="Show only reviews from friends"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, le=100),
    db: AsyncSession = Depends(get_db)
):
    """Get all reviews with optional filtering."""
    # Build query for reviews
    query = select(
        UserInteraction.id,
        UserInteraction.user_id,
        UserInteraction.venue_id,
        UserInteraction.created_at,
        UserInteraction.interaction_metadata,
        User.username,
        User.avatar_url,
        Venue.name.label('venue_name'),
        Venue.cuisine_type.label('venue_cuisine')
    ).join(
        User, UserInteraction.user_id == User.id
    ).join(
        Venue, UserInteraction.venue_id == Venue.id
    ).where(
        UserInteraction.interaction_type == InteractionType.REVIEW
    )
    
    # Apply filters
    if user_id:
        query = query.where(UserInteraction.user_id == user_id)
    
    if venue_id:
        query = query.where(UserInteraction.venue_id == venue_id)
    
    # Get friend IDs if friends_only is True
    friend_ids = []
    if friends_only and user_id:
        friend_query = select(Friendship.friend_id).where(Friendship.user_id == user_id)
        friend_result = await db.execute(friend_query)
        friend_ids = [row[0] for row in friend_result.all()]
        if friend_ids:
            query = query.where(UserInteraction.user_id.in_(friend_ids))
        else:
            # No friends, return empty list
            return []
    
    query = query.order_by(UserInteraction.created_at.desc()).offset(skip).limit(limit)
    
    result = await db.execute(query)
    rows = result.all()
    
    # Get friend IDs for current user if user_id is provided (to mark is_friend)
    current_user_friend_ids = set()
    if user_id:
        friend_query = select(Friendship.friend_id).where(Friendship.user_id == user_id)
        friend_result = await db.execute(friend_query)
        current_user_friend_ids = {row[0] for row in friend_result.all()}
    
    reviews = []
    for row in rows:
        # Extract rating and review_text from metadata
        metadata = row.interaction_metadata or {}
        rating = metadata.get('rating')
        review_text = metadata.get('review_text') or metadata.get('text') or metadata.get('comment')
        
        reviews.append(ReviewResponse(
            id=row.id,
            user_id=row.user_id,
            username=row.username,
            avatar_url=row.avatar_url,
            venue_id=row.venue_id,
            venue_name=row.venue_name,
            venue_cuisine=row.venue_cuisine,
            rating=rating,
            review_text=review_text,
            created_at=row.created_at.isoformat() if isinstance(row.created_at, datetime) else str(row.created_at),
            is_friend=row.user_id in current_user_friend_ids if user_id else False
        ))
    
    return reviews


@router.get("/venue/{venue_id}", response_model=List[ReviewResponse])
async def get_venue_reviews(
    venue_id: int,
    user_id: Optional[int] = Query(None, description="Current user ID for friend detection"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, le=100),
    db: AsyncSession = Depends(get_db)
):
    """Get all reviews for a specific venue."""
    return await list_reviews(
        venue_id=venue_id,
        user_id=user_id,
        friends_only=False,
        skip=skip,
        limit=limit,
        db=db
    )

