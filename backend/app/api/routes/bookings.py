"""
Booking API routes.
"""
from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel

from ...core.database import get_db
from ...models.booking import Booking, BookingStatus, BookingInvitation
from ...models.user import User
from ...agents.booking_agent import BookingAgent

router = APIRouter()


class BookingRequest(BaseModel):
    venue_id: int
    party_size: int = 2
    preferred_time: Optional[datetime] = None
    group_members: Optional[List[int]] = None
    special_requests: Optional[str] = None


class BookingResponse(BaseModel):
    id: int
    user_id: int
    venue_id: int
    party_size: int
    booking_time: datetime
    status: str
    confirmation_code: Optional[str]
    group_members: List[int]
    created_by_agent: Optional[str]

    class Config:
        from_attributes = True


class CreateBookingResponse(BaseModel):
    success: bool
    booking_id: Optional[int] = None
    confirmation_code: Optional[str] = None
    venue_id: Optional[int] = None
    booking_time: Optional[str] = None
    party_size: Optional[int] = None
    invitations_sent: Optional[int] = None
    status: str
    errors: Optional[List[str]] = None


@router.get("/", response_model=List[BookingResponse])
async def list_bookings(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, le=100),
    status: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    """List all bookings."""
    query = select(Booking)

    if status:
        query = query.where(Booking.status == BookingStatus(status))

    query = query.order_by(Booking.created_at.desc()).offset(skip).limit(limit)

    result = await db.execute(query)
    bookings = result.scalars().all()
    return bookings


@router.get("/{booking_id}", response_model=BookingResponse)
async def get_booking(booking_id: int, db: AsyncSession = Depends(get_db)):
    """Get booking by ID."""
    query = select(Booking).where(Booking.id == booking_id)
    result = await db.execute(query)
    booking = result.scalar_one_or_none()

    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")

    return booking


@router.post("/{user_id}/create", response_model=CreateBookingResponse)
async def create_booking(
    user_id: int,
    request: BookingRequest,
    db: AsyncSession = Depends(get_db)
):
    """Create a new booking using the booking agent."""
    # Validate that the user exists (optimized check)
    user_query = select(User.id).where(User.id == user_id)
    user_result = await db.execute(user_query)
    if not user_result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="User not found")

    agent = BookingAgent(db)
    result = await agent.create_booking(
        user_id=user_id,
        venue_id=request.venue_id,
        party_size=request.party_size,
        preferred_time=request.preferred_time,
        group_members=request.group_members,
        special_requests=request.special_requests
    )

    if not result["success"]:
        error_msg = "Booking failed"
        if result.get("errors"):
            error_msg = ", ".join(result["errors"])
            
        # Check for specific errors to determine status code
        status_code = 400
        for error in result.get("errors", []):
            if "not found" in error.lower():
                status_code = 404
                break
            elif "capacity" in error.lower() or "reservations" in error.lower():
                status_code = 422
                break
        
        raise HTTPException(status_code=status_code, detail=error_msg)

    return result


@router.get("/user/{user_id}", response_model=List[BookingResponse])
async def get_user_bookings(
    user_id: int,
    status: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    """Get bookings for a specific user."""
    query = select(Booking).where(Booking.user_id == user_id)

    if status:
        query = query.where(Booking.status == BookingStatus(status))

    query = query.order_by(Booking.booking_time.desc())

    result = await db.execute(query)
    bookings = result.scalars().all()
    return bookings


@router.post("/{booking_id}/cancel")
async def cancel_booking(booking_id: int, db: AsyncSession = Depends(get_db)):
    """Cancel a booking."""
    query = select(Booking).where(Booking.id == booking_id)
    result = await db.execute(query)
    booking = result.scalar_one_or_none()

    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")

    if booking.status == BookingStatus.CANCELLED:
        raise HTTPException(status_code=400, detail="Booking already cancelled")

    booking.status = BookingStatus.CANCELLED
    await db.commit()

    return {"success": True, "booking_id": booking_id, "status": "cancelled"}


@router.post("/venue/{venue_id}/auto-book")
async def auto_book_venue(venue_id: int, db: AsyncSession = Depends(get_db)):
    """
    Automatically create bookings for users interested in a venue.
    Uses the booking agent to match and book compatible users.
    """
    agent = BookingAgent(db)
    bookings = await agent.auto_book_interested_users(venue_id)
    return {
        "success": True,
        "venue_id": venue_id,
        "bookings_created": len(bookings),
        "bookings": bookings
    }
