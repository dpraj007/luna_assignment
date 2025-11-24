'use client'

import { useEffect, useState } from 'react'
import { UserHeader } from '@/components/user/UserHeader'
import { ForYouFeed } from '@/components/user/ForYouFeed'
import { SocialActivity } from '@/components/user/SocialActivity'
import { QuickActions } from '@/components/user/QuickActions'
import { Navigation } from '@/components/shared/Navigation'
import { useUserStore } from '@/stores/userStore'
import { useRecommendations } from '@/hooks/useRecommendations'
import { useRealtimeUpdates } from '@/hooks/useRealtimeUpdates'
import { api, Venue } from '@/lib/api-client'
import { X, MapPin, DollarSign } from 'lucide-react'
import { formatDistance } from '@/lib/utils'

// Demo: Default user ID (in real app, this would come from auth)
const DEFAULT_USER_ID = 1

export default function HomePage() {
  const { currentUser, setCurrentUser, friendActivity, setFriendActivity, bookings, selectedVenueId, setSelectedVenue } = useUserStore()
  const [loading, setLoading] = useState(true)
  const [selectedVenueDetail, setSelectedVenueDetail] = useState<Venue | null>(null)
  const [loadingVenueDetail, setLoadingVenueDetail] = useState(false)
  
  const { recommendations, loading: recLoading } = useRecommendations(
    currentUser?.id || DEFAULT_USER_ID
  )

  // Enable real-time updates
  useRealtimeUpdates(currentUser?.id || DEFAULT_USER_ID)

  // Check for selectedVenueId and load venue details
  useEffect(() => {
    if (selectedVenueId) {
      loadVenueDetail(selectedVenueId)
    }
  }, [selectedVenueId])

  const loadVenueDetail = async (venueId: number) => {
    setLoadingVenueDetail(true)
    try {
      const venue = await api.getVenue(venueId)
      setSelectedVenueDetail(venue)
    } catch (error) {
      console.error('Failed to load venue details:', error)
      setSelectedVenueDetail(null)
      setSelectedVenue(null) // Clear selection on error
    } finally {
      setLoadingVenueDetail(false)
    }
  }

  const handleCloseVenueDetail = () => {
    setSelectedVenueDetail(null)
    setSelectedVenue(null)
  }

  useEffect(() => {
    const loadUserData = async () => {
      try {
        // Load user
        const user = await api.getMe(DEFAULT_USER_ID)
        setCurrentUser(user)

        // Load friend activity (don't block on this)
        api.getFriendActivity(DEFAULT_USER_ID)
          .then(activity => setFriendActivity(activity))
          .catch(error => {
            console.error('Failed to load friend activity:', error)
            // Set empty array on error to prevent blocking
            setFriendActivity([])
          })
      } catch (error) {
        console.error('Failed to load user data:', error)
        // Set a default user so the page can still render
        setCurrentUser({
          id: DEFAULT_USER_ID,
          username: 'User',
          email: undefined,
          avatar_url: undefined,
          persona: undefined,
          location: undefined
        })
      } finally {
        setLoading(false)
      }
    }

    loadUserData()
  }, [setCurrentUser, setFriendActivity])

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <div className="w-16 h-16 border-4 border-purple-600 border-t-transparent rounded-full animate-spin mx-auto mb-4" />
          <p className="text-gray-600">Loading your personalized feed...</p>
        </div>
      </div>
    )
  }

  // Show page even if currentUser is not set (with fallback)
  const displayUser = currentUser || {
    id: DEFAULT_USER_ID,
    username: 'User',
    email: undefined,
    avatar_url: undefined,
    persona: undefined,
    location: undefined
  }

  const upcomingBookings = bookings.filter(
    b => b.status === 'confirmed' || b.status === 'pending'
  )

  return (
    <div className="min-h-screen">
      <UserHeader 
        user={displayUser}
        friendCount={friendActivity.length}
        upcomingBookingsCount={upcomingBookings.length}
      />
      
      <main className="container mx-auto px-4 py-6 max-w-6xl">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Main Content */}
          <div className="lg:col-span-2 space-y-6">
            <ForYouFeed 
              recommendations={recommendations} 
              loading={recLoading}
              userId={currentUser?.id || DEFAULT_USER_ID}
            />
            <SocialActivity activities={friendActivity} />
          </div>

          {/* Sidebar */}
          <div className="lg:col-span-1">
            <QuickActions />
          </div>
        </div>
      </main>

      {/* Venue Detail Modal */}
      {selectedVenueDetail && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50 backdrop-blur-sm">
          <div className="bg-white rounded-2xl shadow-2xl max-w-2xl w-full max-h-[90vh] overflow-y-auto">
            {loadingVenueDetail ? (
              <div className="p-12 text-center">
                <div className="w-16 h-16 border-4 border-purple-600 border-t-transparent rounded-full animate-spin mx-auto mb-4" />
                <p className="text-gray-600">Loading venue details...</p>
              </div>
            ) : (
              <>
                {/* Header */}
                <div className="flex items-center justify-between p-6 border-b">
                  <h2 className="text-2xl font-bold text-gray-900">Venue Details</h2>
                  <button
                    onClick={handleCloseVenueDetail}
                    className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
                  >
                    <X className="w-5 h-5" />
                  </button>
                </div>

                {/* Venue Info */}
                <div className="p-6">
                  <div className="mb-6">
                    <div className="relative h-64 bg-gradient-to-br from-purple-400 to-orange-400 rounded-xl mb-4">
                      <div className="w-full h-full flex items-center justify-center text-white text-6xl font-bold">
                        {selectedVenueDetail.name.charAt(0)}
                      </div>
                      {selectedVenueDetail.trending && (
                        <div className="absolute top-4 right-4 badge-trending">
                          🔥 Trending
                        </div>
                      )}
                    </div>
                    <h3 className="text-3xl font-bold text-gray-900 mb-2">{selectedVenueDetail.name}</h3>
                    <p className="text-lg text-gray-600 mb-4">{selectedVenueDetail.cuisine}</p>
                    
                    <div className="flex flex-wrap gap-4 text-sm text-gray-600 mb-6">
                      {selectedVenueDetail.rating && (
                        <span className="flex items-center gap-1">
                          ⭐ {selectedVenueDetail.rating.toFixed(1)}
                        </span>
                      )}
                      <span className="flex items-center gap-1">
                        <DollarSign className="w-4 h-4" />
                        {selectedVenueDetail.price_level}
                      </span>
                      {selectedVenueDetail.distance && (
                        <span className="flex items-center gap-1">
                          <MapPin className="w-4 h-4" />
                          {formatDistance(selectedVenueDetail.distance)}
                        </span>
                      )}
                    </div>

                    {selectedVenueDetail.availability && (
                      <div className="bg-gray-50 rounded-lg p-4 mb-6">
                        <p className="font-semibold text-gray-900 mb-1">Availability</p>
                        <p className="text-sm text-gray-600">
                          {selectedVenueDetail.availability.available
                            ? `${selectedVenueDetail.availability.slots_remaining} seats available`
                            : 'Currently full'}
                        </p>
                      </div>
                    )}
                  </div>
                </div>
              </>
            )}
          </div>
        </div>
      )}

      <Navigation />
    </div>
  )
}

