"""
API routes for Luna Social.
"""
from fastapi import APIRouter
from .routes import users, venues, recommendations, bookings, simulation, admin, reviews

api_router = APIRouter()

api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(venues.router, prefix="/venues", tags=["venues"])
api_router.include_router(recommendations.router, prefix="/recommendations", tags=["recommendations"])
api_router.include_router(bookings.router, prefix="/bookings", tags=["bookings"])
api_router.include_router(simulation.router, prefix="/simulation", tags=["simulation"])
api_router.include_router(admin.router, prefix="/admin", tags=["admin"])
api_router.include_router(reviews.router, prefix="/reviews", tags=["reviews"])
