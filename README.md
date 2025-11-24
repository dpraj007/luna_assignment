# Luna Social - Backend Platform

A sophisticated AI-powered backend platform for social dining experiences, featuring intelligent recommendations, automated bookings, and real-time simulation capabilities.

## Track 2: Backend Implementation

This implementation focuses on **Track 2: Backend** with emphasis on:
- AI Agents and Recommendation Algorithms
- Spatial Analysis for venue recommendations
- Social Compatibility scoring
- Automated booking agents

## Architecture Overview

```
┌──────────────────────────────┬──────────────────────────────────────┐
│     User View (Next.js)      │      Admin Dashboard (React)         │
│  Personalized Feed │ Booking │  Metrics │ Controls │ Agent Views   │
└──────────────────────────────┴──────────────────────────────────────┘
                    │                           │
                    └─────────SSE/WebSocket─────┘
                                    │
┌─────────────────────────────────────────────────────────────────────┐
│                         FastAPI Backend                              │
├─────────────────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐                  │
│  │ Recommend.  │  │  Booking    │  │ Simulation  │                  │
│  │   Agent     │  │   Agent     │  │   Agent     │                  │
│  └─────────────┘  └─────────────┘  └─────────────┘                  │
│         │               │               │                           │
│  ┌─────────────────────────────────────────────────┐               │
│  │           Recommendation Engine                  │               │
│  │   • Spatial Analysis (Haversine distance)       │               │
│  │   • Social Compatibility (Graph analysis)       │               │
│  │   • Preference Matching (ML-ready)              │               │
│  │   • LightGCN (Graph Neural Network)             │               │
│  │   • Hybrid Scoring (70% rule-based + 30% GNN)  │               │
│  └─────────────────────────────────────────────────┘               │
│                           │                                         │
│  ┌─────────────────────────────────────────────────┐               │
│  │           Streaming Service                      │               │
│  │   • Redis Streams / In-Memory backend           │               │
│  │   • Server-Sent Events (SSE)                    │               │
│  │   • Real-time event distribution                │               │
│  └─────────────────────────────────────────────────┘               │
└─────────────────────────────────────────────────────────────────────┘
                                    │
┌─────────────────────────────────────────────────────────────────────┐
│                    SQLite/PostgreSQL Database                        │
│   Users │ Venues │ Bookings │ Friendships │ Interactions │ Events   │
└─────────────────────────────────────────────────────────────────────┘
```

## Features Implemented

### 1. Recommendation Engine

**Spatial Analysis:**
- Haversine distance calculations for accurate venue proximity
- Location-based filtering with configurable radius
- Group centroid optimization for multi-user gatherings

**Social Compatibility:**
- Friend network analysis
- Mutual connection scoring
- Preference similarity algorithms (Jaccard similarity)
- Activity pattern matching
- Openness to new connections factor

**Contextual Recommendations:**
- Time-of-day awareness (breakfast, lunch, dinner, late-night)
- Weekend vs. weekday behavior patterns
- Trending venue detection
- Price-level matching

**Graph Neural Network (LightGCN):**
- Social-aware learning from user-venue interactions
- Friendship graph propagation for preference learning
- Hybrid scoring: 70% rule-based + 30% GNN predictions
- Automatic graph building from SQL relational data
- BPR (Bayesian Personalized Ranking) loss optimization
- Production-ready with graceful fallbacks

See [`docs/GNN_IMPLEMENTATION.md`](docs/GNN_IMPLEMENTATION.md) for detailed GNN documentation.

### 2. AI Agents

**Booking Agent:**
- Automated reservation creation
- Group booking coordination
- Invitation management
- Confirmation code generation
- Status tracking (pending, confirmed, cancelled, completed)

**Recommendation Agent:**
- Context-aware suggestion generation
- Explanation generation for recommendations
- Interest tracking and learning
- User interaction logging

**Simulator Agent:**
- User persona simulation (7 archetypes):
  - Social Butterfly
  - Foodie Explorer
  - Routine Regular
  - Event Organizer
  - Spontaneous Diner
  - Busy Professional
  - Budget Conscious
- Behavior probability modeling
- Real-time action generation

### 3. Simulation System

**Pre-programmed Scenarios:**
- Normal Day: Regular activity patterns
- Lunch Rush: High booking activity 11:30 AM - 1:30 PM
- Friday Night: Social interaction surge
- Weekend Brunch: Leisurely group formations
- Concert Night: Event-driven recommendations

**Features:**
- Adjustable speed multiplier (1x - 100x)
- Pause/Resume controls
- Real-time metrics tracking
- Event streaming to dashboard

### 4. Real-time Streaming

