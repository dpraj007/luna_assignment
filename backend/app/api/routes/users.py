"""
User API routes.
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel

from ...core.database import get_db
from ...models.user import User, UserPreferences, Friendship

router = APIRouter()


class UserResponse(BaseModel):
    id: int
    username: str
    full_name: Optional[str]
    email: str
    avatar_url: Optional[str]
    city: Optional[str]
    activity_score: float
    social_score: float
    is_simulated: bool

    class Config:
        from_attributes = True


class UserPreferencesResponse(BaseModel):
    cuisine_preferences: List[str]
    min_price_level: int
    max_price_level: int
    preferred_ambiance: List[str]
    dietary_restrictions: List[str]
    preferred_group_size: int
    open_to_new_people: bool
    max_distance: float

    class Config:
        from_attributes = True


class FriendResponse(BaseModel):
    id: int
    username: str
    full_name: Optional[str]
    avatar_url: Optional[str]
    compatibility_score: float

    class Config:
        from_attributes = True


@router.get("/", response_model=List[UserResponse])
async def list_users(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, le=100),
    simulated_only: bool = False,
    db: AsyncSession = Depends(get_db)
):
    """List all users."""
    # Optimize query by selecting only needed columns
    query = select(
        User.id,
        User.username,
        User.full_name,
        User.email,
        User.avatar_url,
        User.city,
        User.activity_score,
        User.social_score,
        User.is_simulated
    )
    if simulated_only:
        query = query.where(User.is_simulated == True)
    query = query.offset(skip).limit(limit)

    result = await db.execute(query)
    users = result.all()
    
    # Map row results to UserResponse model manually or via dict
    # Since we selected specific columns, the result is a list of Row objects
    # which behave like tuples/dicts
    return [
        UserResponse(
            id=row.id,
            username=row.username,
            full_name=row.full_name,
            email=row.email,
            avatar_url=row.avatar_url,
            city=row.city,
            activity_score=row.activity_score,
            social_score=row.social_score,
            is_simulated=row.is_simulated
        )
        for row in users
    ]


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(user_id: int, db: AsyncSession = Depends(get_db)):
    """Get user by ID."""
    query = select(User).where(User.id == user_id)
    result = await db.execute(query)
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return user


@router.get("/{user_id}/preferences", response_model=UserPreferencesResponse)
async def get_user_preferences(user_id: int, db: AsyncSession = Depends(get_db)):
    """Get user preferences."""
    query = select(UserPreferences).where(UserPreferences.user_id == user_id)
    result = await db.execute(query)
    prefs = result.scalar_one_or_none()

    if not prefs:
        raise HTTPException(status_code=404, detail="Preferences not found")

    return prefs


@router.get("/{user_id}/friends", response_model=List[FriendResponse])
async def get_user_friends(
    user_id: int,
    limit: int = Query(20, le=50),
    db: AsyncSession = Depends(get_db)
):
    """Get user's friends."""
    # Optimize query to select only necessary columns
    query = select(
        Friendship.compatibility_score,
        User.id,
        User.username,
        User.full_name,
        User.avatar_url
    ).join(
        User, Friendship.friend_id == User.id
    ).where(Friendship.user_id == user_id).limit(limit)

    result = await db.execute(query)
    rows = result.all()

    return [
        FriendResponse(
            id=row.id,
            username=row.username,
            full_name=row.full_name,
            avatar_url=row.avatar_url,
            compatibility_score=row.compatibility_score
        )
        for row in rows
    ]
