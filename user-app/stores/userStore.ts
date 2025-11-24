import { create } from 'zustand'
import { User, Recommendation, Booking, FriendActivity } from '@/lib/api-client'

interface UserState {
  currentUser: User | null
  recommendations: Recommendation[]
  bookings: Booking[]
  friendActivity: FriendActivity[]
  selectedVenueId: number | null
  isLoading: boolean
  
  setCurrentUser: (user: User) => void
  setRecommendations: (recommendations: Recommendation[]) => void
  setBookings: (bookings: Booking[]) => void
  setFriendActivity: (activity: FriendActivity[]) => void
  setSelectedVenue: (venueId: number | null) => void
  setLoading: (loading: boolean) => void
  addBooking: (booking: Booking) => void
  updateBooking: (bookingId: number, updates: Partial<Booking>) => void
}

export const useUserStore = create<UserState>((set) => ({
  currentUser: null,
  recommendations: [],
  bookings: [],
  friendActivity: [],
  selectedVenueId: null,
  isLoading: false,

  setCurrentUser: (user) => set({ currentUser: user }),
  setRecommendations: (recommendations) => set({ recommendations }),
  setBookings: (bookings) => set({ bookings }),
  setFriendActivity: (activity) => set({ friendActivity: activity }),
  setSelectedVenue: (venueId) => set({ selectedVenueId: venueId }),
  setLoading: (loading) => set({ isLoading: loading }),
  
  addBooking: (booking) => set((state) => ({
    bookings: [...state.bookings, booking]
  })),
  
  updateBooking: (bookingId, updates) => set((state) => ({
    bookings: state.bookings.map(b => 
      b.id === bookingId ? { ...b, ...updates } : b
    )
  })),
}))