**Channels:**
- `user_actions`: Browse, search, save events
- `recommendations`: Generated suggestions
- `bookings`: Reservation activities
- `social`: Friend requests, invitations
- `system`: System events
- `metrics`: Performance indicators
- `simulation`: Control events

### 5. Admin Dashboard

- Real-time event feed with color-coded events
- Activity metrics charts (Recharts)
- Simulation controls (start, pause, speed, scenario)
- System statistics overview
- Data seeding capability
- **Agent Visualization Views:**
  - **Recommendation Agent View**: Deep insights into recommendation reasoning, user context, compatibility scores, and LLM-generated explanations
  - **Booking Agent View**: Live booking pipeline visualization, group formation dynamics, invitation flows, and decision logs
- GNN training interface and model status monitoring

### 6. User View (Planned)

**Customer-facing application design** - See [`docs/implementation_plan.md`](docs/implementation_plan.md) Section 5.6 for complete details:

- **Personalized "For You" Feed**: AI-powered recommendations with explanations
- **Smart Venue Discovery**: Interactive map view, real-time availability, intelligent filtering
- **Social Dining Features**: Group coordination, compatibility matching, partner discovery
- **One-Tap Booking**: Intelligent defaults, availability grid, smart suggestions
- **Activity Tracking**: Dining stats dashboard, personal insights, achievements/badges
- **Real-Time Notifications**: Personalized recommendations, social invites, booking updates
- **Mobile-First PWA**: Progressive Web App with offline support, gesture controls, voice interface

See [`docs/implementation_plan.md`](docs/implementation_plan.md) for comprehensive User View implementation guide.

## Technology Stack

### Backend
- **FastAPI**: High-performance async API framework
- **SQLAlchemy 2.0**: Async ORM with SQLite/PostgreSQL
- **Redis Streams**: Event streaming (with in-memory fallback)
- **Pydantic**: Data validation and serialization
- **PyTorch**: Deep learning framework for GNN models
- **PyTorch Geometric**: Graph neural network library (LightGCN)
- **LangGraph-ready**: Agent architecture for LLM integration

### Frontend
- **React 18**: Modern UI library
- **TypeScript**: Type-safe development
- **Tailwind CSS**: Utility-first styling
- **Recharts**: Data visualization
- **Lucide React**: Icon library
- **Vite**: Fast build tool

## API Endpoints

### Recommendations
```
GET  /api/v1/recommendations/{user_id}         - Get personalized recommendations
GET  /api/v1/recommendations/{user_id}/venues  - Get venue recommendations
GET  /api/v1/recommendations/{user_id}/people  - Get compatible people
POST /api/v1/recommendations/{user_id}/interest - Express venue interest
GET  /api/v1/recommendations/group/{user_ids}   - Group venue optimization
```

### Bookings
```
GET  /api/v1/bookings/                      - List all bookings
GET  /api/v1/bookings/{booking_id}          - Get booking by ID
POST /api/v1/bookings/{user_id}/create      - Create booking via agent
GET  /api/v1/bookings/user/{user_id}        - Get user's bookings
POST /api/v1/bookings/{booking_id}/cancel   - Cancel booking
POST /api/v1/bookings/venue/{venue_id}/auto-book - Auto-book interested users
```

### Simulation
```
POST /api/v1/simulation/start    - Start simulation
POST /api/v1/simulation/pause    - Pause simulation
POST /api/v1/simulation/resume   - Resume simulation
POST /api/v1/simulation/stop     - Stop simulation
POST /api/v1/simulation/reset    - Reset simulation
POST /api/v1/simulation/speed    - Set speed multiplier
POST /api/v1/simulation/scenario - Trigger scenario
GET  /api/v1/simulation/state    - Get current state
GET  /api/v1/simulation/metrics  - Get metrics
```

### Admin/Streaming
```
GET  /api/v1/admin/stats                       - Dashboard statistics
GET  /api/v1/admin/streams/subscribe/{channel} - SSE subscription
GET  /api/v1/admin/streams/subscribe-all       - Subscribe to all channels
GET  /api/v1/admin/streams/history/{channel}   - Get event history
POST /api/v1/admin/data/seed                   - Seed demo data
POST /api/v1/admin/data/reset                  - Reset database
```

### GNN Training
```
POST /api/v1/admin/gnn/train                   - Train LightGCN model
GET  /api/v1/admin/gnn/status                  - Get GNN model status
```

**Note**: GNN scores are automatically included in recommendation endpoints when a trained model is available. See [`docs/GNN_IMPLEMENTATION.md`](docs/GNN_IMPLEMENTATION.md) for training guide.

## Setup Instructions

### Prerequisites
- Python 3.10+
- Node.js 18+
- Redis (optional, uses in-memory fallback)
- PyTorch (for GNN training - optional but recommended)

### Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run the server
uvicorn app.main:app --reload --port 8000
```

### Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Run development server
npm run dev
```

