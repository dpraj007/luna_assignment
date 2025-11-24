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
import { api } from '@/lib/api-client'

// Demo: Default user ID (in real app, this would come from auth)
const DEFAULT_USER_ID = 1

export default function HomePage() {
  const { currentUser, setCurrentUser, friendActivity, setFriendActivity, bookings } = useUserStore()
  const [loading, setLoading] = useState(true)
  
  const { recommendations, loading: recLoading } = useRecommendations(
    currentUser?.id || DEFAULT_USER_ID
  )

  // Enable real-time updates
  useRealtimeUpdates(currentUser?.id || DEFAULT_USER_ID)

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
      <Navigation />
    </div>
  )
}

