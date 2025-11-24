'use client'

import { useEffect, useState } from 'react'
import { useRouter, useParams } from 'next/navigation'
import { ArrowLeft, MapPin, Calendar, Users, TrendingUp, Heart, Star } from 'lucide-react'
import { Navigation } from '@/components/shared/Navigation'
import { api, User, Friend, Booking } from '@/lib/api-client'
import { formatDate, formatTime } from '@/lib/utils'

interface UserProfile extends User {
  full_name?: string
  city?: string
  activity_score?: number
  social_score?: number
  persona?: string
}

export default function UserProfilePage() {
  const router = useRouter()
  const params = useParams()
  const userId = parseInt(params.id as string)
  
  const [user, setUser] = useState<UserProfile | null>(null)
  const [friends, setFriends] = useState<Friend[]>([])
  const [bookings, setBookings] = useState<Booking[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (userId && !isNaN(userId)) {
      loadUserProfile()
    }
  }, [userId])

  const loadUserProfile = async () => {
    setLoading(true)
    setError(null)
    try {
      // Load user data
      const userData = await api.getMe(userId)
      setUser(userData as UserProfile)

      // Load friends and bookings in parallel
      const [friendsData, bookingsData] = await Promise.allSettled([
        api.getFriends(userId),
        api.getUserBookings(userId)
      ])

      if (friendsData.status === 'fulfilled') {
        setFriends(friendsData.value)
      }

      if (bookingsData.status === 'fulfilled') {
        setBookings(bookingsData.value)
      }
    } catch (err: any) {
      console.error('Failed to load user profile:', err)
      setError(err.message || 'Failed to load user profile')
    } finally {
      setLoading(false)
    }
  }

  const personaColors: Record<string, string> = {
    'Social Butterfly': 'bg-pink-100 text-pink-700',
    'Foodie Explorer': 'bg-orange-100 text-orange-700',
    'Routine Regular': 'bg-blue-100 text-blue-700',
    'Event Organizer': 'bg-purple-100 text-purple-700',
    'Spontaneous Diner': 'bg-green-100 text-green-700',
    'Busy Professional': 'bg-gray-100 text-gray-700',
  }

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-purple-50 to-orange-50">
        <div className="text-center">
          <div className="w-16 h-16 border-4 border-purple-600 border-t-transparent rounded-full animate-spin mx-auto mb-4" />
          <p className="text-gray-600">Loading profile...</p>
        </div>
      </div>
    )
  }

  if (error || !user) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-purple-50 to-orange-50 pb-20">
        <div className="container mx-auto px-4 py-6 max-w-4xl">
          <button
            onClick={() => router.back()}
            className="flex items-center gap-2 text-gray-600 hover:text-gray-900 mb-6"
          >
            <ArrowLeft className="w-5 h-5" />
            <span>Back</span>
          </button>
          <div className="bg-white rounded-xl p-12 text-center">
            <p className="text-red-600 mb-4">{error || 'User not found'}</p>
            <button onClick={() => router.back()} className="btn-primary">
              Go Back
            </button>
          </div>
        </div>
        <Navigation />
      </div>
    )
  }

  const upcomingBookings = bookings.filter(
    b => (b.status === 'confirmed' || b.status === 'pending') && new Date(b.booking_time) > new Date()
  )

  const completedBookings = bookings.filter(
    b => b.status === 'completed' || new Date(b.booking_time) < new Date()
  )

  return (
    <div className="min-h-screen bg-gradient-to-br from-purple-50 to-orange-50 pb-20">
      <div className="container mx-auto px-4 py-6 max-w-4xl">
        {/* Back Button */}
        <button
          onClick={() => router.back()}
          className="flex items-center gap-2 text-gray-600 hover:text-gray-900 mb-6 transition-colors"
        >
          <ArrowLeft className="w-5 h-5" />
          <span>Back</span>
        </button>

        {/* Profile Header */}
        <div className="bg-white rounded-xl p-6 mb-6 shadow-sm">
          <div className="flex items-start gap-6">
            <div className="w-24 h-24 rounded-full bg-gradient-to-br from-purple-500 to-orange-500 flex items-center justify-center text-white font-bold text-3xl flex-shrink-0">
              {user.avatar_url ? (
                <img
                  src={user.avatar_url}
                  alt={user.username}
                  className="w-full h-full rounded-full object-cover"
                />
              ) : (
                user.username.charAt(0).toUpperCase()
              )}
            </div>
            <div className="flex-1 min-w-0">
              <h1 className="text-3xl font-bold text-gray-900 mb-2">
                {user.full_name || user.username}
              </h1>
              <p className="text-gray-500 mb-3">@{user.username}</p>
              
              {user.persona && (
                <span className={`inline-block px-3 py-1 rounded-full text-sm font-semibold mb-3 ${
                  personaColors[user.persona] || 'bg-gray-100 text-gray-700'
                }`}>
                  {user.persona}
                </span>
              )}

              {user.city && (
                <div className="flex items-center gap-2 text-gray-600">
                  <MapPin className="w-4 h-4" />
                  <span>{user.city}</span>
                </div>
              )}
            </div>
          </div>

          {/* Stats */}
          <div className="grid grid-cols-3 gap-4 mt-6 pt-6 border-t border-gray-100">
            <div className="text-center">
              <div className="text-2xl font-bold text-gray-900">{friends.length}</div>
              <div className="text-sm text-gray-500 flex items-center justify-center gap-1 mt-1">
                <Users className="w-4 h-4" />
                <span>Friends</span>
              </div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-gray-900">{bookings.length}</div>
              <div className="text-sm text-gray-500 flex items-center justify-center gap-1 mt-1">
                <Calendar className="w-4 h-4" />
                <span>Bookings</span>
              </div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-gray-900">
                {user.activity_score ? Math.round(user.activity_score * 100) : 'N/A'}
              </div>
              <div className="text-sm text-gray-500 flex items-center justify-center gap-1 mt-1">
                <TrendingUp className="w-4 h-4" />
                <span>Activity</span>
              </div>
            </div>
          </div>
        </div>

        {/* Friends Section */}
        {friends.length > 0 && (
          <div className="bg-white rounded-xl p-6 mb-6 shadow-sm">
            <h2 className="text-xl font-bold text-gray-900 mb-4 flex items-center gap-2">
              <Users className="w-5 h-5" />
              Friends ({friends.length})
            </h2>
            <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
              {friends.slice(0, 6).map((friend) => (
                <div
                  key={friend.id}
                  className="flex items-center gap-3 p-3 rounded-lg hover:bg-gray-50 transition-colors cursor-pointer"
                  onClick={() => router.push(`/user/${friend.id}`)}
                >
                  <div className="w-10 h-10 rounded-full bg-gradient-to-br from-purple-500 to-orange-500 flex items-center justify-center text-white font-semibold flex-shrink-0">
                    {friend.avatar_url ? (
                      <img
                        src={friend.avatar_url}
                        alt={friend.username}
                        className="w-full h-full rounded-full object-cover"
                      />
                    ) : (
                      friend.username.charAt(0).toUpperCase()
                    )}
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="font-semibold text-gray-900 truncate text-sm">
                      {friend.full_name || friend.username}
                    </p>
                    <p className="text-xs text-gray-500">
                      {Math.round(friend.compatibility_score * 100)}% match
                    </p>
                  </div>
                </div>
              ))}
            </div>
            {friends.length > 6 && (
              <button
                onClick={() => router.push('/social?tab=friends')}
                className="mt-4 text-sm text-purple-600 hover:text-purple-700 font-semibold"
              >
                View all friends →
              </button>
            )}
          </div>
        )}

        {/* Bookings Section */}
        {bookings.length > 0 && (
          <div className="bg-white rounded-xl p-6 shadow-sm">
            <h2 className="text-xl font-bold text-gray-900 mb-4 flex items-center gap-2">
              <Calendar className="w-5 h-5" />
              Recent Bookings ({bookings.length})
            </h2>
            
            {upcomingBookings.length > 0 && (
              <div className="mb-6">
                <h3 className="text-sm font-semibold text-gray-700 mb-3">Upcoming</h3>
                <div className="space-y-3">
                  {upcomingBookings.slice(0, 3).map((booking) => (
                    <div
                      key={booking.id}
                      className="flex items-center gap-4 p-3 rounded-lg bg-purple-50 border border-purple-100"
                    >
                      {booking.venue && (
                        <>
                          <div className="flex-1">
                            <p className="font-semibold text-gray-900">{booking.venue.name}</p>
                            <p className="text-sm text-gray-600">{booking.venue.cuisine}</p>
                            <p className="text-xs text-gray-500 mt-1">
                              {formatDate(booking.booking_time)} at {formatTime(booking.booking_time)}
                            </p>
                          </div>
                          <div className="text-right">
                            <span className={`badge ${
                              booking.status === 'confirmed' 
                                ? 'bg-green-100 text-green-700' 
                                : 'bg-yellow-100 text-yellow-700'
                            }`}>
                              {booking.status}
                            </span>
                          </div>
                        </>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            )}

            {completedBookings.length > 0 && (
              <div>
                <h3 className="text-sm font-semibold text-gray-700 mb-3">Past</h3>
                <div className="space-y-3">
                  {completedBookings.slice(0, 3).map((booking) => (
                    <div
                      key={booking.id}
                      className="flex items-center gap-4 p-3 rounded-lg bg-gray-50"
                    >
                      {booking.venue && (
                        <>
                          <div className="flex-1">
                            <p className="font-semibold text-gray-900">{booking.venue.name}</p>
                            <p className="text-sm text-gray-600">{booking.venue.cuisine}</p>
                            <p className="text-xs text-gray-500 mt-1">
                              {formatDate(booking.booking_time)}
                            </p>
                          </div>
                          <div className="text-right">
                            <span className="badge bg-gray-100 text-gray-700">
                              {booking.status}
                            </span>
                          </div>
                        </>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            )}

            {bookings.length > 6 && (
              <button
                onClick={() => router.push('/bookings')}
                className="mt-4 text-sm text-purple-600 hover:text-purple-700 font-semibold"
              >
                View all bookings →
              </button>
            )}
          </div>
        )}

        {/* Empty State */}
        {friends.length === 0 && bookings.length === 0 && (
          <div className="bg-white rounded-xl p-12 text-center shadow-sm">
            <Users className="w-16 h-16 text-gray-400 mx-auto mb-4" />
            <p className="text-gray-500">No additional information available</p>
          </div>
        )}
      </div>
      <Navigation />
    </div>
  )
}

