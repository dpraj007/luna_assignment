# Backend Quick Start Guide

Get the Luna Social API server running in under 3 minutes.

## Prerequisites

- **Python** 3.10+ (check with `python --version`)
- **pip** (check with `pip --version`)

## Quick Start

```bash
# 1. Navigate to backend directory
cd backend

# 2. Create virtual environment
python -m venv venv

# 3. Activate virtual environment
source venv/bin/activate  # Linux/Mac
# OR
venv\Scripts\activate     # Windows

# 4. Install dependencies
pip install -r requirements.txt

# 5. Start the server
uvicorn app.main:app --reload --port 8000
```

The API will be available at **http://localhost:8000**

API Documentation: **http://localhost:8000/docs**

## Available Commands

| Command | Description |
|---------|-------------|
| `uvicorn app.main:app --reload --port 8000` | Start dev server with hot reload |
| `uvicorn app.main:app --host 0.0.0.0 --port 8000` | Start production server |
| `pytest ../tests/ -v` | Run all tests |
| `pytest ../tests/layer3_backend/ -v` | Run backend tests only |

## Environment Setup (Optional)

Copy the example environment file:
```bash
cp .env.example .env
```

Default settings work out of the box. Key variables:

```bash
# Database (SQLite by default - no setup needed)
DATABASE_URL="sqlite+aiosqlite:///./luna_social.db"

# Streaming (in-memory by default - no Redis needed)
USE_FAKE_REDIS=true
STREAM_BACKEND="memory"

# Optional: LLM for AI agents (not required for demo)
OPENROUTER_API_KEY="sk-or-v1-..."
```

## Tech Stack

- **FastAPI** - Modern async web framework
- **SQLAlchemy 2.0** - Async ORM
- **Pydantic** - Data validation
- **Uvicorn** - ASGI server
- **LangGraph** - AI agent orchestration
- **SSE-Starlette** - Server-Sent Events for real-time streaming

## Project Structure

```
backend/
├── app/
│   ├── main.py              # FastAPI entry point
│   ├── api/
│   │   └── routes/          # API endpoints
│   │       ├── users.py         # User management
│   │       ├── venues.py        # Venue data
│   │       ├── recommendations.py # Recommendations
│   │       ├── bookings.py      # Booking system
│   │       ├── simulation.py    # Simulation control
│   │       └── admin.py         # Admin & streaming
│   ├── agents/              # AI agents
│   │   ├── booking_agent.py     # Automated bookings
│   │   ├── recommendation_agent.py
│   │   ├── simulator_agent.py   # User behavior simulation
│   │   └── simulator_graph.py   # LangGraph orchestrator
│   ├── core/
│   │   ├── config.py        # Settings
│   │   └── database.py      # Database setup
│   ├── models/              # SQLAlchemy models
│   └── services/            # Business logic
│       ├── recommendation.py    # Recommendation engine
│       ├── streaming.py         # Event streaming
│       └── data_generator.py    # Demo data seeding
├── requirements.txt
└── .env.example
```

## Quick API Test

After starting the server, try these commands:

```bash
# 1. Seed the database with demo data
curl -X POST "http://localhost:8000/api/v1/admin/data/seed?user_count=50"

# 2. Get all users
curl "http://localhost:8000/api/v1/users/"

# 3. Get recommendations for user 1
curl "http://localhost:8000/api/v1/recommendations/1"

# 4. Start a simulation
curl -X POST "http://localhost:8000/api/v1/simulation/start" \
  -H "Content-Type: application/json" \
  -d '{"scenario": "happy_hour_rush", "speed_multiplier": 10}'

# 5. Watch real-time events (keep terminal open)
curl "http://localhost:8000/api/v1/admin/streams/subscribe-all"
```

## Key API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/admin/data/seed` | POST | Seed database with demo data |
| `/api/v1/users/` | GET | List all users |
| `/api/v1/venues/` | GET | List all venues |
| `/api/v1/recommendations/{user_id}` | GET | Get recommendations |
| `/api/v1/bookings/` | POST | Create a booking |
| `/api/v1/simulation/start` | POST | Start simulation |
| `/api/v1/simulation/stop` | POST | Stop simulation |
| `/api/v1/admin/streams/subscribe-all` | GET | SSE event stream |
| `/docs` | GET | Interactive API docs |

## Simulation Scenarios

Available scenarios for `POST /api/v1/simulation/start`:
- `happy_hour_rush` - Evening dining surge
- `weekend_brunch` - Weekend morning activity
- `random_activity` - Random user behaviors
- `group_coordination` - Group booking patterns
- `preference_drift` - Evolving user preferences

## Troubleshooting

### Port 8000 already in use
```bash
# Find and kill the process
lsof -i :8000
kill -9 <PID>
```

### Module not found errors
```bash
# Ensure virtual environment is activated
source venv/bin/activate
pip install -r requirements.txt
```

### Database errors
```bash
# Remove existing database and restart
rm luna_social.db
uvicorn app.main:app --reload --port 8000
```

### Import errors with app module
```bash
# Run from the backend directory
cd /path/to/backend
uvicorn app.main:app --reload --port 8000
```

## Running Tests

```bash
# Activate virtual environment first
source venv/bin/activate

# Run all tests
pytest ../tests/ -v

# Run specific test layers
pytest ../tests/layer1_inference/ -v  # ML algorithm tests
pytest ../tests/layer2_agents/ -v     # Agent behavior tests
pytest ../tests/layer3_backend/ -v    # Database tests
pytest ../tests/layer4_api/ -v        # API integration tests
```

## Next Steps

1. Start the frontend dashboard (see `frontend/QUICKSTART.md`)
2. Open http://localhost:3000 to see the live dashboard
3. Explore the API docs at http://localhost:8000/docs
4. Run simulations and watch real-time updates!
