# Luna Social Recommendation Architecture

> A comprehensive guide to the AI-powered recommendation system for venue discovery and social matching.

## Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [Core Components](#core-components)
3. [Recommendation Pipeline](#recommendation-pipeline)
4. [Machine Learning (GNN)](#machine-learning-gnn)
5. [Scoring Algorithms](#scoring-algorithms)
6. [Preference Evolution](#preference-evolution)
7. [Temporal Context](#temporal-context)
8. [LLM Integration](#llm-integration)
9. [API Endpoints](#api-endpoints)
10. [Data Flow Diagram](#data-flow-diagram)

---

## Architecture Overview

Luna Social's recommendation system is a **hybrid AI architecture** that combines:

- **Rule-based scoring** for interpretable, preference-aligned recommendations
- **Graph Neural Networks (LightGCN)** for collaborative filtering via learned embeddings
- **LLM-powered explanations** for personalized, human-readable reasoning
- **Dynamic preference evolution** that learns from user behavior over time
- **Temporal context awareness** for time-appropriate suggestions

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         RECOMMENDATION ARCHITECTURE                          │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│   ┌──────────────┐     ┌──────────────────┐     ┌──────────────────┐       │
│   │   API Layer  │────▶│ Recommendation   │────▶│  Response with   │       │
│   │   (FastAPI)  │     │     Agent        │     │   Explanations   │       │
│   └──────────────┘     └────────┬─────────┘     └──────────────────┘       │
│                                 │                                           │
│                    ┌────────────┼────────────┐                              │
│                    ▼            ▼            ▼                              │
│           ┌────────────┐ ┌────────────┐ ┌────────────┐                      │
│           │  Temporal  │ │ Preference │ │    LLM     │                      │
│           │  Context   │ │ Evolution  │ │  Client    │                      │
│           └────────────┘ └────────────┘ └────────────┘                      │
│                                 │                                           │
│                                 ▼                                           │
│                    ┌────────────────────────┐                               │
│                    │  Recommendation Engine │                               │
│                    │   ┌──────────────────┐ │                               │
│                    │   │  Rule-Based      │ │   70% weight                  │
│                    │   │  Scoring         │ │                               │
│                    │   └──────────────────┘ │                               │
│                    │   ┌──────────────────┐ │                               │
│                    │   │  GNN (LightGCN)  │ │   30% weight                  │
│                    │   │  Scoring         │ │                               │
│                    │   └──────────────────┘ │                               │
│                    └────────────────────────┘                               │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Core Components

### 1. RecommendationAgent (`agents/recommendation_agent.py`)

The orchestration layer that coordinates the entire recommendation workflow.

**Key Responsibilities:**
- Context analysis (time, location, user history)
- Workflow orchestration across multiple services
- Event publishing for real-time updates
- Interaction tracking for learning

**State Machine:**
```
initiated → context_analyzed → venues_recommended → people_recommended → completed
```

**Core Methods:**
| Method | Description |
|--------|-------------|
| `get_recommendations()` | Main entry point for personalized recommendations |
| `express_interest()` | Record user interest in a venue |
| `track_interaction()` | Log user interactions for learning |

---

### 2. RecommendationEngine (`services/recommendation.py`)

The computational core that generates venue and social recommendations.

**Features:**
- Spatial analysis using Haversine distance calculation
- Multi-factor venue scoring
- Social compatibility matching
- Group venue optimization

**Key Methods:**

| Method | Description |
|--------|-------------|
| `get_venue_recommendations()` | Personalized venue suggestions with hybrid scoring |
| `get_compatible_users()` | Find dining companions based on compatibility |
| `find_optimal_venue_for_group()` | Best venue for a group considering all preferences |
| `get_users_interested_in_venue()` | Users who expressed interest in a specific venue |

---

### 3. LightGCN Model (`ml_models/lightgcn.py`)

State-of-the-art Graph Convolutional Network for collaborative filtering.

**Architecture:**
```
┌────────────────────────────────────────────────────────────────┐
│                        LightGCN Model                          │
├────────────────────────────────────────────────────────────────┤
│                                                                │
│   Users [0, num_users)          Venues [num_users, total)      │
│         │                              │                       │
│         ▼                              ▼                       │
│   ┌───────────────┐            ┌───────────────┐              │
│   │   Embedding   │◄──────────▶│   Embedding   │              │
│   │   (64 dim)    │    GCN     │   (64 dim)    │              │
│   └───────────────┘   Layers   └───────────────┘              │
│         │                              │                       │
│         └──────────┬───────────────────┘                       │
│                    ▼                                           │
│           ┌───────────────┐                                    │
│           │ Neighborhood  │  × 3 layers                        │
│           │ Aggregation   │                                    │
│           └───────────────┘                                    │
│                    │                                           │
│                    ▼                                           │
│           ┌───────────────┐                                    │
│           │ Final Embed = │                                    │
│           │ mean(layers)  │                                    │
│           └───────────────┘                                    │
│                    │                                           │
│                    ▼                                           │
│           ┌───────────────┐                                    │
│           │  Dot Product  │ → Affinity Score                   │
│           └───────────────┘                                    │
│                                                                │
└────────────────────────────────────────────────────────────────┘
```

**Hyperparameters:**
| Parameter | Default | Description |
|-----------|---------|-------------|
| `embedding_dim` | 64 | Embedding vector dimension |
| `num_layers` | 3 | GCN propagation layers |
| `dropout` | 0.0 | Dropout rate |
| `learning_rate` | 0.001 | Adam optimizer LR |
| `batch_size` | 2048 | Training batch size |
| `epochs` | 100 | Training epochs |

**Loss Function:** BPR (Bayesian Personalized Ranking)
```
L = -log(σ(score_positive - score_negative))
```

---

### 4. GNNTrainer (`services/gnn_trainer.py`)

Manages the full training lifecycle for the LightGCN model.

**Training Pipeline:**
1. Build graph from database via `GraphDataBuilder`
2. Initialize LightGCN model
3. Prepare positive/negative training pairs
4. Train with BPR loss
5. Save model and metadata

**Persistence:**
- Model weights: `models/lightgcn.pt`
- Metadata (ID mappings): `models/gnn_metadata.json`

---

### 5. GraphDataBuilder (`services/graph_data.py`)

Transforms relational database into graph tensors.

**Graph Structure:**
```
Node Types:
├── Users:  indices [0, num_users)
└── Venues: indices [num_users, num_users + num_venues)

Edge Types:
├── User-Venue: Interactions (views, saves, bookings, interests)
└── User-User:  Friendships (bidirectional)
```

**Interaction Weights:**
| Interaction Type | Weight |
|------------------|--------|
| View | 1.0 + duration bonus (up to +2.0) |
| Share | 2.0 |
| Like | 2.5 |
| Save | 3.0 |
| Review | 4.0 |
| Explicit Interest | 5.0 |
| Booking | 10.0 |

---

## Recommendation Pipeline

### Venue Recommendation Flow

```
1. User Request
      │
      ▼
2. Context Analysis
   ├── Time of day (meal period)
   ├── Day of week (weekend/weekday)
   ├── User location
   └── User preferences
      │
      ▼
3. Venue Scoring (per venue)
   │
   ├── Rule-Based Score (70% weight)
   │   ├── Distance score (30%)
   │   ├── Price compatibility (15%)
   │   ├── Rating score (20%)
   │   ├── Popularity score (10%)
   │   ├── Cuisine match (15%)
   │   └── Trending bonus (10%)
   │
   └── GNN Score (30% weight)
       └── LightGCN dot product affinity
      │
      ▼
4. Final Score = 0.7 × rule_score + 0.3 × gnn_score
      │
      ▼
5. Sort by score, return top N
      │
      ▼
6. Generate LLM explanations
```

### Social Compatibility Flow

```
1. Find Candidate Users
   ├── Exclude self
   ├── Exclude existing friends (for new connections)
   └── Filter by openness to new people
      │
      ▼
2. Batch Data Fetching (optimization)
   ├── Preferences for all candidates
   ├── Mutual friend counts
   └── Shared venue interests
      │
      ▼
3. Compatibility Scoring (per user)
   ├── Friend connection (25%)
   ├── Preference similarity (25%)
   ├── Shared venue interest (20% if venue specified)
   ├── Activity level match (15%)
   └── Social openness (15%)
      │
      ▼
4. Filter by COMPATIBILITY_THRESHOLD
      │
      ▼
5. Return top matches with reasons
```

---

## Scoring Algorithms

### Venue Scoring Formula

```python
score = Σ(weight_i × score_i) / Σ(weight_i)

Components:
├── distance_score   = 1 - (distance / max_distance)           weight: 0.30
├── price_score      = 1.0 if in range, else 0.3               weight: 0.15
├── rating_score     = rating / 5.0                            weight: 0.20
├── popularity_score = venue.popularity_score                  weight: 0.10
├── cuisine_score    = 1.0 if match, else 0.5                  weight: 0.15
└── trending_score   = 1.0 if trending, else 0.5               weight: 0.10
```

### Social Compatibility Formula

```python
compatibility = Σ(weight_i × score_i) / Σ(weight_i)

Components:
├── friend_connection = 1.0 if friend, min(mutuals/5, 1.0) if mutuals, else 0.3
├── preference_similarity = jaccard(cuisines) + price_overlap + jaccard(ambiance)
├── venue_interest   = 1.0 if shared, else 0.3 (only if venue specified)
├── activity_match   = 1 - |activity_diff|
└── social_openness  = 1.0 if open, else 0.5
```

### Preference Similarity (Jaccard-based)

```python
def preference_similarity(user1_prefs, user2_prefs):
    similarities = []
    
    # Cuisine overlap
    cuisine_sim = |user1_cuisines ∩ user2_cuisines| / |user1_cuisines ∪ user2_cuisines|
    
    # Price range overlap
    price_sim = (min(max1, max2) - max(min1, min2)) / (max(max1, max2) - min(min1, min2))
    
    # Ambiance overlap
    ambiance_sim = |user1_ambiance ∩ user2_ambiance| / |user1_ambiance ∪ user2_ambiance|
    
    return mean(similarities)
```

---

## Preference Evolution

The system dynamically updates user preferences based on behavior.

### Learning Rates

| Action | Rate | Effect |
|--------|------|--------|
| Browse | 0.02 (2%) | Slight preference shift |
| Express Interest | 0.05 (5%) | Moderate shift |
| Make Booking | 0.10 (10%) | Strong positive shift |
| Cancel Booking | -0.03 (-3%) | Negative feedback |

### Social Influence

When users dine together, preferences slowly converge:
- Influence rate: 2% per interaction
- Maximum total influence: 15%

### Seasonal Drift

Preferences shift based on season:

| Season | Boosted Cuisines | Decreased Cuisines |
|--------|-----------------|-------------------|
| Summer | salad, seafood, mediterranean, asian | steakhouse, comfort |
| Winter | italian, american, steakhouse, comfort | salad, seafood |
| Spring | asian, mediterranean, brunch | comfort |
| Fall | american, steakhouse, comfort | salad |

---

## Temporal Context

The `TemporalEventGenerator` applies time-based modifiers to action probabilities.

### Meal Periods

| Period | Hours | Action Modifiers |
|--------|-------|------------------|
| Breakfast | 6-11 | browse ↑1.1×, invites ↓0.7× |
| Lunch | 11-15 | browse ↑1.5×, booking ↑1.5× |
| Afternoon | 15-18 | browse ↑1.2×, interests ↑1.1× |
| Dinner | 18-22 | all activities ↑1.2-1.4× |
| Late Night | 22-24 | social ↑1.3×, booking ↓0.6× |
| Early Morning | 0-6 | all activities ↓0.3-0.5× |

### Weekend Modifiers

- Social invites: ↑1.3×
- Friend checking: ↑1.2×
- Bookings: ↑1.15×
- Saturday brunch: browse ↑1.4×, booking ↑1.5×

### Holiday Modifiers

Major holidays (Valentine's Day, NYE, etc.) significantly boost:
- Social invites: ↑1.3-1.6×
- Bookings: ↑1.4-1.5×

---

## LLM Integration

Uses OpenRouter API for personalized explanations.

### Recommendation Explanations

```python
# System prompt
"You are a friendly dining assistant for Luna Social..."

# Generated explanation example
"'Sakura' serves Japanese cuisine - one of your favorites! 
Perfect for dinner with its cozy rooftop ambiance."
```

### Social Match Reasons

```python
# Generated reason example
"You both love Italian food and share 2 mutual friends - 
perfect for a weekend brunch!"
```

### Fallback Mechanism

If LLM unavailable, falls back to template-based explanations:
```python
f"'{venue_name}' serves {cuisine} cuisine - one of your favorites! 
Perfect for {meal_time}."
```

---

## API Endpoints

### Recommendation Routes (`/api/v1/recommendations`)

| Endpoint | Method | Description |
|----------|--------|-------------|
| `GET /` | Query | Get full recommendations (venues + people) |
| `GET /user/{user_id}` | Path | Get recommendations for specific user |
| `GET /{user_id}/venues` | Path | Get venue recommendations only |
| `GET /compatible` | Query | Get compatible people |
| `GET /user/{user_id}/people` | Path | Get people recommendations |
| `POST /interest` | Body | Express interest in a venue |
| `GET /group` | Query | Get optimal venue for group |

### Request/Response Examples

**Get Recommendations:**
```http
GET /api/v1/recommendations?user_id=1&include_people=true

Response:
{
  "user_id": 1,
  "venues": [
    {
      "id": 42,
      "name": "Sakura",
      "score": 0.85,
      "rule_score": 0.87,
      "gnn_score": 0.81,
      "distance_km": 1.2,
      "cuisine_type": "Japanese",
      ...
    }
  ],
  "people": [
    {
      "id": 7,
      "username": "foodie_jane",
      "compatibility_score": 0.78,
      "reasons": ["Similar taste", "2 mutual friends"],
      ...
    }
  ],
  "context": {
    "meal_time": "dinner",
    "is_weekend": true
  },
  "explanations": [
    "'Sakura' is trending right now!",
    "foodie_jane: You both enjoy Mediterranean cuisine!"
  ]
}
```

**Express Interest:**
```http
POST /api/v1/recommendations/interest
{
  "user_id": 1,
  "venue_id": 42,
  "preferred_time_slot": "dinner",
  "open_to_invites": true
}

Response:
{
  "success": true,
  "venue_id": 42,
  "others_interested": [...],
  "message": "Interest recorded! 5 others are also interested."
}
```

---

## Data Flow Diagram

```
┌──────────────────────────────────────────────────────────────────────────────┐
│                              DATA FLOW                                        │
└──────────────────────────────────────────────────────────────────────────────┘

                    ┌─────────────────────┐
                    │   User Interaction  │
                    │   (API Request)     │
                    └──────────┬──────────┘
                               │
                               ▼
┌──────────────────────────────────────────────────────────────────────────────┐
│                         RecommendationAgent                                   │
│  ┌────────────┐  ┌─────────────────┐  ┌─────────────────┐                    │
│  │  Analyze   │→ │ Get Venues      │→ │ Get People      │                    │
│  │  Context   │  │ Recommendations │  │ Recommendations │                    │
│  └────────────┘  └─────────────────┘  └─────────────────┘                    │
└────────┬─────────────────┬─────────────────────┬─────────────────────────────┘
         │                 │                     │
         ▼                 ▼                     ▼
┌────────────────┐ ┌───────────────┐     ┌───────────────┐
│ TemporalEvent  │ │ Recommendation│     │    LLM        │
│ Generator      │ │ Engine        │     │   Client      │
│                │ │               │     │               │
│ • Meal period  │ │ • Venue score │     │ • Explanation │
│ • Weekend      │ │ • Social match│     │ • Match reason│
│ • Holiday      │ │ • GNN score   │     │               │
│ • Season       │ │               │     │               │
└────────────────┘ └───────┬───────┘     └───────────────┘
                           │
         ┌─────────────────┼─────────────────┐
         │                 │                 │
         ▼                 ▼                 ▼
┌────────────────┐ ┌───────────────┐ ┌───────────────┐
│   Database     │ │  GNNTrainer   │ │ Preference    │
│                │ │               │ │ Evolution     │
│ • Users        │ │ • LightGCN    │ │               │
│ • Venues       │ │ • Embeddings  │ │ • Action-based│
│ • Interactions │ │ • Predictions │ │ • Social      │
│ • Friendships  │ │               │ │ • Seasonal    │
│ • Interests    │ │               │ │               │
└────────────────┘ └───────┬───────┘ └───────────────┘
                           │
                           ▼
                   ┌───────────────┐
                   │ GraphData     │
                   │ Builder       │
                   │               │
                   │ • ID mappings │
                   │ • Edge index  │
                   │ • Weights     │
                   └───────────────┘
```

---

## Configuration

Key settings in `core/config.py`:

| Setting | Default | Description |
|---------|---------|-------------|
| `MAX_DISTANCE_KM` | 10.0 | Default max venue distance |
| `COMPATIBILITY_THRESHOLD` | 0.5 | Min score to show as compatible |
| `OPENROUTER_MODEL` | configurable | LLM model for explanations |
| `LLM_TIMEOUT_SECONDS` | 30 | LLM request timeout |
| `LLM_MAX_TOKENS` | 150 | Max tokens for explanations |
| `LLM_TEMPERATURE` | 0.7 | LLM creativity setting |

---

## Performance Optimizations

1. **Batch Data Fetching**: Preferences, mutual friends, and interests are fetched in bulk to avoid N+1 queries

2. **Early Filtering**: Candidate users are filtered before scoring to limit computation

3. **Spatial Pre-filtering**: Group venue search uses bounding box before distance calculation

4. **Event Throttling**: Recommendation events are throttled (60s) to prevent duplicates

5. **GNN Caching**: Model weights and embeddings are cached after training

---

## Future Enhancements

- [ ] Real-time embedding updates without full retraining
- [ ] Contextual bandits for exploration/exploitation balance
- [ ] Multi-modal venue features (images, reviews)
- [ ] Cross-session preference tracking
- [ ] A/B testing framework for scoring weights

