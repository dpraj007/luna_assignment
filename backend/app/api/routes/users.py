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
    try:
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
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Failed to fetch users: {str(e)}")


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


class CreateFriendshipRequest(BaseModel):
    friend_id: int


@router.post("/{user_id}/friends", response_model=dict)
async def create_friendship(
    user_id: int,
    request: CreateFriendshipRequest,
    db: AsyncSession = Depends(get_db)
):
    """Create a friendship connection between users."""
    from sqlalchemy import and_
    
    # Check if friendship already exists
    existing_query = select(Friendship).where(
        and_(
            Friendship.user_id == user_id,
            Friendship.friend_id == request.friend_id
        )
    )
    existing_result = await db.execute(existing_query)
    existing = existing_result.scalar_one_or_none()
    
    if existing:
        raise HTTPException(status_code=400, detail="Friendship already exists")
    
    # Check if trying to friend self
    if user_id == request.friend_id:
        raise HTTPException(status_code=400, detail="Cannot friend yourself")
    
    # Check if friend user exists
    friend_query = select(User).where(User.id == request.friend_id)
    friend_result = await db.execute(friend_query)
    friend_user = friend_result.scalar_one_or_none()
    
    if not friend_user:
        raise HTTPException(status_code=404, detail="Friend user not found")
    
    # Create friendship (calculate compatibility score - simplified for now)
    # In a real app, you'd calculate this based on preferences, mutual friends, etc.
    compatibility_score = 0.7  # Default score
    
    friendship = Friendship(
        user_id=user_id,
        friend_id=request.friend_id,
        compatibility_score=compatibility_score,
        status="active"
    )
    
    db.add(friendship)
    await db.commit()
    await db.refresh(friendship)
    
    return {
        "success": True,
        "message": f"Successfully connected with {friend_user.username}",
        "friendship_id": friendship.id
    }


class FriendActivityResponse(BaseModel):
    user_id: int
    user: dict  # {username, avatar_url}
    activity_type: str  # 'booking', 'review', 'interest'
    venue: Optional[dict]  # {id, name, cuisine}
    timestamp: str

    class Config:
        from_attributes = True


@router.get("/{user_id}/activity", response_model=List[FriendActivityResponse])
async def get_friend_activity(
    user_id: int,
    limit: int = Query(20, le=50),
    db: AsyncSession = Depends(get_db)
):
    """Get recent activity from user's friends."""
    from ...models.booking import Booking, BookingStatus
    from ...models.interaction import UserInteraction, VenueInterest, InteractionType
    from ...models.venue import Venue
    from datetime import datetime, timedelta
    
    try:
        # Get friend IDs
        friend_query = select(Friendship.friend_id).where(Friendship.user_id == user_id)
        friend_result = await db.execute(friend_query)
        friend_ids = [row[0] for row in friend_result.all()]
        
        if not friend_ids:
            return []
        
        activities = []
        
        # Get recent bookings from friends (last 30 days for testing)
        cutoff_time = datetime.utcnow() - timedelta(days=30)
        booking_query = select(
            Booking.user_id,
            Booking.venue_id,
            Booking.created_at,
            User.username,
            User.avatar_url,
            Venue.name.label('venue_name'),
            Venue.cuisine_type
        ).join(
            User, Booking.user_id == User.id
        ).join(
            Venue, Booking.venue_id == Venue.id
        ).where(
            Booking.user_id.in_(friend_ids),
            Booking.created_at >= cutoff_time
        ).order_by(Booking.created_at.desc()).limit(limit)
        
        booking_result = await db.execute(booking_query)
        for row in booking_result.all():
            activities.append({
                'user_id': row.user_id,
                'user': {'username': row.username, 'avatar_url': row.avatar_url},
                'activity_type': 'booking',
                'venue': {'id': row.venue_id, 'name': row.venue_name, 'cuisine': row.cuisine_type},
                'timestamp': row.created_at.isoformat()
            })
        
        # Get recent reviews from friends
        review_query = select(
            UserInteraction.user_id,
            UserInteraction.venue_id,
            UserInteraction.created_at,
            User.username,
            User.avatar_url,
            Venue.name.label('venue_name'),
            Venue.cuisine_type
        ).join(
            User, UserInteraction.user_id == User.id
        ).join(
            Venue, UserInteraction.venue_id == Venue.id
        ).where(
            UserInteraction.user_id.in_(friend_ids),
            UserInteraction.interaction_type == InteractionType.REVIEW,
            UserInteraction.created_at >= cutoff_time
        ).order_by(UserInteraction.created_at.desc()).limit(limit)
        
        review_result = await db.execute(review_query)
        for row in review_result.all():
            activities.append({
                'user_id': row.user_id,
                'user': {'username': row.username, 'avatar_url': row.avatar_url},
                'activity_type': 'review',
                'venue': {'id': row.venue_id, 'name': row.venue_name, 'cuisine': row.cuisine_type},
                'timestamp': row.created_at.isoformat()
            })
        
        # Get recent venue interests from friends
        interest_query = select(
            VenueInterest.user_id,
            VenueInterest.venue_id,
            VenueInterest.created_at,
            User.username,
            User.avatar_url,
            Venue.name.label('venue_name'),
            Venue.cuisine_type
        ).join(
            User, VenueInterest.user_id == User.id
        ).join(
            Venue, VenueInterest.venue_id == Venue.id
        ).where(
            VenueInterest.user_id.in_(friend_ids),
            VenueInterest.explicitly_interested == 1,
            VenueInterest.created_at >= cutoff_time
        ).order_by(VenueInterest.created_at.desc()).limit(limit)
        
        interest_result = await db.execute(interest_query)
        for row in interest_result.all():
            activities.append({
                'user_id': row.user_id,
                'user': {'username': row.username, 'avatar_url': row.avatar_url},
                'activity_type': 'interest',
                'venue': {'id': row.venue_id, 'name': row.venue_name, 'cuisine': row.cuisine_type},
                'timestamp': row.created_at.isoformat()
            })
        
        # Sort all activities by timestamp and limit
        activities.sort(key=lambda x: x['timestamp'], reverse=True)
        return activities[:limit]
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))
