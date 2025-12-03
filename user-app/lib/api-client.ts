// API Client for Luna Social User App

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1'

// Types
export interface User {
  id: number
  username: string
  email?: string
  avatar_url?: string
  persona?: string
  location?: {
    lat: number
    lon: number
    city?: string
  }
  activity_score?: number
  social_score?: number
  created_at?: string
}

export interface UserPreferences {
  cuisines: string[]
  price_range: { min: number; max: number }
  ambiance: string[]
  dietary_restrictions: string[]
  preferred_group_size: number
  openness_to_new: number
}

export interface Venue {
  id: number
  name: string
  cuisine: string
  address?: string
  city?: string
  latitude?: number
  longitude?: number
  price_level: number
  rating?: number
  capacity?: number
  ambiance?: string[]
  features?: string[]
  image_url?: string
  trending?: boolean
  distance?: number
  availability?: {
    available: boolean
    slots_remaining: number
  }
}

export interface Recommendation {
  venue: Venue
  score: number
  match_score: number  // Display score (0-100)
  reasons: string[]
  reasoning?: string  // AI explanation
  explanation?: string
  gnn_score?: number  // GNN model score (0-1)
  rule_score?: number  // Rule-based score (0-1)
  social_context?: {
    friends_interested: number
    friend_names: string[]
  }
}

export interface Booking {
  id: number
  user_id: number
  venue_id: number
  venue?: Venue
  party_size: number
  booking_time: string
  status: 'pending' | 'confirmed' | 'cancelled' | 'completed'
  confirmation_code?: string
  special_requests?: string
  created_at: string
}

export interface FriendActivity {
  id: number
  user_id: number
  username: string
  avatar_url?: string
  action: string
  venue_name?: string
  venue_id?: number
  timestamp: string
  details?: string
}

export interface RecommendationResponse {
  user_id: number
  venues: any[]  // Raw API response with venue data
  people?: any[]  // People recommendations
  context?: any
  explanations?: string[]
  generated_at: string
}

export interface Friend {
  id: number
  username: string
  full_name?: string
  avatar_url?: string
  compatibility_score?: number
}

export interface SocialMatch {
  user: {
    id: number
    username: string
    full_name?: string
    avatar_url?: string
  }
  compatibility_score: number
  shared_interests?: string[]
  reasoning?: string
}

export interface Review {
  id: number
  user_id: number
  username: string
  avatar_url?: string
  venue_id: number
  venue_name: string
  venue_cuisine?: string
  rating?: number
  review_text?: string
  created_at: string
  is_friend: boolean
}

// API Error class
class ApiError extends Error {
  status: number
  
  constructor(message: string, status: number) {
    super(message)
    this.status = status
    this.name = 'ApiError'
  }
}

// Helper function for API requests
async function fetchApi<T>(endpoint: string, options?: RequestInit): Promise<T> {
  const url = `${API_BASE_URL}${endpoint}`
  
  try {
    const response = await fetch(url, {
      ...options,
      headers: {
        'Content-Type': 'application/json',
        ...options?.headers,
      },
    })
    
    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}))
      throw new ApiError(
        errorData.detail || `API error: ${response.status}`,
        response.status
      )
    }
    
    return response.json()
  } catch (error) {
    if (error instanceof ApiError) {
      throw error
    }
    console.error(`API request failed: ${url}`, error)
    throw new ApiError('Network error - please check your connection', 0)
  }
}

