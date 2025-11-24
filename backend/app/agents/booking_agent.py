"""
Booking Agent - Handles automated reservations and bookings.

This agent is triggered when users express interest in going to a venue
together. It automatically creates bookings and manages invitations.
"""
from typing import TypedDict, List, Optional, Annotated
from datetime import datetime, timedelta
import random
import string
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from ..models.booking import Booking, BookingStatus, BookingInvitation
from ..models.venue import Venue
from ..models.user import User
from ..models.interaction import VenueInterest
from ..services.streaming import StreamingService, get_streaming_service


class BookingState(TypedDict):
    """State for the booking agent."""
    user_id: int
    venue_id: int
    party_size: int
    preferred_time: Optional[datetime]
    group_members: List[int]
    special_requests: Optional[str]
    booking: Optional[Booking]
    invitations_sent: List[int]
    status: str
    errors: List[str]


class BookingAgent:
    """
    AI Agent for automated booking management.

    Workflow:
    1. Validate venue availability
    2. Check user preferences
    3. Find compatible time slots
    4. Create booking
    5. Send invitations to group members
    6. Confirm booking
    """

    def __init__(self, db: AsyncSession):
        self.db = db
        self.streaming = get_streaming_service()

    def _generate_confirmation_code(self) -> str:
        """Generate unique confirmation code."""
        return ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))

    async def _validate_venue(self, state: BookingState) -> BookingState:
        """Validate venue exists and has availability."""
        query = select(Venue).where(Venue.id == state["venue_id"])
        result = await self.db.execute(query)
        venue = result.scalar_one_or_none()

        if not venue:
            state["errors"].append(f"Venue {state['venue_id']} not found")
            state["status"] = "failed"
            return state

        if not venue.accepts_reservations:
            state["errors"].append("Venue does not accept reservations")
            state["status"] = "failed"
            return state

        if venue.current_occupancy + state["party_size"] > venue.capacity:
            state["errors"].append("Venue at capacity")
            state["status"] = "failed"
            return state

        state["status"] = "venue_validated"
        return state

    async def _find_optimal_time(self, state: BookingState) -> BookingState:
        """Find optimal booking time based on preferences."""
        if state["status"] == "failed":
            return state

        # Use preferred time or find next available slot
        if state["preferred_time"]:
            booking_time = state["preferred_time"]
        else:
            # Default to next meal time
            now = datetime.utcnow()
            hour = now.hour

            if hour < 11:
                # Morning - schedule for lunch
                booking_time = now.replace(hour=12, minute=0, second=0, microsecond=0)
            elif hour < 17:
                # Afternoon - schedule for dinner
                booking_time = now.replace(hour=19, minute=0, second=0, microsecond=0)
            else:
                # Evening - schedule for next day lunch
                booking_time = (now + timedelta(days=1)).replace(hour=12, minute=0, second=0, microsecond=0)

        state["preferred_time"] = booking_time
        state["status"] = "time_selected"
        return state

    async def _create_booking(self, state: BookingState) -> BookingState:
        """Create the booking record."""
        if state["status"] == "failed":
            return state

        booking = Booking(
            user_id=state["user_id"],
            venue_id=state["venue_id"],
            party_size=state["party_size"],
            booking_time=state["preferred_time"],
            duration_minutes=90,
            status=BookingStatus.PENDING,
            group_members=state["group_members"],
            special_requests=state["special_requests"],
            confirmation_code=self._generate_confirmation_code(),
            created_by_agent="booking_agent"
        )

        self.db.add(booking)
        await self.db.flush()
        await self.db.refresh(booking)

        state["booking"] = booking
        state["status"] = "booking_created"

        # Publish event
        await self.streaming.publish_event(
            event_type="booking_created",
            channel="bookings",
            payload={
                "booking_id": booking.id,
                "venue_id": booking.venue_id,
                "user_id": booking.user_id,
                "party_size": booking.party_size,
                "confirmation_code": booking.confirmation_code,
            },
            simulation_time=datetime.utcnow(),
            user_id=booking.user_id,
            venue_id=booking.venue_id,
            booking_id=booking.id
        )

        return state

    async def _send_invitations(self, state: BookingState) -> BookingState:
        """Send invitations to group members."""
        if state["status"] == "failed" or not state["booking"]:
            return state

        invitations_sent = []

        for member_id in state["group_members"]:
            if member_id == state["user_id"]:
                continue  # Skip the organizer

            invitation = BookingInvitation(
                booking_id=state["booking"].id,
                inviter_id=state["user_id"],
                invitee_id=member_id,
                status="pending",
                message=f"You're invited to join us!"
            )

            self.db.add(invitation)
            invitations_sent.append(member_id)

            # Publish invitation event
            await self.streaming.publish_event(
                event_type="invite_sent",
                channel="social_interactions",
                payload={
                    "booking_id": state["booking"].id,
                    "inviter_id": state["user_id"],
                    "invitee_id": member_id,
                },
                simulation_time=datetime.utcnow(),
                user_id=member_id,
                booking_id=state["booking"].id
            )

        # await self.db.commit()  # Defer commit to confirmation step

        state["invitations_sent"] = invitations_sent
        state["status"] = "invitations_sent"
        return state

    async def _confirm_booking(self, state: BookingState) -> BookingState:
        """Confirm the booking."""
        if state["status"] == "failed" or not state["booking"]:
            return state

        state["booking"].status = BookingStatus.CONFIRMED
        await self.db.commit()

        state["status"] = "confirmed"

        # Publish confirmation event
        await self.streaming.publish_event(
            event_type="booking_confirmed",
            channel="bookings",
            payload={
                "booking_id": state["booking"].id,
                "confirmation_code": state["booking"].confirmation_code,
            },
            simulation_time=datetime.utcnow(),
            booking_id=state["booking"].id
        )

        return state

    async def create_booking(
        self,
        user_id: int,
        venue_id: int,
        party_size: int = 2,
        preferred_time: Optional[datetime] = None,
        group_members: Optional[List[int]] = None,
        special_requests: Optional[str] = None
    ) -> dict:
        """
        Execute the full booking workflow.

        Returns booking details or error information.
        """
        # Initialize state
        state: BookingState = {
            "user_id": user_id,
            "venue_id": venue_id,
            "party_size": party_size,
            "preferred_time": preferred_time,
            "group_members": group_members or [],
            "special_requests": special_requests,
            "booking": None,
            "invitations_sent": [],
            "status": "initiated",
            "errors": []
        }

        # Execute workflow steps
        state = await self._validate_venue(state)
        state = await self._find_optimal_time(state)
        state = await self._create_booking(state)
        state = await self._send_invitations(state)
        state = await self._confirm_booking(state)

        # Return result
        if state["status"] == "confirmed" and state["booking"]:
            return {
                "success": True,
                "booking_id": state["booking"].id,
                "confirmation_code": state["booking"].confirmation_code,
                "venue_id": state["venue_id"],
                "booking_time": state["preferred_time"].isoformat() if state["preferred_time"] else None,
                "party_size": state["party_size"],
                "invitations_sent": len(state["invitations_sent"]),
                "status": state["status"]
            }
        else:
            return {
                "success": False,
                "errors": state["errors"],
                "status": state["status"]
            }

    async def auto_book_interested_users(self, venue_id: int) -> List[dict]:
        """
        Automatically create bookings for users interested in a venue.

        Groups compatible users and creates bookings for them.
        """
        # Find users interested in this venue who are open to invites
        query = select(VenueInterest, User).join(
            User, VenueInterest.user_id == User.id
        ).where(
            VenueInterest.venue_id == venue_id,
            VenueInterest.explicitly_interested == 1,
            VenueInterest.open_to_invites == 1
        )

        result = await self.db.execute(query)
        interested = result.all()

        if len(interested) < 2:
            return []

        # Group users (simple grouping - pairs or small groups)
        bookings_created = []
        used_users = set()

        for i, (interest1, user1) in enumerate(interested):
            if user1.id in used_users:
                continue

            # Find a compatible partner
            group_members = [user1.id]
            used_users.add(user1.id)

            for j, (interest2, user2) in enumerate(interested[i+1:], i+1):
                if user2.id in used_users:
                    continue

                # Simple compatibility: same time slot preference
                if interest1.preferred_time_slot == interest2.preferred_time_slot:
                    group_members.append(user2.id)
                    used_users.add(user2.id)

                    if len(group_members) >= 4:  # Max group size
                        break

            if len(group_members) >= 2:
                # Create booking for this group
                result = await self.create_booking(
                    user_id=group_members[0],
                    venue_id=venue_id,
                    party_size=len(group_members),
                    group_members=group_members
                )
                bookings_created.append(result)

        return bookings_created
