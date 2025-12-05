# Luna Social Voice Agent - Implementation Specification

> **Version**: 1.0.0  
> **Created**: December 2024  
> **Status**: Draft  

---

## Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [System Overview](#2-system-overview)
3. [Architecture Design](#3-architecture-design)
4. [Technology Stack](#4-technology-stack)
5. [Agent System Design](#5-agent-system-design)
6. [Voice Gateway Service](#6-voice-gateway-service)
7. [Intent Recognition System](#7-intent-recognition-system)
8. [Action Agent Design](#8-action-agent-design)
9. [API Specifications](#9-api-specifications)
10. [Frontend Integration](#10-frontend-integration)
11. [Hathora Deployment](#11-hathora-deployment)
12. [Data Flow & Sequences](#12-data-flow--sequences)
13. [Error Handling](#13-error-handling)
14. [Testing Strategy](#14-testing-strategy)
15. [Implementation Phases](#15-implementation-phases)
16. [Open Questions & Decisions](#16-open-questions--decisions)

---

## 1. Executive Summary

### 1.1 Purpose

This document specifies the implementation of a voice-enabled conversational interface for the Luna Social platform. Users will be able to interact with the platform through natural speech to:

- Get venue recommendations
- Make, modify, and cancel bookings
- Find friends at venues
- Send and respond to invites
- Get directions and check availability

### 1.2 Key Design Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Speech Model | Qwen-Omni3 | Native speech-to-speech, low latency, multimodal |
| Architecture | Two-Agent System | Separation of concerns: Voice Agent + Action Agent |
| Infrastructure | Hathora | Multi-region deployment, auto-scaling, low-latency networking |
| Interaction Mode | Full Duplex (Click-to-Activate) | Natural conversation flow with explicit user control |
| State Management | Stateless with Multi-turn | Session-based context without persistent conversation history |
| Framework | LangGraph | Consistent with existing agent architecture |

### 1.3 Scope

**In Scope:**
- Voice-to-voice conversation via Qwen-Omni3
- Intent recognition and action routing
- Integration with existing booking, recommendation, and social APIs
- User-app (Next.js) integration
- Hathora deployment configuration

**Out of Scope (v1.0):**
- Authentication/authorization for voice
- Multi-language support
- Voice biometrics
- Persistent conversation history
- Proactive notifications

---

## 2. System Overview

### 2.1 High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              USER DEVICE                                     │
│  ┌─────────────────────────────────────────────────────────────────────────┐│
│  │                         /user-app (Next.js)                              ││
│  │  ┌────────────────┐   ┌──────────────────┐   ┌───────────────────────┐  ││
│  │  │ Voice Button   │──▶│  Audio Capture   │──▶│   WebSocket Client    │  ││
│  │  │ (Click-to-Talk)│   │  (MediaRecorder) │   │   (Real-time Audio)   │  ││
│  │  └────────────────┘   └──────────────────┘   └───────────┬───────────┘  ││
│  │                                                           │              ││
│  │  ┌────────────────┐   ┌──────────────────┐               │              ││
│  │  │ Audio Playback │◀──│  Audio Decoder   │◀──────────────┘              ││
│  │  │ (Web Audio API)│   │  (Streaming)     │                              ││
│  │  └────────────────┘   └──────────────────┘                              ││
│  └─────────────────────────────────────────────────────────────────────────┘│
└──────────────────────────────────────┬──────────────────────────────────────┘
                                       │
                          WebSocket (Bidirectional Audio Stream)
                                       │
┌──────────────────────────────────────▼──────────────────────────────────────┐
│                         HATHORA INFRASTRUCTURE                               │
│  ┌─────────────────────────────────────────────────────────────────────────┐│
│  │                     VOICE GATEWAY SERVICE                                ││
│  │  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────────────┐  ││
│  │  │ Connection Mgr  │  │ Session Manager │  │ Audio Stream Handler    │  ││
│  │  │ (WebSocket)     │  │ (Multi-turn)    │  │ (Bidirectional)         │  ││
│  │  └────────┬────────┘  └────────┬────────┘  └────────────┬────────────┘  ││
│  │           │                    │                        │               ││
│  │           └────────────────────┼────────────────────────┘               ││
│  │                                │                                         ││
│  │  ┌─────────────────────────────▼─────────────────────────────────────┐  ││
│  │  │                     VOICE AGENT (Qwen-Omni3)                       │  ││
│  │  │  ┌───────────────┐  ┌────────────────┐  ┌──────────────────────┐  │  ││
│  │  │  │ Audio Input   │─▶│ Speech-to-     │─▶│ Response Generation  │  │  ││
│  │  │  │ Processing    │  │ Understanding  │  │ (Speech Output)      │  │  ││
│  │  │  └───────────────┘  └───────┬────────┘  └──────────────────────┘  │  ││
│  │  │                             │                      ▲               │  ││
│  │  │                    Intent + Entities               │               │  ││
│  │  │                             │              Action Result           │  ││
│  │  │                             ▼                      │               │  ││
│  │  │  ┌──────────────────────────────────────────────────────────────┐ │  ││
│  │  │  │              INTENT ROUTER (LangGraph)                        │ │  ││
│  │  │  │  ┌────────────┐  ┌────────────┐  ┌────────────────────────┐  │ │  ││
│  │  │  │  │ Classifier │─▶│ Slot Filler│─▶│ Action Dispatcher      │  │ │  ││
│  │  │  │  └────────────┘  └────────────┘  └────────────────────────┘  │ │  ││
│  │  │  └──────────────────────────────────────────────────────────────┘ │  ││
│  │  └───────────────────────────────────────────────────────────────────┘  ││
│  └─────────────────────────────────────────────────────────────────────────┘│
│                                       │                                      │
│                              Internal API Call                               │
│                                       │                                      │
│  ┌────────────────────────────────────▼────────────────────────────────────┐│
│  │                        ACTION AGENT (LangGraph)                          ││
│  │  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────────────┐  ││
│  │  │ Tool Selector   │  │ Parameter       │  │ Execution Engine        │  ││
│  │  │                 │  │ Validator       │  │                         │  ││
│  │  └────────┬────────┘  └────────┬────────┘  └────────────┬────────────┘  ││
│  │           │                    │                        │               ││
│  │           └────────────────────┼────────────────────────┘               ││
│  │                                │                                         ││
│  │  ┌─────────────────────────────▼─────────────────────────────────────┐  ││
│  │  │                         TOOL REGISTRY                              │  ││
│  │  │  ┌───────────┐ ┌───────────┐ ┌───────────┐ ┌───────────┐          │  ││
│  │  │  │ Booking   │ │ Recommend │ │ Social    │ │ Venue     │          │  ││
│  │  │  │ Tools     │ │ Tools     │ │ Tools     │ │ Tools     │          │  ││
│  │  │  └───────────┘ └───────────┘ └───────────┘ └───────────┘          │  ││
│  │  └───────────────────────────────────────────────────────────────────┘  ││
│  └─────────────────────────────────────────────────────────────────────────┘│
└──────────────────────────────────────┬──────────────────────────────────────┘
                                       │
                              HTTP/Internal Call
                                       │
┌──────────────────────────────────────▼──────────────────────────────────────┐
│                          LUNA SOCIAL BACKEND                                 │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────────────────┐  │
│  │ BookingAgent    │  │ Recommendation  │  │ Database (SQLite/Postgres)  │  │
│  │ (Existing)      │  │ Agent (Existing)│  │                             │  │
│  └─────────────────┘  └─────────────────┘  └─────────────────────────────┘  │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────────────────┐  │
│  │ Streaming       │  │ LLM Client      │  │ Venue/User Models           │  │
│  │ Service         │  │ (OpenRouter)    │  │                             │  │
│  └─────────────────┘  └─────────────────┘  └─────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 2.2 Component Summary

| Component | Responsibility | Technology |
|-----------|---------------|------------|
| Voice Button | Trigger voice interaction | React + Web Audio API |
| Audio Capture | Capture microphone input | MediaRecorder API |
| WebSocket Client | Real-time audio streaming | Native WebSocket |
| Voice Gateway | Connection & session management | FastAPI + WebSocket |
| Voice Agent | Speech understanding & generation | Qwen-Omni3 |
| Intent Router | Classify intent & extract entities | LangGraph |
| Action Agent | Execute platform actions | LangGraph + Tools |
| Tool Registry | Available action definitions | Python Functions |
| Luna Backend | Business logic & data | Existing FastAPI |

---

## 3. Architecture Design

### 3.1 Two-Agent Architecture

The system employs a deliberate separation between the **Voice Agent** and the **Action Agent**:

```
┌─────────────────────────────────────────────────────────────────────┐
│                           VOICE AGENT                                │
│                                                                      │
│  Responsibilities:                                                   │
│  ✓ Receive and process audio input                                  │
│  ✓ Understand user intent from speech                               │
│  ✓ Generate natural spoken responses                                │
│  ✓ Handle conversational flow (greetings, clarifications)          │
│  ✓ Delegate actions to Action Agent                                 │
│  ✓ Synthesize action results into speech                           │
│                                                                      │
│  Does NOT:                                                           │
│  ✗ Execute database operations                                      │
│  ✗ Make API calls directly                                          │
│  ✗ Handle business logic                                            │
└──────────────────────────────┬──────────────────────────────────────┘
                               │
                  Structured Intent + Entities
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────────┐
│                          ACTION AGENT                                │
│                                                                      │
│  Responsibilities:                                                   │
│  ✓ Validate action parameters                                       │
│  ✓ Select and invoke appropriate tools                              │
│  ✓ Execute booking, recommendation, social operations              │
│  ✓ Handle multi-step action workflows                               │
│  ✓ Return structured results                                        │
│                                                                      │
│  Does NOT:                                                           │
│  ✗ Process audio                                                    │
│  ✗ Generate speech                                                  │
│  ✗ Handle conversational nuances                                    │
└─────────────────────────────────────────────────────────────────────┘
```

### 3.2 Rationale for Two-Agent Design

1. **Separation of Concerns**: Voice handling is complex; action execution is domain-specific
2. **Testability**: Action Agent can be tested independently with text inputs
3. **Flexibility**: Can swap voice models without touching action logic
4. **Latency**: Action Agent can be optimized for speed without audio overhead
5. **Security**: Action Agent can have different permission boundaries
6. **Reusability**: Action Agent could serve chat-based interfaces too

### 3.3 Communication Protocol

```
Voice Agent → Action Agent:
{
    "session_id": "uuid",
    "intent": "make_booking",
    "entities": {
        "venue_name": "Olive Garden",
        "party_size": 4,
        "time": "7pm tonight"
    },
    "confidence": 0.92,
    "user_id": 123,
    "context": {
        "turn_count": 2,
        "previous_intents": ["get_recommendations"]
    }
}

Action Agent → Voice Agent:
{
    "session_id": "uuid",
    "status": "success",
    "action": "make_booking",
    "result": {
        "booking_id": 456,
        "confirmation_code": "ABC123",
        "venue_name": "Olive Garden",
        "time": "2024-12-05T19:00:00",
        "party_size": 4
    },
    "speak_text": "I've booked a table for 4 at Olive Garden for 7 PM tonight. Your confirmation code is ABC123.",
    "follow_up_prompt": "Would you like me to invite any friends?"
}
```

---

## 4. Technology Stack

### 4.1 Core Technologies

| Layer | Technology | Version | Purpose |
|-------|------------|---------|---------|
| Speech Model | Qwen-Omni3 | Latest | Speech-to-speech understanding & generation |
| Backend Framework | FastAPI | 0.100+ | Voice Gateway & Action Agent APIs |
| Agent Framework | LangGraph | 0.0.40+ | Agent orchestration & state management |
| WebSocket | FastAPI WebSocket | Built-in | Real-time audio streaming |
| Audio Processing | PyAudio / soundfile | Latest | Audio format handling |
| Infrastructure | Hathora | Latest | Deployment, scaling, networking |

### 4.2 Frontend Technologies

| Technology | Purpose |
|------------|---------|
| Next.js 14 | User app framework (existing) |
| Web Audio API | Audio capture & playback |
| MediaRecorder API | Audio recording |
| WebSocket API | Real-time communication |
| React Context | Voice session state management |

### 4.3 Audio Specifications

| Parameter | Value | Notes |
|-----------|-------|-------|
| Sample Rate | 16000 Hz | Standard for speech recognition |
| Channels | Mono | Single channel for voice |
| Bit Depth | 16-bit | PCM format |
| Codec (Streaming) | Opus | Low-latency, good compression |
| Codec (Fallback) | WAV | Uncompressed, reliable |
| Chunk Size | 20-40ms | Balance between latency & efficiency |

### 4.4 Qwen-Omni3 Integration

Qwen-Omni3 is Alibaba's multimodal model with native speech-to-speech capabilities:

```
┌─────────────────────────────────────────────────────────────────┐
│                      QWEN-OMNI3 CAPABILITIES                     │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Input Modalities:          Output Modalities:                  │
│  ├── Text                   ├── Text                            │
│  ├── Audio (Speech)         ├── Audio (Speech)                  │
│  ├── Image                  └── Structured (JSON)               │
│  └── Video                                                       │
│                                                                  │
│  Key Features:                                                   │
│  ✓ End-to-end speech understanding (no separate ASR)           │
│  ✓ Native speech synthesis (no separate TTS)                    │
│  ✓ Maintains prosody and emotion                                │
│  ✓ Low latency for real-time conversation                       │
│  ✓ Function calling support                                      │
│  ✓ Streaming output                                              │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

**Integration Options:**

1. **Qwen API (Cloud)**
   - Hosted by Alibaba Cloud
   - Pay-per-use pricing
   - Lowest integration effort

2. **Self-Hosted on Hathora**
   - Deploy Qwen-Omni3 model on Hathora infrastructure
   - Full control over latency and scaling
   - Higher complexity, better customization

3. **Hybrid**
   - Use Hathora for Voice Gateway
   - Call Qwen API for model inference
   - Balance of control and simplicity

**Recommended: Option 3 (Hybrid)** for v1.0 - minimal infrastructure complexity while leveraging Hathora's networking capabilities.

---

## 5. Agent System Design

### 5.1 Voice Agent (Qwen-Omni3)

The Voice Agent is powered by Qwen-Omni3 and handles all speech interaction:

```python
# Conceptual structure - not implementation code

class VoiceAgentConfig:
    """Configuration for the Voice Agent."""
    
    # Model settings
    model: str = "qwen-omni3"
    
    # Audio settings
    input_sample_rate: int = 16000
    output_sample_rate: int = 24000
    
    # Conversation settings
    system_prompt: str = """
    You are Luna, a friendly voice assistant for Luna Social, 
    a social dining platform. You help users:
    - Find great restaurants and venues
    - Make reservations and bookings
    - Connect with friends for dining
    - Discover who's interested in the same venues
    
    Keep responses concise and conversational. When users want 
    to take actions (book, invite, etc.), extract the relevant 
    information and delegate to the action system.
    
    Always confirm important details before taking actions.
    Be warm, helpful, and enthusiastic about food and social dining!
    """
    
    # Function calling
    available_functions: List[str] = [
        "make_booking",
        "get_recommendations", 
        "find_friends_at_venue",
        "send_invite",
        "check_venue_availability",
        "get_directions",
        "cancel_booking",
        "respond_to_invite"
    ]
```

### 5.2 Voice Agent State Machine

```
                                    ┌─────────────┐
                                    │   IDLE      │
                                    │ (Waiting)   │
                                    └──────┬──────┘
                                           │
                              User clicks voice button
                                           │
                                           ▼
                                    ┌─────────────┐
                                    │  LISTENING  │◀──────────────┐
                                    │ (Recording) │               │
                                    └──────┬──────┘               │
                                           │                      │
                            Voice activity detected               │
                                           │                      │
                                           ▼                      │
                                    ┌─────────────┐               │
                                    │ PROCESSING  │               │
                                    │ (Understanding)             │
                                    └──────┬──────┘               │
                                           │                      │
                         ┌─────────────────┼─────────────────┐    │
                         │                 │                 │    │
                    Needs Action    Conversational      Unclear   │
                         │                 │                 │    │
                         ▼                 ▼                 ▼    │
                  ┌─────────────┐   ┌─────────────┐   ┌─────────────┐
                  │  EXECUTING  │   │  RESPONDING │   │ CLARIFYING  │
                  │  (Action)   │   │  (Direct)   │   │ (Ask more)  │
                  └──────┬──────┘   └──────┬──────┘   └──────┬──────┘
                         │                 │                 │
                         │                 │                 │
                         ▼                 ▼                 │
                  ┌─────────────┐   ┌─────────────┐          │
                  │  SPEAKING   │◀──│  SPEAKING   │          │
                  │ (Result)    │   │ (Response)  │          │
                  └──────┬──────┘   └──────┬──────┘          │
                         │                 │                 │
                         └────────┬────────┘                 │
                                  │                          │
                                  ▼                          │
                           ┌─────────────┐                   │
                           │  WAITING    │───────────────────┘
                           │ (Next turn) │
                           └──────┬──────┘
                                  │
                     User stops or timeout
                                  │
                                  ▼
                           ┌─────────────┐
                           │   IDLE      │
                           └─────────────┘
```

### 5.3 Action Agent Design

The Action Agent is a LangGraph-based agent that executes platform actions:

```
┌─────────────────────────────────────────────────────────────────┐
│                    ACTION AGENT GRAPH                            │
│                                                                  │
│  ┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐  │
│  │  PARSE   │───▶│ VALIDATE │───▶│ EXECUTE  │───▶│  FORMAT  │  │
│  │  Intent  │    │  Params  │    │  Action  │    │  Result  │  │
│  └──────────┘    └────┬─────┘    └────┬─────┘    └──────────┘  │
│                       │               │                         │
│                       │ Invalid       │ Failed                  │
│                       ▼               ▼                         │
│                  ┌──────────┐    ┌──────────┐                   │
│                  │  ERROR   │    │  RETRY   │                   │
│                  │ Response │    │  /Error  │                   │
│                  └──────────┘    └──────────┘                   │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### 5.4 Tool Definitions

```python
# Tool registry for Action Agent

VOICE_ACTION_TOOLS = {
    
    "make_booking": {
        "description": "Create a reservation at a venue",
        "parameters": {
            "venue_id": {"type": "int", "required": False},
            "venue_name": {"type": "str", "required": False},
            "party_size": {"type": "int", "required": True, "default": 2},
            "date_time": {"type": "datetime", "required": True},
            "special_requests": {"type": "str", "required": False}
        },
        "requires_confirmation": True,
        "handler": "booking_agent.create_booking"
    },
    
    "get_recommendations": {
        "description": "Get personalized venue recommendations",
        "parameters": {
            "cuisine_type": {"type": "str", "required": False},
            "max_distance": {"type": "float", "required": False},
            "price_range": {"type": "str", "required": False},
            "occasion": {"type": "str", "required": False}
        },
        "requires_confirmation": False,
        "handler": "recommendation_agent.get_recommendations"
    },
    
    "find_friends_at_venue": {
        "description": "Find friends or people interested in a venue",
        "parameters": {
            "venue_id": {"type": "int", "required": False},
            "venue_name": {"type": "str", "required": False}
        },
        "requires_confirmation": False,
        "handler": "recommendation_agent.get_compatible_users"
    },
    
    "send_invite": {
        "description": "Send a dining invitation to a friend",
        "parameters": {
            "friend_id": {"type": "int", "required": False},
            "friend_name": {"type": "str", "required": False},
            "venue_id": {"type": "int", "required": False},
            "venue_name": {"type": "str", "required": False},
            "date_time": {"type": "datetime", "required": False}
        },
        "requires_confirmation": True,
        "handler": "booking_agent.send_invitation"
    },
    
    "respond_to_invite": {
        "description": "Accept or decline a pending invitation",
        "parameters": {
            "invite_id": {"type": "int", "required": True},
            "response": {"type": "str", "enum": ["accept", "decline"]}
        },
        "requires_confirmation": False,
        "handler": "booking_agent.respond_invitation"
    },
    
    "check_venue_availability": {
        "description": "Check if a venue has availability",
        "parameters": {
            "venue_id": {"type": "int", "required": False},
            "venue_name": {"type": "str", "required": False},
            "date_time": {"type": "datetime", "required": False},
            "party_size": {"type": "int", "required": False, "default": 2}
        },
        "requires_confirmation": False,
        "handler": "venue_service.check_availability"
    },
    
    "get_directions": {
        "description": "Get directions to a venue",
        "parameters": {
            "venue_id": {"type": "int", "required": False},
            "venue_name": {"type": "str", "required": False}
        },
        "requires_confirmation": False,
        "handler": "venue_service.get_directions"
    },
    
    "cancel_booking": {
        "description": "Cancel an existing booking",
        "parameters": {
            "booking_id": {"type": "int", "required": False},
            "confirmation_code": {"type": "str", "required": False}
        },
        "requires_confirmation": True,
        "handler": "booking_agent.cancel_booking"
    }
}
```

---

## 6. Voice Gateway Service

### 6.1 Overview

The Voice Gateway is a FastAPI service that manages WebSocket connections and orchestrates the voice interaction:

```
┌─────────────────────────────────────────────────────────────────┐
│                    VOICE GATEWAY SERVICE                         │
│                                                                  │
│  Endpoints:                                                      │
│  ├── WS  /voice/connect           - Main voice WebSocket        │
│  ├── GET /voice/health            - Health check                │
│  ├── GET /voice/session/{id}      - Get session info            │
│  └── DELETE /voice/session/{id}   - End session                 │
│                                                                  │
│  Components:                                                     │
│  ├── ConnectionManager            - WebSocket lifecycle         │
│  ├── SessionManager               - Multi-turn context          │
│  ├── AudioStreamHandler           - Audio processing            │
│  ├── VoiceAgentClient             - Qwen-Omni3 integration      │
│  └── ActionAgentClient            - Action execution            │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### 6.2 WebSocket Protocol

**Connection Handshake:**
```
Client → Server: WebSocket Connect to /voice/connect?user_id={user_id}
Server → Client: { "type": "connected", "session_id": "uuid" }
```

**Audio Streaming (Client → Server):**
```json
{
    "type": "audio_chunk",
    "data": "<base64 encoded audio>",
    "sequence": 1,
    "timestamp": 1701792000000
}
```

**Audio Streaming (Server → Client):**
```json
{
    "type": "audio_chunk", 
    "data": "<base64 encoded audio>",
    "is_final": false
}
```

**Control Messages:**
```json
// Start listening
{ "type": "start_listening" }

// Stop listening  
{ "type": "stop_listening" }

// Interrupt (stop current response)
{ "type": "interrupt" }

// Session end
{ "type": "end_session" }
```

**Status Updates:**
```json
{
    "type": "status",
    "state": "listening|processing|speaking|idle",
    "message": "Processing your request..."
}
```

**Action Confirmation:**
```json
{
    "type": "action_confirmation",
    "action": "make_booking",
    "details": {
        "venue": "Olive Garden",
        "time": "7 PM",
        "party_size": 4
    },
    "confirm_prompt": "Should I book a table for 4 at Olive Garden for 7 PM?"
}
```

### 6.3 Session Management

```
┌─────────────────────────────────────────────────────────────────┐
│                      SESSION STRUCTURE                           │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Session {                                                       │
│    id: "uuid",                                                   │
│    user_id: 123,                                                 │
│    created_at: "2024-12-05T10:00:00Z",                          │
│    state: "listening",                                           │
│                                                                  │
│    // Multi-turn context (NOT persisted)                        │
│    conversation_context: {                                       │
│      turn_count: 3,                                              │
│      recent_intents: ["get_recommendations", "make_booking"],    │
│      entities_mentioned: {                                       │
│        "venue": "Olive Garden",                                  │
│        "party_size": 4                                           │
│      },                                                          │
│      pending_confirmation: null                                  │
│    },                                                            │
│                                                                  │
│    // Metrics                                                    │
│    metrics: {                                                    │
│      total_audio_seconds: 45.2,                                  │
│      actions_executed: 2,                                        │
│      errors: 0                                                   │
│    }                                                             │
│  }                                                               │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### 6.4 Full Duplex Handling

Since the system is full-duplex (user can speak while system is responding):

```
┌─────────────────────────────────────────────────────────────────┐
│                    FULL DUPLEX FLOW                              │
│                                                                  │
│  Timeline:                                                       │
│  ─────────────────────────────────────────────────────────────  │
│                                                                  │
│  User:    [Speaking...]                                          │
│  System:                  [Processing] [Speaking response...]    │
│  User:                                      [Interrupts!]        │
│  System:                                      [STOP]             │
│  System:                                          [New process]  │
│                                                                  │
│  Implementation:                                                 │
│  1. System maintains separate input/output audio streams        │
│  2. Voice Activity Detection (VAD) on input stream               │
│  3. When user speaks during system output:                       │
│     - If > threshold duration: treat as interruption             │
│     - Stop current output immediately                            │
│     - Process new input                                          │
│  4. Interruption sensitivity configurable                        │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## 7. Intent Recognition System

### 7.1 Intent Categories

```
┌─────────────────────────────────────────────────────────────────┐
│                    INTENT TAXONOMY                               │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  BOOKING INTENTS                                                 │
│  ├── make_booking          "Book a table at..."                 │
│  ├── modify_booking        "Change my reservation to..."        │
│  ├── cancel_booking        "Cancel my booking..."               │
│  └── check_booking         "What are my upcoming bookings?"     │
│                                                                  │
│  DISCOVERY INTENTS                                               │
│  ├── get_recommendations   "Find me a good Italian place..."   │
│  ├── search_venue          "Is there a Starbucks nearby?"       │
│  ├── venue_info            "Tell me about The Blue Plate..."    │
│  └── check_availability    "Is Olive Garden open tonight?"      │
│                                                                  │
│  SOCIAL INTENTS                                                  │
│  ├── find_friends          "Who else wants to go to..."         │
│  ├── send_invite           "Invite Sarah to dinner..."          │
│  ├── respond_invite        "Accept the invite from John..."     │
│  └── check_invites         "Do I have any pending invites?"     │
│                                                                  │
│  NAVIGATION INTENTS                                              │
│  ├── get_directions        "How do I get to..."                 │
│  └── estimate_travel       "How long to get to..."              │
│                                                                  │
│  CONVERSATIONAL INTENTS                                          │
│  ├── greeting              "Hello" / "Hey Luna"                  │
│  ├── thanks                "Thank you"                           │
│  ├── help                  "What can you do?"                   │
│  ├── confirm               "Yes" / "Confirm" / "Go ahead"        │
│  ├── deny                  "No" / "Cancel" / "Never mind"        │
│  └── unclear               [Fallback for unrecognized]           │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### 7.2 Entity Extraction

```
┌─────────────────────────────────────────────────────────────────┐
│                    ENTITY TYPES                                  │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Entity Type        Examples                    Resolution       │
│  ──────────────────────────────────────────────────────────────  │
│  VENUE_NAME         "Olive Garden", "that       → venue_id       │
│                      Italian place"                              │
│                                                                  │
│  PERSON_NAME        "Sarah", "my friend John"   → user_id        │
│                                                                  │
│  DATE_TIME          "tonight", "7pm tomorrow",  → datetime       │
│                      "next Friday evening"                       │
│                                                                  │
│  PARTY_SIZE         "for 4", "just me",         → int            │
│                      "table for two"                             │
│                                                                  │
│  CUISINE_TYPE       "Italian", "sushi",         → cuisine_enum   │
│                      "something spicy"                           │
│                                                                  │
│  PRICE_RANGE        "cheap", "fancy",           → price_level    │
│                      "mid-range"                                 │
│                                                                  │
│  DISTANCE           "nearby", "within 5 miles"  → km             │
│                                                                  │
│  CONFIRMATION       "yes", "sure", "no",        → bool           │
│                      "cancel that"                               │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### 7.3 Entity Resolution

For entities like `venue_name` that need to be resolved to IDs:

```
User says: "Book a table at that Italian place we went to last week"

Entity Extraction:
{
    "venue_name": "that Italian place we went to last week",
    "temporal_reference": "last week"
}

Resolution Process:
1. Check conversation context for recently mentioned venues
2. Query user's recent booking history
3. Fuzzy match against venue database
4. If ambiguous, ask for clarification

Resolution Result:
{
    "venue_id": 42,
    "venue_name": "Carrabba's Italian Grill",
    "confidence": 0.85
}
```

---

## 8. Action Agent Design

### 8.1 LangGraph State Definition

```python
# Action Agent state structure

class ActionAgentState(TypedDict):
    """State for the Action Agent graph."""
    
    # Input from Voice Agent
    session_id: str
    user_id: int
    intent: str
    entities: Dict[str, Any]
    confidence: float
    
    # Context from conversation
    context: Dict[str, Any]
    
    # Processing state
    resolved_entities: Dict[str, Any]
    selected_tool: Optional[str]
    tool_params: Dict[str, Any]
    
    # Execution
    execution_result: Optional[Dict[str, Any]]
    execution_status: str  # pending, success, failed, needs_confirmation
    
    # Output
    response_text: str
    follow_up_prompt: Optional[str]
    errors: List[str]
```

### 8.2 Action Agent Graph

```
                            ┌──────────────┐
                            │    START     │
                            └──────┬───────┘
                                   │
                                   ▼
                            ┌──────────────┐
                            │    PARSE     │
                            │   (Intent)   │
                            └──────┬───────┘
                                   │
                     ┌─────────────┼─────────────┐
                     │             │             │
               Actionable    Conversational   Unknown
                     │             │             │
                     ▼             ▼             ▼
              ┌──────────┐  ┌──────────┐  ┌──────────┐
              │ RESOLVE  │  │ RESPOND  │  │ CLARIFY  │
              │ Entities │  │ Direct   │  │ (Ask)    │
              └────┬─────┘  └────┬─────┘  └────┬─────┘
                   │             │             │
                   ▼             │             │
              ┌──────────┐       │             │
              │ VALIDATE │       │             │
              │ Params   │       │             │
              └────┬─────┘       │             │
                   │             │             │
         ┌─────────┴─────────┐   │             │
         │                   │   │             │
       Valid             Invalid │             │
         │                   │   │             │
         ▼                   ▼   │             │
    ┌──────────┐       ┌──────────┐            │
    │ CONFIRM? │       │  ERROR   │            │
    │ (if req) │       │ Response │            │
    └────┬─────┘       └────┬─────┘            │
         │                  │                  │
    ┌────┴────┐             │                  │
    │         │             │                  │
  Needed  Not Needed        │                  │
    │         │             │                  │
    ▼         ▼             │                  │
┌────────┐ ┌────────┐       │                  │
│PENDING │ │EXECUTE │       │                  │
│CONFIRM │ │ Action │       │                  │
└───┬────┘ └───┬────┘       │                  │
    │          │            │                  │
    │     ┌────┴────┐       │                  │
    │     │         │       │                  │
    │  Success   Failed     │                  │
    │     │         │       │                  │
    │     ▼         ▼       │                  │
    │ ┌────────┐ ┌────────┐ │                  │
    │ │ FORMAT │ │ RETRY/ │ │                  │
    │ │ Result │ │ ERROR  │ │                  │
    │ └───┬────┘ └───┬────┘ │                  │
    │     │          │      │                  │
    └─────┴────┬─────┴──────┴──────────────────┘
               │
               ▼
        ┌──────────────┐
        │     END      │
        │  (Response)  │
        └──────────────┘
```

### 8.3 Action Agent Nodes

| Node | Input | Output | Description |
|------|-------|--------|-------------|
| PARSE | Raw intent + entities | Categorized intent | Classify intent type and extract key information |
| RESOLVE | Entity names/references | Entity IDs | Resolve names to database IDs, disambiguate |
| VALIDATE | Resolved entities | Validation result | Check required params, validate constraints |
| CONFIRM | Action details | Confirmation prompt | Generate confirmation request for critical actions |
| EXECUTE | Validated params | Action result | Call appropriate tool/handler |
| FORMAT | Raw result | Spoken response | Convert result to natural language |
| ERROR | Error info | Error response | Generate helpful error message |
| CLARIFY | Incomplete info | Clarification question | Ask user for missing information |

---

## 9. API Specifications

### 9.1 Voice Gateway Endpoints

#### WebSocket: Connect Voice Session
```
WS /api/v1/voice/connect

Query Parameters:
- user_id: int (required) - The user initiating voice session

Connection Response:
{
    "type": "connected",
    "session_id": "uuid",
    "config": {
        "sample_rate": 16000,
        "encoding": "opus",
        "language": "en-US"
    }
}
```

#### GET: Voice Health Check
```
GET /api/v1/voice/health

Response:
{
    "status": "healthy",
    "model_status": "ready",
    "active_sessions": 5,
    "avg_latency_ms": 250
}
```

#### GET: Session Info
```
GET /api/v1/voice/session/{session_id}

Response:
{
    "session_id": "uuid",
    "user_id": 123,
    "state": "idle",
    "created_at": "2024-12-05T10:00:00Z",
    "turn_count": 5,
    "actions_executed": 2
}
```

### 9.2 Internal Action Agent API

These are internal APIs called by the Voice Gateway:

#### POST: Execute Action
```
POST /api/v1/voice/action/execute

Request:
{
    "session_id": "uuid",
    "user_id": 123,
    "intent": "make_booking",
    "entities": {
        "venue_name": "Olive Garden",
        "party_size": 4,
        "date_time": "2024-12-05T19:00:00"
    },
    "context": {
        "turn_count": 2,
        "confirmed": false
    }
}

Response:
{
    "status": "success",
    "action": "make_booking",
    "result": {
        "booking_id": 456,
        "confirmation_code": "ABC123"
    },
    "speak_text": "Done! I've booked a table for 4...",
    "follow_up_prompt": "Would you like to invite anyone?"
}
```

#### POST: Confirm Pending Action
```
POST /api/v1/voice/action/confirm

Request:
{
    "session_id": "uuid",
    "confirmed": true
}

Response:
{
    "status": "executed",
    "result": { ... }
}
```

---

## 10. Frontend Integration

### 10.1 User App Structure

The voice interface will be integrated into the existing `/user-app` Next.js application:

```
user-app/
├── app/
│   └── ... (existing routes)
├── components/
│   ├── shared/
│   │   └── ... (existing)
│   ├── user/
│   │   └── ... (existing)
│   └── voice/                    # NEW: Voice components
│       ├── VoiceButton.tsx       # Main voice activation button
│       ├── VoiceOverlay.tsx      # Full-screen voice interface
│       ├── VoiceWaveform.tsx     # Audio visualization
│       ├── VoiceStatus.tsx       # Status indicator
│       ├── VoiceTranscript.tsx   # Live transcript display
│       └── VoiceConfirmation.tsx # Action confirmation UI
├── hooks/
│   ├── ... (existing)
│   └── useVoice.ts               # NEW: Voice session hook
├── lib/
│   ├── ... (existing)
│   └── voice/                    # NEW: Voice utilities
│       ├── audio-capture.ts      # Audio recording
│       ├── audio-playback.ts     # Audio playback
│       ├── websocket-client.ts   # Voice WebSocket
│       └── voice-state.ts        # State machine
├── stores/
│   ├── ... (existing)
│   └── voiceStore.ts             # NEW: Voice state store
└── types/
    └── voice.ts                  # NEW: Voice types
```

### 10.2 Voice Button Integration

The voice button will be a floating action button available across the app:

```
┌─────────────────────────────────────────────────────────────────┐
│                         USER APP LAYOUT                          │
│                                                                  │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │                      Navigation                            │  │
│  └───────────────────────────────────────────────────────────┘  │
│                                                                  │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │                                                            │  │
│  │                                                            │  │
│  │                     Page Content                           │  │
│  │                                                            │  │
│  │                                                            │  │
│  │                                                            │  │
│  └───────────────────────────────────────────────────────────┘  │
│                                                                  │
│                                              ┌────────────────┐  │
│                                              │  🎤 Voice      │  │
│                                              │   Button       │  │
│                                              └────────────────┘  │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### 10.3 Voice Overlay UI

When voice is activated, a full-screen overlay appears:

```
┌─────────────────────────────────────────────────────────────────┐
│                       VOICE OVERLAY                              │
│                                                                  │
│                    ┌─────────────────┐                          │
│                    │  Luna is        │                          │
│                    │  listening...   │                          │
│                    └─────────────────┘                          │
│                                                                  │
│                    ╭──────────────────╮                         │
│                    │                  │                          │
│                    │   [Waveform]     │                          │
│                    │   Animation      │                          │
│                    │                  │                          │
│                    ╰──────────────────╯                          │
│                                                                  │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │                                                            │  │
│  │  "Find me a good Italian restaurant nearby for dinner     │  │
│  │   tonight..."                                              │  │
│  │                                                            │  │
│  │                              [Live Transcript]             │  │
│  └───────────────────────────────────────────────────────────┘  │
│                                                                  │
│             ┌──────────┐              ┌──────────┐              │
│             │  Cancel  │              │   Done   │              │
│             └──────────┘              └──────────┘              │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### 10.4 Voice State Hook

```typescript
// Conceptual API for useVoice hook

interface UseVoiceReturn {
    // State
    isConnected: boolean;
    isListening: boolean;
    isSpeaking: boolean;
    isProcessing: boolean;
    
    // Session info
    sessionId: string | null;
    turnCount: number;
    
    // Transcript
    userTranscript: string;
    assistantTranscript: string;
    
    // Confirmation
    pendingConfirmation: ActionConfirmation | null;
    
    // Actions
    startListening: () => Promise<void>;
    stopListening: () => void;
    interrupt: () => void;
    confirmAction: (confirmed: boolean) => void;
    endSession: () => void;
    
    // Error
    error: Error | null;
}
```

---

## 11. Hathora Deployment

### 11.1 Deployment Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    HATHORA DEPLOYMENT                            │
│                                                                  │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │                     FLEET: voice-gateway                   │  │
│  │                                                            │  │
│  │  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐          │  │
│  │  │  Instance   │ │  Instance   │ │  Instance   │  Auto-   │  │
│  │  │  (Chicago)  │ │ (Frankfurt) │ │ (Singapore) │  scaled  │  │
│  │  └─────────────┘ └─────────────┘ └─────────────┘          │  │
│  │                                                            │  │
│  │  Container: voice-gateway-service                          │  │
│  │  Ports: 8080 (WebSocket), 8081 (HTTP)                      │  │
│  │  Resources: 2 vCPU, 4GB RAM per instance                   │  │
│  │                                                            │  │
│  └───────────────────────────────────────────────────────────┘  │
│                                                                  │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │                     FLEET: action-agent                    │  │
│  │                                                            │  │
│  │  ┌─────────────┐ ┌─────────────┐                          │  │
│  │  │  Instance   │ │  Instance   │  Auto-scaled              │  │
│  │  │     (US)    │ │    (EU)     │  based on load           │  │
│  │  └─────────────┘ └─────────────┘                          │  │
│  │                                                            │  │
│  │  Container: action-agent-service                           │  │
│  │  Ports: 8080 (HTTP)                                        │  │
│  │  Resources: 1 vCPU, 2GB RAM per instance                   │  │
│  │                                                            │  │
│  └───────────────────────────────────────────────────────────┘  │
│                                                                  │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │                   EXTERNAL SERVICES                        │  │
│  │                                                            │  │
│  │  ┌─────────────────────────────────────────────────────┐  │  │
│  │  │ Qwen-Omni3 API (Alibaba Cloud / Self-hosted)        │  │  │
│  │  └─────────────────────────────────────────────────────┘  │  │
│  │                                                            │  │
│  │  ┌─────────────────────────────────────────────────────┐  │  │
│  │  │ Luna Social Backend (Existing FastAPI)              │  │  │
│  │  └─────────────────────────────────────────────────────┘  │  │
│  │                                                            │  │
│  └───────────────────────────────────────────────────────────┘  │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### 11.2 Hathora Configuration

```yaml
# hathora.yaml - Voice Gateway Fleet

version: 1

fleets:
  voice-gateway:
    build:
      dockerfile: ./voice-gateway/Dockerfile
      context: ./voice-gateway
    
    regions:
      - chicago
      - frankfurt  
      - singapore
      - sao_paulo
    
    scaling:
      min_instances: 1
      max_instances: 10
      target_cpu_utilization: 70
      scale_down_delay_seconds: 300
    
    resources:
      cpu: 2
      memory: 4096  # MB
    
    networking:
      ports:
        - port: 8080
          protocol: websocket
          public: true
        - port: 8081
          protocol: http
          public: true
    
    health_check:
      path: /health
      port: 8081
      interval_seconds: 10
      timeout_seconds: 5
    
    environment:
      QWEN_API_ENDPOINT: ${QWEN_API_ENDPOINT}
      QWEN_API_KEY: ${QWEN_API_KEY}
      LUNA_BACKEND_URL: ${LUNA_BACKEND_URL}
      LOG_LEVEL: INFO

  action-agent:
    build:
      dockerfile: ./action-agent/Dockerfile
      context: ./action-agent
    
    regions:
      - chicago
      - frankfurt
    
    scaling:
      min_instances: 1
      max_instances: 5
      target_cpu_utilization: 60
    
    resources:
      cpu: 1
      memory: 2048
    
    networking:
      ports:
        - port: 8080
          protocol: http
          public: false  # Internal only
    
    environment:
      LUNA_BACKEND_URL: ${LUNA_BACKEND_URL}
      DATABASE_URL: ${DATABASE_URL}
```

### 11.3 Container Structure

```dockerfile
# voice-gateway/Dockerfile

FROM python:3.11-slim

WORKDIR /app

# Install audio dependencies
RUN apt-get update && apt-get install -y \
    libportaudio2 \
    libsndfile1 \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Expose ports
EXPOSE 8080 8081

# Run
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]
```

### 11.4 Latency Optimization

Hathora provides several features for low-latency voice:

1. **Edge Load Balancing**: Route users to nearest region
2. **Persistent Connections**: WebSocket connection reuse
3. **Private Networking**: Low-latency internal communication
4. **Auto-scaling**: Handle traffic spikes without latency impact

```
User (NYC) ──────► Edge (Chicago) ──────► Voice Gateway
                      │
                      │ < 20ms internal
                      ▼
               Action Agent ──────► Luna Backend
```

---

## 12. Data Flow & Sequences

### 12.1 Complete Voice Interaction Flow

```
┌─────────┐     ┌─────────────┐     ┌──────────────┐     ┌────────────┐     ┌───────────┐
│  User   │     │ Voice Button│     │Voice Gateway │     │Action Agent│     │Luna Backend│
│ (Mobile)│     │  (Next.js)  │     │  (Hathora)   │     │ (Hathora)  │     │ (FastAPI) │
└────┬────┘     └──────┬──────┘     └──────┬───────┘     └─────┬──────┘     └─────┬─────┘
     │                 │                   │                   │                  │
     │  Tap Voice Btn  │                   │                   │                  │
     │────────────────▶│                   │                   │                  │
     │                 │                   │                   │                  │
     │                 │  WebSocket Connect│                   │                  │
     │                 │──────────────────▶│                   │                  │
     │                 │                   │                   │                  │
     │                 │  Connected + SessionID                │                  │
     │                 │◀──────────────────│                   │                  │
     │                 │                   │                   │                  │
     │    Speak        │                   │                   │                  │
     │  "Book a table" │                   │                   │                  │
     │────────────────▶│                   │                   │                  │
     │                 │                   │                   │                  │
     │                 │  Audio Chunks     │                   │                  │
     │                 │══════════════════▶│                   │                  │
     │                 │  (streaming)      │                   │                  │
     │                 │                   │                   │                  │
     │                 │  Status: Processing                   │                  │
     │                 │◀──────────────────│                   │                  │
     │                 │                   │                   │                  │
     │                 │                   │  Qwen-Omni3       │                  │
     │                 │                   │  Process Audio    │                  │
     │                 │                   │────────┐          │                  │
     │                 │                   │        │          │                  │
     │                 │                   │◀───────┘          │                  │
     │                 │                   │                   │                  │
     │                 │                   │  Intent: make_booking               │
     │                 │                   │  Entities: {...}  │                  │
     │                 │                   │──────────────────▶│                  │
     │                 │                   │                   │                  │
     │                 │                   │                   │  Resolve venue   │
     │                 │                   │                   │─────────────────▶│
     │                 │                   │                   │                  │
     │                 │                   │                   │  Venue details   │
     │                 │                   │                   │◀─────────────────│
     │                 │                   │                   │                  │
     │                 │                   │  Needs Confirmation                  │
     │                 │                   │◀──────────────────│                  │
     │                 │                   │                   │                  │
     │                 │  Audio: "Should I │                   │                  │
     │                 │  book at Olive..."│                   │                  │
     │                 │◀══════════════════│                   │                  │
     │                 │  (streaming audio)│                   │                  │
     │                 │                   │                   │                  │
     │ Hear response   │                   │                   │                  │
     │◀────────────────│                   │                   │                  │
     │                 │                   │                   │                  │
     │  "Yes, confirm" │                   │                   │                  │
     │────────────────▶│                   │                   │                  │
     │                 │                   │                   │                  │
     │                 │  Audio Chunks     │                   │                  │
     │                 │══════════════════▶│                   │                  │
     │                 │                   │                   │                  │
     │                 │                   │  Qwen: Confirm    │                  │
     │                 │                   │──────────────────▶│                  │
     │                 │                   │                   │                  │
     │                 │                   │                   │  Create booking  │
     │                 │                   │                   │─────────────────▶│
     │                 │                   │                   │                  │
     │                 │                   │                   │  Booking created │
     │                 │                   │                   │◀─────────────────│
     │                 │                   │                   │                  │
     │                 │                   │  Success + Result │                  │
     │                 │                   │◀──────────────────│                  │
     │                 │                   │                   │                  │
     │                 │  Audio: "Done!    │                   │                  │
     │                 │  Confirmation..." │                   │                  │
     │                 │◀══════════════════│                   │                  │
     │                 │                   │                   │                  │
     │ Hear confirm    │                   │                   │                  │
     │◀────────────────│                   │                   │                  │
     │                 │                   │                   │                  │
```

### 12.2 Error Handling Flow

```
┌─────────┐     ┌─────────────┐     ┌──────────────┐
│  User   │     │Voice Gateway│     │Action Agent  │
└────┬────┘     └──────┬──────┘     └──────┬───────┘
     │                 │                   │
     │  "Book at XYZ"  │                   │
     │────────────────▶│                   │
     │                 │                   │
     │                 │  Intent: booking  │
     │                 │──────────────────▶│
     │                 │                   │
     │                 │  Error: Venue     │
     │                 │  not found        │
     │                 │◀──────────────────│
     │                 │                   │
     │  "I couldn't    │                   │
     │  find XYZ.      │                   │
     │  Did you mean..."                   │
     │◀────────────────│                   │
     │                 │                   │
```

---

## 13. Error Handling

### 13.1 Error Categories

| Category | Examples | Handling Strategy |
|----------|----------|-------------------|
| **Connection Errors** | WebSocket disconnect, timeout | Auto-reconnect with backoff |
| **Audio Errors** | Mic permission denied, poor quality | User-friendly message, fallback |
| **Speech Errors** | Unrecognized speech, noise | Ask to repeat, provide examples |
| **Intent Errors** | Unclear intent, missing entities | Clarification questions |
| **Action Errors** | Venue not found, booking failed | Explain error, suggest alternatives |
| **System Errors** | Service unavailable, rate limit | Graceful degradation, retry |

### 13.2 Error Response Templates

```python
ERROR_RESPONSES = {
    "connection_lost": {
        "speak": "I'm having trouble with the connection. Please try again in a moment.",
        "action": "auto_reconnect"
    },
    "speech_unclear": {
        "speak": "I didn't catch that. Could you please repeat?",
        "action": "continue_listening"
    },
    "intent_unclear": {
        "speak": "I'm not sure what you'd like to do. You can ask me to find restaurants, make bookings, or connect with friends.",
        "action": "continue_listening"
    },
    "venue_not_found": {
        "speak": "I couldn't find that venue. Could you give me more details or try a different name?",
        "action": "continue_listening"
    },
    "booking_failed": {
        "speak": "I wasn't able to complete that booking. Would you like me to try a different time or venue?",
        "action": "suggest_alternatives"
    },
    "service_unavailable": {
        "speak": "I'm having some technical difficulties right now. Please try again in a few minutes.",
        "action": "end_session"
    }
}
```

### 13.3 Graceful Degradation

```
┌─────────────────────────────────────────────────────────────────┐
│                   GRACEFUL DEGRADATION                           │
│                                                                  │
│  Level 1: Full Voice (Normal)                                    │
│  ├── Speech-to-speech with Qwen-Omni3                           │
│  └── Full action execution                                       │
│                                                                  │
│  Level 2: Voice Input Only (Qwen API issues)                     │
│  ├── Speech-to-text (fallback ASR)                              │
│  ├── Text-based LLM for response                                │
│  └── Text-to-speech (fallback TTS)                              │
│                                                                  │
│  Level 3: Text Mode (Audio system issues)                        │
│  ├── Type instead of speak                                       │
│  ├── Read responses                                              │
│  └── Full functionality preserved                                │
│                                                                  │
│  Level 4: Offline Mode (Network issues)                          │
│  ├── Show cached data                                            │
│  ├── Queue actions for later                                     │
│  └── Notify when back online                                     │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## 14. Testing Strategy

### 14.1 Testing Layers

```
┌─────────────────────────────────────────────────────────────────┐
│                      TESTING PYRAMID                             │
│                                                                  │
│                         ╱╲                                       │
│                        ╱  ╲      E2E Tests                       │
│                       ╱    ╲     (Voice flow testing)            │
│                      ╱──────╲                                    │
│                     ╱        ╲                                   │
│                    ╱ Integration╲   Integration Tests             │
│                   ╱   Tests      ╲  (Agent + Backend)            │
│                  ╱────────────────╲                              │
│                 ╱                  ╲                             │
│                ╱    Unit Tests      ╲  Unit Tests                │
│               ╱                      ╲ (Components, Tools)       │
│              ╱────────────────────────╲                          │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### 14.2 Test Categories

| Category | Scope | Tools |
|----------|-------|-------|
| **Unit Tests** | Individual functions, tools | pytest, unittest.mock |
| **Integration Tests** | Agent workflows, API chains | pytest-asyncio, httpx |
| **Audio Tests** | Audio processing, encoding | Audio fixtures, mock streams |
| **Intent Tests** | Intent classification accuracy | Test utterance dataset |
| **E2E Tests** | Full voice flows | Playwright, audio simulation |
| **Load Tests** | Concurrent sessions, latency | Locust, k6 |

### 14.3 Test Utterance Dataset

```json
{
    "booking_intents": [
        {
            "utterance": "Book a table for 4 at Olive Garden tonight at 7",
            "expected_intent": "make_booking",
            "expected_entities": {
                "venue_name": "Olive Garden",
                "party_size": 4,
                "time": "tonight at 7"
            }
        },
        {
            "utterance": "I need a reservation for two, somewhere nice for our anniversary",
            "expected_intent": "make_booking",
            "expected_entities": {
                "party_size": 2,
                "occasion": "anniversary"
            }
        }
    ],
    "recommendation_intents": [
        {
            "utterance": "Find me a good sushi place nearby",
            "expected_intent": "get_recommendations",
            "expected_entities": {
                "cuisine": "sushi",
                "distance": "nearby"
            }
        }
    ]
}
```

### 14.4 Mock Audio Generation

For testing without real microphone input:

```python
# Test utilities for audio mocking

class MockAudioStream:
    """Generate mock audio for testing."""
    
    @staticmethod
    def from_text(text: str, voice: str = "default") -> bytes:
        """Generate audio bytes from text using TTS."""
        # Use a fast TTS for test audio generation
        pass
    
    @staticmethod
    def silence(duration_ms: int) -> bytes:
        """Generate silence audio."""
        pass
    
    @staticmethod
    def noise(duration_ms: int, level: float = 0.1) -> bytes:
        """Generate background noise for robustness testing."""
        pass
```

---

## 15. Implementation Phases

### Phase 1: Foundation (Week 1-2)

**Goal**: Basic infrastructure and WebSocket communication

- [ ] Set up Voice Gateway service structure
- [ ] Implement WebSocket connection manager
- [ ] Create basic session management
- [ ] Set up Hathora project and initial deployment
- [ ] Frontend: Voice button component (no audio yet)
- [ ] Frontend: WebSocket client hook

**Deliverables**:
- Working WebSocket connection between app and gateway
- Basic session create/end functionality
- Hathora deployment pipeline

### Phase 2: Audio Pipeline (Week 2-3)

**Goal**: Audio capture, streaming, and playback

- [ ] Frontend: Audio capture with MediaRecorder
- [ ] Frontend: Audio playback with Web Audio API
- [ ] Gateway: Audio stream handling
- [ ] Gateway: Audio format conversion
- [ ] Gateway: Voice Activity Detection (VAD)
- [ ] Bidirectional audio streaming working

**Deliverables**:
- Audio can be captured and streamed to gateway
- Audio can be received and played back
- VAD detects speech start/end

### Phase 3: Voice Model Integration (Week 3-4)

**Goal**: Integrate Qwen-Omni3 for speech understanding

- [ ] Qwen-Omni3 API client
- [ ] Audio input processing
- [ ] Speech-to-text/understanding
- [ ] Text-to-speech/audio generation
- [ ] Streaming response handling
- [ ] Basic conversation flow

**Deliverables**:
- Can have basic conversation with voice
- System understands and responds appropriately
- Streaming audio responses work

### Phase 4: Action Agent (Week 4-5)

**Goal**: Implement action execution system

- [ ] LangGraph Action Agent setup
- [ ] Tool registry with all actions
- [ ] Entity resolution service
- [ ] Integration with existing Luna APIs
- [ ] Confirmation flow for critical actions
- [ ] Error handling and recovery

**Deliverables**:
- Voice commands execute real actions
- Bookings, recommendations work via voice
- Confirmation flow for bookings

### Phase 5: Intent System (Week 5-6)

**Goal**: Robust intent recognition and multi-turn

- [ ] Intent classification tuning
- [ ] Entity extraction refinement
- [ ] Multi-turn context handling
- [ ] Clarification dialogs
- [ ] Edge case handling

**Deliverables**:
- High accuracy intent recognition
- Natural multi-turn conversations
- Graceful handling of unclear requests

### Phase 6: Polish & Production (Week 6-7)

**Goal**: Production readiness

- [ ] Full duplex handling (interruption)
- [ ] Error handling and graceful degradation
- [ ] Performance optimization
- [ ] Load testing
- [ ] Security review
- [ ] Documentation

**Deliverables**:
- Production-ready voice system
- Performance within latency targets
- Comprehensive error handling

### Phase 7: Launch & Iterate (Week 7+)

**Goal**: Launch and improve based on usage

- [ ] Staged rollout
- [ ] Usage analytics
- [ ] User feedback collection
- [ ] Iterative improvements
- [ ] Additional features backlog

---

## 16. Open Questions & Decisions

### 16.1 Technical Decisions Needed

| # | Question | Options | Recommendation | Status |
|---|----------|---------|----------------|--------|
| 1 | Qwen-Omni3 hosting | Cloud API vs Self-hosted on Hathora | Cloud API for v1 (simpler) | **PENDING** |
| 2 | Audio codec for streaming | Opus vs WAV vs WebM | Opus (best latency/quality) | **PENDING** |
| 3 | Session timeout | 1min, 5min, 10min, no timeout | 5 minutes of inactivity | **PENDING** |
| 4 | Action confirmation | Always / Critical only / Never | Critical actions only | **PENDING** |
| 5 | Transcript display | Real-time / After utterance / None | Real-time during speech | **PENDING** |

### 16.2 Business Decisions Needed

| # | Question | Notes | Status |
|---|----------|-------|--------|
| 1 | Qwen-Omni3 API access | Need Alibaba Cloud account, API keys | **PENDING** |
| 2 | Hathora account setup | Need to create account, configure billing | **PENDING** |
| 3 | Voice branding | Voice persona name (Luna?), personality | **PENDING** |
| 4 | Usage limits | Max sessions per user, daily limits | **PENDING** |
| 5 | Fallback behavior | What happens if voice unavailable | **PENDING** |

### 16.3 Future Considerations (Post v1.0)

- Multi-language support
- Voice authentication/biometrics
- Proactive notifications via voice
- Voice customization (speed, formality)
- Conversation history and context
- Integration with smart speakers
- Offline voice commands (limited)

---

## Appendix A: Glossary

| Term | Definition |
|------|------------|
| **ASR** | Automatic Speech Recognition - converting speech to text |
| **TTS** | Text-to-Speech - converting text to audio |
| **VAD** | Voice Activity Detection - detecting when someone is speaking |
| **Full Duplex** | Both parties can speak/listen simultaneously |
| **Intent** | The user's goal or desired action |
| **Entity** | Specific pieces of information (venue name, time, etc.) |
| **Slot Filling** | Collecting required entities for an action |
| **Turn** | One exchange in conversation (user speaks → system responds) |

---

## Appendix B: Reference Links

- [Qwen-Omni3 Documentation](https://github.com/QwenLM/Qwen) - Model details
- [Hathora Documentation](https://hathora.dev/docs) - Deployment platform
- [LangGraph Documentation](https://python.langchain.com/docs/langgraph) - Agent framework
- [Web Audio API](https://developer.mozilla.org/en-US/docs/Web/API/Web_Audio_API) - Browser audio
- [MediaRecorder API](https://developer.mozilla.org/en-US/docs/Web/API/MediaRecorder) - Audio recording
- [FastAPI WebSockets](https://fastapi.tiangolo.com/advanced/websockets/) - WebSocket handling

---

## Appendix C: File Structure Summary

```
luna_assignment/
├── backend/
│   ├── app/
│   │   ├── agents/
│   │   │   ├── voice_agent.py          # NEW: Qwen-Omni3 integration
│   │   │   ├── action_agent.py         # NEW: LangGraph action agent
│   │   │   └── ... (existing)
│   │   ├── api/
│   │   │   └── routes/
│   │   │       ├── voice.py            # NEW: Voice endpoints
│   │   │       └── ... (existing)
│   │   ├── services/
│   │   │   ├── voice_gateway.py        # NEW: WebSocket handling
│   │   │   ├── audio_processing.py     # NEW: Audio utilities
│   │   │   ├── qwen_client.py          # NEW: Qwen API client
│   │   │   └── ... (existing)
│   │   └── ... (existing)
│   └── ... (existing)
│
├── voice-gateway/                       # NEW: Hathora service
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── main.py
│   ├── config.py
│   ├── websocket_handler.py
│   ├── session_manager.py
│   ├── audio_stream.py
│   └── qwen_integration.py
│
├── action-agent/                        # NEW: Hathora service
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── main.py
│   ├── agent_graph.py
│   ├── tools/
│   │   ├── booking_tools.py
│   │   ├── recommendation_tools.py
│   │   ├── social_tools.py
│   │   └── venue_tools.py
│   └── entity_resolver.py
│
├── user-app/
│   ├── components/
│   │   └── voice/                       # NEW: Voice UI
│   │       ├── VoiceButton.tsx
│   │       ├── VoiceOverlay.tsx
│   │       └── ...
│   ├── hooks/
│   │   └── useVoice.ts                  # NEW
│   ├── lib/
│   │   └── voice/                       # NEW
│   │       └── ...
│   └── ... (existing)
│
├── hathora.yaml                         # NEW: Hathora config
└── VOICE_AGENT_IMPLEMENTATION_SPEC.md   # This document
```

---

**Document Status**: Draft  
**Last Updated**: December 2024  
**Authors**: Engineering Team  
**Reviewers**: [Pending]