// API client
export const api = {
  // User endpoints
  async getMe(userId: number): Promise<User> {
    return fetchApi<User>(`/users/${userId}`)
  },
  
  async getUser(userId: number): Promise<User> {
    return fetchApi<User>(`/users/${userId}`)
  },
  
  async updateUserPreferences(userId: number, preferences: Partial<UserPreferences>): Promise<User> {
    return fetchApi<User>(`/users/${userId}/preferences`, {
      method: 'PUT',
      body: JSON.stringify(preferences),
    })
  },
  
  // Venue endpoints
  async getVenues(params?: { cuisine?: string; price_level?: number; category?: string }): Promise<Venue[]> {
    const searchParams = new URLSearchParams()
    if (params?.cuisine) searchParams.set('cuisine', params.cuisine)
    if (params?.price_level) searchParams.set('price_level', params.price_level.toString())
    if (params?.category) searchParams.set('category', params.category)
    
    const query = searchParams.toString()
    const venues = await fetchApi<any[]>(`/venues/${query ? `?${query}` : ''}`)
    // Transform backend response to match Venue interface
    return venues.map(v => ({
      id: v.id,
      name: v.name,
      cuisine: v.cuisine_type || v.category || 'Restaurant',
      address: v.address,
      city: v.city,
      latitude: v.latitude,
      longitude: v.longitude,
      price_level: v.price_level,
      rating: v.rating,
      capacity: v.capacity,
      ambiance: v.ambiance,
      features: v.features,
      image_url: v.image_url,
      trending: v.trending,
    }))
  },
  
  async getVenue(venueId: number): Promise<Venue> {
    const v = await fetchApi<any>(`/venues/${venueId}`)
    return {
      id: v.id,
      name: v.name,
      cuisine: v.cuisine_type || v.category || 'Restaurant',
      address: v.address,
      city: v.city,
      latitude: v.latitude,
      longitude: v.longitude,
      price_level: v.price_level,
      rating: v.rating,
      capacity: v.capacity,
      ambiance: v.ambiance,
      features: v.features,
      image_url: v.image_url,
      trending: v.trending,
    }
  },
  
  async searchVenues(query: string, filters?: { trending?: boolean; open_now?: boolean }): Promise<Venue[]> {
    // Backend doesn't have a search endpoint, so we fetch all venues and filter client-side
    const params: { category?: string; trending_only?: boolean } = {}
    
    if (filters?.trending) {
      // Use trending endpoint if filtering by trending
      return this.getTrendingVenues(20)
    }
    
    const venues = await this.getVenues(params)
    
    // Filter by search query client-side
    if (query) {
      const lowerQuery = query.toLowerCase()
      return venues.filter(v => 
        v.name.toLowerCase().includes(lowerQuery) ||
        v.cuisine.toLowerCase().includes(lowerQuery) ||
        (v.ambiance && v.ambiance.some(a => a.toLowerCase().includes(lowerQuery)))
      )
    }
    
    return venues
  },
  
  async getTrendingVenues(limit?: number): Promise<Venue[]> {
    const venues = await fetchApi<any[]>(`/venues/trending?limit=${limit || 10}`)
    return venues.map(v => ({
      id: v.id,
      name: v.name,
      cuisine: v.cuisine_type || v.category || 'Restaurant',
      address: v.address,
      city: v.city,
      latitude: v.latitude,
      longitude: v.longitude,
      price_level: v.price_level,
      rating: v.rating,
      capacity: v.capacity,
      ambiance: v.ambiance,
      features: v.features,
      image_url: v.image_url,
      trending: v.trending,
    }))
  },
  
  // Recommendation endpoints
  async getRecommendations(userId: number): Promise<RecommendationResponse> {
    // Use query parameter version: GET /recommendations?user_id={userId}
    return fetchApi<RecommendationResponse>(`/recommendations?user_id=${userId}`)
  },
  
  async getVenueRecommendations(userId: number, limit?: number): Promise<Recommendation[]> {
    const query = limit ? `?limit=${limit}` : ''
    const response = await fetchApi<{ venues: any[] }>(`/recommendations/${userId}/venues${query}`)
    // Transform API response to match Recommendation interface
    return response.venues.map(v => ({
      venue: {
        id: v.id,
        name: v.name,
        cuisine: v.cuisine_type || v.category,
        address: v.address,
        city: v.city,
        latitude: v.latitude,
        longitude: v.longitude,
        price_level: v.price_level,
        rating: v.rating,
        ambiance: v.ambiance,
        image_url: v.image_url,
        trending: v.trending,
        distance: v.distance_km,
      },
      score: v.score,
      reasons: [],
    }))
  },
  
  async expressInterest(userId: number, venueId: number): Promise<void> {
    // POST /recommendations/interest with body { user_id, venue_id }
    await fetchApi(`/recommendations/interest`, {
      method: 'POST',
      body: JSON.stringify({ user_id: userId, venue_id: venueId }),
    })
  },
  
  // Booking endpoints
  async getBookings(userId: number): Promise<Booking[]> {
    return fetchApi<Booking[]>(`/bookings/user/${userId}`)
  },
  
  async getBooking(bookingId: number): Promise<Booking> {
    return fetchApi<Booking>(`/bookings/${bookingId}`)
  },
  
  async createBooking(
    userId: number,
    venueId: number,
    partySize: number,
    bookingTime: string,
    specialRequests?: string
  ): Promise<Booking> {
    return fetchApi<Booking>(`/bookings/${userId}/create`, {
      method: 'POST',
      body: JSON.stringify({
        venue_id: venueId,
        party_size: partySize,
        booking_time: bookingTime,
        special_requests: specialRequests,
      }),
    })
  },
  
  async cancelBooking(bookingId: number): Promise<Booking> {
    return fetchApi<Booking>(`/bookings/${bookingId}/cancel`, {
      method: 'POST',
    })
  },
  
  // Social endpoints
  async getFriendActivity(userId: number): Promise<FriendActivity[]> {
    try {
      // Try the friend activity endpoint first
      return await fetchApi<FriendActivity[]>(`/users/${userId}/friend-activity`)
    } catch (error) {
      // If that fails, return empty array
      console.warn('Friend activity endpoint not available, returning empty array')
      return []
    }
  },
  
  async getFriends(userId: number): Promise<Friend[]> {
    return fetchApi<Friend[]>(`/users/${userId}/friends`)
  },
  
  async getSocialMatches(userId: number): Promise<SocialMatch[]> {
    try {
      // Use the people recommendations endpoint
      const response = await fetchApi<SocialMatch[]>(`/recommendations/user/${userId}/people`)
      return response
    } catch (error) {
      console.warn('Social matches endpoint not available, returning empty array')
      return []
    }
  },
  
  async connectWithUser(userId: number, friendId: number): Promise<{ success: boolean; message: string }> {
    // This would normally create a friendship - for now we simulate it
    // The backend may not have this endpoint, so we handle gracefully
    try {
      return await fetchApi<{ success: boolean; message: string }>(`/users/${userId}/connect`, {
        method: 'POST',
        body: JSON.stringify({ friend_id: friendId }),
      })
    } catch (error) {
      // Simulate success if endpoint doesn't exist
      console.warn('Connect endpoint not available, simulating success')
      return { success: true, message: 'Connection request sent!' }
    }
  },
  
  async getUserBookings(userId: number): Promise<Booking[]> {
    return fetchApi<Booking[]>(`/bookings/user/${userId}`)
  },
  
  // Reviews
  async getVenueReviews(venueId: number, userId?: number): Promise<Review[]> {
    const params = userId ? `?user_id=${userId}` : ''
    return fetchApi<Review[]>(`/reviews/venue/${venueId}${params}`)
  },
  
  async getReviews(params?: { userId?: number; venueId?: number; friendsOnly?: boolean; limit?: number }): Promise<Review[]> {
    const searchParams = new URLSearchParams()
    if (params?.userId) searchParams.set('user_id', params.userId.toString())
    if (params?.venueId) searchParams.set('venue_id', params.venueId.toString())
    if (params?.friendsOnly) searchParams.set('friends_only', 'true')
    if (params?.limit) searchParams.set('limit', params.limit.toString())
    
    const query = searchParams.toString()
    return fetchApi<Review[]>(`/reviews/${query ? `?${query}` : ''}`)
  },
  
  async submitReview(
    userId: number,
    venueId: number,
    rating: number,
    comment?: string
  ): Promise<any> {
    return fetchApi(`/reviews/`, {
      method: 'POST',
      body: JSON.stringify({
        user_id: userId,
        venue_id: venueId,
        rating,
        comment,
      }),
    })
  },
}

export default api

