/**
 * Shared types for Agent Views
 */

export interface User {
  id: number
  username: string
  persona?: string
  latitude?: number
  longitude?: number
}

export interface Venue {
  id: number
  name: string
  cuisine: string
  price_level: number
  distance_km?: number
  trending?: boolean
  category?: string
}

export interface RecommendationContext {
  meal_time: string
  is_weekend: boolean
  hour: number
  user_location: {
    lat: number
    lon: number
  }
  user_persona: string | null
  preferences: {
    cuisines: string[]
    price_range: number[]
    max_distance: number
  }
}

export interface VenueRecommendation {
  id: number
  name: string
  cuisine: string
  price_level: number
  distance_km: number
  compatibility_score: number
  trending?: boolean
  category?: string
  explanation?: string
  score_breakdown?: {
    cuisine_match: number
    distance: number
    price_fit: number
    social_compatibility: number
    trending_factor: number
  }
}

export interface SocialMatch {
  id: number
  username: string
  compatibility_score: number
  reasons: string[]
  shared_interests?: string[]
  mutual_friends?: number
  status?: string
  llm_reasoning?: string
}

export interface RecommendationData {
  user_id: number
  user: User
  venues: VenueRecommendation[]
  people: SocialMatch[]
  context: RecommendationContext
  explanations: string[]
  generated_at: string
}

export interface BookingStep {
  name: string
  status: 'completed' | 'active' | 'waiting' | 'pending' | 'failed'
  duration?: number
  details?: string
}

export interface BookingInvitee {
  id: number
  username: string
  status: 'pending' | 'accepted' | 'declined' | 'no_response'
  response_time?: number
  message?: string
}

export interface BookingData {
  id: number
  organizer_id: number
  organizer_name: string
  venue_id: number
  venue_name: string
  venue_photo?: string
  party_size: number
  requested_party_size: number
  booking_time: string
  confirmation_code?: string
  status: 'initiated' | 'pending' | 'confirmed' | 'failed'
  steps: BookingStep[]
  invitees: BookingInvitee[]
  decision_log: DecisionLogEntry[]
  special_requests?: string
  created_at: string
  error_reason?: string
}

export interface DecisionLogEntry {
  timestamp: string
  message: string
  type?: 'info' | 'success' | 'warning' | 'error'
}

export interface BookingError {
  booking_id: number
  timestamp: string
  user_id: number
  venue_id: number
  venue_name: string
  reason: string
  agent_decision?: string
  retry_scheduled?: boolean
}

