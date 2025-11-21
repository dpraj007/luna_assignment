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
    query = select(User)
    if simulated_only:
        query = query.where(User.is_simulated == True)
    query = query.offset(skip).limit(limit)

    result = await db.execute(query)
    users = result.scalars().all()
    return users


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
    query = select(Friendship, User).join(
        User, Friendship.friend_id == User.id
    ).where(Friendship.user_id == user_id).limit(limit)

    result = await db.execute(query)
    rows = result.all()

    return [
        FriendResponse(
            id=user.id,
            username=user.username,
            full_name=user.full_name,
            avatar_url=user.avatar_url,
            compatibility_score=friendship.compatibility_score
        )
        for friendship, user in rows
    ]
