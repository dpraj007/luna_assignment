"""
Simulation API routes.
"""
from typing import Optional, Literal
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, field_validator

from ...core.database import get_db
from ...core.config import settings
from ...agents.simulator_agent import SimulationOrchestrator, SimulationScenario

router = APIRouter()

# Singleton orchestrator
_orchestrator: Optional[SimulationOrchestrator] = None


async def get_orchestrator(db: AsyncSession = Depends(get_db)) -> SimulationOrchestrator:
    """Get or create simulation orchestrator."""
    global _orchestrator
    if _orchestrator is None:
        _orchestrator = SimulationOrchestrator(db)
    return _orchestrator


# Valid scenario values
VALID_SCENARIOS = [s.value for s in SimulationScenario]


class SimulationStartRequest(BaseModel):
    speed: float = 1.0
    scenario: Literal["normal", "lunch_rush", "friday_night", "weekend_brunch", "concert_night", "new_user_onboarding"] = "normal"

    @field_validator('speed')
    @classmethod
    def validate_speed(cls, v: float) -> float:
        if v <= 0:
            raise ValueError('Speed must be greater than 0')
        if v > settings.MAX_SIMULATION_SPEED:
            raise ValueError(f'Speed must not exceed {settings.MAX_SIMULATION_SPEED}')
        return v


class SimulationSpeedRequest(BaseModel):
    multiplier: float

    @field_validator('multiplier')
    @classmethod
    def validate_multiplier(cls, v: float) -> float:
        if v <= 0:
            raise ValueError('Speed multiplier must be greater than 0')
        if v > settings.MAX_SIMULATION_SPEED:
            raise ValueError(f'Speed multiplier must not exceed {settings.MAX_SIMULATION_SPEED}')
        return v


class ScenarioRequest(BaseModel):
    scenario: Literal["normal", "lunch_rush", "friday_night", "weekend_brunch", "concert_night", "new_user_onboarding"]


@router.post("/start")
async def start_simulation(
    request: SimulationStartRequest,
    orchestrator: SimulationOrchestrator = Depends(get_orchestrator)
):
    """Start the simulation."""
    result = await orchestrator.start(
        speed=request.speed,
        scenario=request.scenario
    )
    return result


@router.post("/pause")
async def pause_simulation(
    orchestrator: SimulationOrchestrator = Depends(get_orchestrator)
):
    """Pause the simulation."""
    result = await orchestrator.pause()
    return result


@router.post("/resume")
async def resume_simulation(
    orchestrator: SimulationOrchestrator = Depends(get_orchestrator)
):
    """Resume the simulation."""
    result = await orchestrator.resume()
    return result


@router.post("/stop")
async def stop_simulation(
    orchestrator: SimulationOrchestrator = Depends(get_orchestrator)
):
    """Stop the simulation."""
    result = await orchestrator.stop()
    return result


@router.post("/reset")
async def reset_simulation(
    orchestrator: SimulationOrchestrator = Depends(get_orchestrator)
):
    """Reset the simulation."""
    result = await orchestrator.reset()
    return result


@router.post("/speed")
async def set_simulation_speed(
    request: SimulationSpeedRequest,
    orchestrator: SimulationOrchestrator = Depends(get_orchestrator)
):
    """Set simulation speed multiplier."""
    result = await orchestrator.set_speed(request.multiplier)
    return result


@router.post("/scenario")
async def trigger_scenario(
    request: ScenarioRequest,
    orchestrator: SimulationOrchestrator = Depends(get_orchestrator)
):
    """Trigger a specific simulation scenario."""
    result = await orchestrator.trigger_scenario(request.scenario)
    return result


@router.get("/state")
async def get_simulation_state(
    orchestrator: SimulationOrchestrator = Depends(get_orchestrator)
):
    """Get current simulation state."""
    return await orchestrator.get_state()


@router.get("/metrics")
async def get_simulation_metrics(
    orchestrator: SimulationOrchestrator = Depends(get_orchestrator)
):
    """Get simulation metrics."""
    return await orchestrator.get_metrics()


@router.get("/scenarios")
async def list_scenarios():
    """List available simulation scenarios."""
    return {
        "scenarios": [
            {
                "id": "normal",
                "name": "Normal Day",
                "description": "Regular day-to-day activity patterns"
            },
            {
                "id": "lunch_rush",
                "name": "Lunch Rush",
                "description": "11:30 AM - 1:30 PM high activity, office workers seeking spots"
            },
            {
                "id": "friday_night",
                "name": "Friday Night Out",
                "description": "High social interaction, group formations, premium venues"
            },
            {
                "id": "weekend_brunch",
                "name": "Weekend Brunch",
                "description": "Leisurely browsing, larger groups, Instagram-worthy venues"
            },
            {
                "id": "concert_night",
                "name": "Concert Night",
                "description": "Event-driven dining, pre/post event recommendations"
            },
            {
                "id": "new_user_onboarding",
                "name": "New User Onboarding",
                "description": "Cold start demonstration, progressive learning"
            }
        ]
    }