### Quick Start Demo

1. Start the backend server
2. Start the frontend dev server
3. Open http://localhost:3000
4. Click "Seed Demo Data" to populate the database
5. (Optional) Train GNN model: `POST /api/v1/admin/gnn/train` with default parameters
6. Click "Start" to begin simulation
7. Adjust speed and scenarios to see different behaviors
8. Explore Agent Views to see recommendation and booking logic in action

**Note**: The system works with rule-based recommendations alone. GNN training enhances recommendations with learned social patterns but is optional.

## Data Models

### User
- Profile information (username, email, avatar)
- Location (latitude, longitude, city)
- Persona type (for simulation)
- Activity and social scores

### UserPreferences
- Cuisine preferences (array)
- Price range (min/max)
- Ambiance preferences
- Dietary restrictions
- Social preferences (group size, openness)

### Venue
- Location and address
- Category and cuisine type
- Price level and rating
- Capacity and availability
- Features and ambiance tags
- Operating hours

### Booking
- User and venue references
- Party size and time
- Status (pending, confirmed, cancelled, completed)
- Group members (for social bookings)
- Agent tracking (which agent created it)

### Social Graph
- Friendships with compatibility scores
- Venue interests with time preferences
- User interactions for learning

## Design Decisions

### Why Async Python?
- High concurrency for real-time streaming
- Efficient database operations
- FastAPI's native async support

### Why In-Memory Streaming?
- Zero-dependency demo capability
- Easy deployment for evaluation
- Redis-ready for production scaling

### Why Persona-Based Simulation?
- Realistic behavior patterns
- Demonstrates recommendation adaptation
- Compelling demo scenarios

### Agent Architecture
- Modular, testable components
- LangGraph-compatible for LLM integration
- Clear separation of concerns

### Why Graph Neural Networks?
- Learns from user-venue interactions and social connections
- Captures implicit preferences and social influence
- Improves recommendations over time with more data
- Hybrid approach balances explainability (rule-based) with learning (GNN)
- Production-ready with graceful fallbacks when model unavailable

## Coding Agent Usage

This project was developed with assistance from Claude (Anthropic's AI assistant) for:
- Architecture design and planning
- Code generation and implementation
- Documentation and README creation

All code was reviewed and structured following best practices for:
- Type safety (TypeScript, Python type hints)
- Async patterns
- Clean architecture
- Security considerations

## Documentation

- **[GNN Implementation Guide](docs/GNN_IMPLEMENTATION.md)**: Complete guide to LightGCN implementation, training, and integration
- **[Implementation Plan](docs/implementation_plan.md)**: Comprehensive system design including simulation, agent views, and user view
- **[API Documentation](backend/API_DOCUMENTATION.md)**: Detailed API endpoint documentation
- **[Quick Start Guide](backend/QUICKSTART.md)**: Step-by-step setup and usage guide

## Future Enhancements

1. **LLM Integration**: Add OpenAI/Claude for natural language recommendations and explanations
2. **Vector Database**: Semantic search for venues and preferences
3. **GNN Improvements**: 
   - Incremental training for new interactions
   - Cached graph to avoid rebuilding
   - Multi-GPU training for larger datasets
   - Hyperparameter auto-tuning
4. **Real Redis**: Production-ready streaming infrastructure
5. **Authentication**: JWT-based user authentication
6. **iOS Integration**: API endpoints ready for SwiftUI frontend
7. **User View Implementation**: Complete customer-facing Next.js application (see implementation plan)

## Project Structure

```
luna_assignment/
├── backend/
│   ├── app/
│   │   ├── api/
│   │   │   └── routes/          # API endpoints
│   │   ├── agents/              # AI agents
│   │   ├── core/                # Config and database
│   │   ├── ml_models/           # GNN model architecture (LightGCN)
│   │   ├── models/              # SQLAlchemy models
│   │   ├── services/            # Business logic (includes GNN trainer)
│   │   └── main.py              # Application entry
│   ├── models/                  # Saved GNN model files (.pt, metadata)
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── App.tsx              # Main dashboard
│   │   └── main.tsx             # Entry point
│   ├── package.json
│   └── vite.config.ts
├── docs/
│   ├── GNN_IMPLEMENTATION.md    # Complete GNN guide
│   ├── implementation_plan.md   # System design with User View
│   └── DELIVERABLE_ASSESSMENT.md # Assessment documentation
├── backend/
│   ├── API_DOCUMENTATION.md     # API endpoint docs
│   └── QUICKSTART.md            # Quick start guide
└── README.md
```

## License

This project was created for the Luna Social Take Home Technical Assignment.

---

**Author**: Developed as part of Luna Social Backend Track evaluation
**Date**: November 2025
