'use client'

import { useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'
import { Users, UserPlus, Activity, Sparkles, Calendar, Heart, MapPin, TrendingUp } from 'lucide-react'
import { Navigation } from '@/components/shared/Navigation'
import { api, Friend, SocialMatch, FriendActivity } from '@/lib/api-client'
import { useUserStore } from '@/stores/userStore'
import { formatTime, formatDate } from '@/lib/utils'

const DEFAULT_USER_ID = 1

type TabType = 'friends' | 'matches' | 'activity'

export default function SocialPage() {
  const router = useRouter()
  const { currentUser, setSelectedVenue } = useUserStore()
  const [activeTab, setActiveTab] = useState<TabType>('friends')
  const [friends, setFriends] = useState<Friend[]>([])
  const [socialMatches, setSocialMatches] = useState<SocialMatch[]>([])
  const [friendActivity, setFriendActivity] = useState<FriendActivity[]>([])
  const [loading, setLoading] = useState(true)
  const [connecting, setConnecting] = useState<number | null>(null)

  useEffect(() => {
    loadSocialData()
  }, [])

  const loadSocialData = async () => {
    setLoading(true)
    try {
      // Use Promise.allSettled to handle partial failures gracefully
      const results = await Promise.allSettled([
        api.getFriends(DEFAULT_USER_ID),
        api.getSocialMatches(DEFAULT_USER_ID),
        api.getFriendActivity(DEFAULT_USER_ID)
      ])
      
      // Process results, using empty arrays for failed requests
      if (results[0].status === 'fulfilled') {
        setFriends(results[0].value)
      } else {
        console.error('Failed to load friends:', results[0].reason)
        setFriends([])
      }
      
      if (results[1].status === 'fulfilled') {
        setSocialMatches(results[1].value)
      } else {
        console.error('Failed to load social matches:', results[1].reason)
        setSocialMatches([])
      }
      
      if (results[2].status === 'fulfilled') {
        setFriendActivity(results[2].value)
      } else {
        console.error('Failed to load friend activity:', results[2].reason)
        setFriendActivity([])
      }
    } catch (error) {
      console.error('Failed to load social data:', error)
      // Set empty arrays on error to prevent blocking
      setFriends([])
      setSocialMatches([])
      setFriendActivity([])
    } finally {
      setLoading(false)
    }
  }

  const handleConnect = async (friendId: number) => {
    if (connecting === friendId) return
    
    setConnecting(friendId)
    try {
      const result = await api.connectWithUser(DEFAULT_USER_ID, friendId)
      alert(result.message || 'Successfully connected!')
      // Reload friends list
      const friendsData = await api.getFriends(DEFAULT_USER_ID)
      setFriends(friendsData)
      // Remove from matches if it was there
      setSocialMatches(prev => prev.filter(m => m.user.id !== friendId))
    } catch (error: any) {
      alert(error.message || 'Failed to connect. Please try again.')
    } finally {
      setConnecting(null)
    }
  }

  const handleViewProfile = (userId: number, username: string) => {
    router.push(`/user/${userId}`)
  }

  const handleViewVenue = (venueId: number) => {
    setSelectedVenue(venueId)
    router.push('/discover')
  }

  const getActivityIcon = (type: string) => {
    switch (type) {
      case 'booking':
        return <Calendar className="w-5 h-5 text-blue-600" />
      case 'review':
        return <Heart className="w-5 h-5 text-red-600" />
      case 'interest':
        return <MapPin className="w-5 h-5 text-purple-600" />
      default:
        return <Activity className="w-5 h-5 text-gray-600" />
    }
  }

  const getActivityText = (activity: FriendActivity) => {
    switch (activity.activity_type) {
      case 'booking':
        return `booked ${activity.venue?.name || 'a venue'}`
      case 'review':
        return `loved ${activity.venue?.name || 'a venue'}`
      case 'interest':
        return `is interested in ${activity.venue?.name || 'a venue'}`
      default:
        return 'has new activity'
    }
  }

  const getCompatibilityColor = (score: number) => {
    if (score >= 0.8) return 'text-green-600 bg-green-50'
    if (score >= 0.6) return 'text-blue-600 bg-blue-50'
    if (score >= 0.4) return 'text-yellow-600 bg-yellow-50'
    return 'text-gray-600 bg-gray-50'
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-purple-50 to-orange-50 pb-20">
      <div className="container mx-auto px-4 py-6 max-w-6xl">
        {/* Header */}
        <div className="mb-6">
          <h1 className="text-3xl font-bold text-gray-900 mb-2">Social</h1>
          <p className="text-gray-600">Connect with friends and discover dining partners</p>
        </div>

        {/* Tabs */}
        <div className="flex gap-2 mb-6 border-b border-gray-200">
          <button
            onClick={() => setActiveTab('friends')}
            className={`px-6 py-3 font-semibold transition-colors relative ${
              activeTab === 'friends'
                ? 'text-purple-600'
                : 'text-gray-600 hover:text-gray-900'
            }`}
          >
            <div className="flex items-center gap-2">
              <Users className="w-5 h-5" />
              <span>Friends</span>
              {friends.length > 0 && (
                <span className="badge bg-purple-100 text-purple-700 text-xs">
                  {friends.length}
                </span>
              )}
            </div>
            {activeTab === 'friends' && (
              <div className="absolute bottom-0 left-0 right-0 h-0.5 bg-purple-600" />
            )}
          </button>
          <button
            onClick={() => setActiveTab('matches')}
            className={`px-6 py-3 font-semibold transition-colors relative ${
              activeTab === 'matches'
                ? 'text-purple-600'
                : 'text-gray-600 hover:text-gray-900'
            }`}
          >
            <div className="flex items-center gap-2">
              <Sparkles className="w-5 h-5" />
              <span>Matches</span>
              {socialMatches.length > 0 && (
                <span className="badge bg-purple-100 text-purple-700 text-xs">
                  {socialMatches.length}
                </span>
              )}
            </div>
            {activeTab === 'matches' && (
              <div className="absolute bottom-0 left-0 right-0 h-0.5 bg-purple-600" />
            )}
          </button>
          <button
            onClick={() => setActiveTab('activity')}
            className={`px-6 py-3 font-semibold transition-colors relative ${
              activeTab === 'activity'
                ? 'text-purple-600'
                : 'text-gray-600 hover:text-gray-900'
            }`}
          >
            <div className="flex items-center gap-2">
              <Activity className="w-5 h-5" />
              <span>Activity</span>
              {friendActivity.length > 0 && (
                <span className="badge bg-purple-100 text-purple-700 text-xs">
                  {friendActivity.length}
                </span>
              )}
            </div>
            {activeTab === 'activity' && (
              <div className="absolute bottom-0 left-0 right-0 h-0.5 bg-purple-600" />
            )}
          </button>
        </div>

        {/* Content */}
        {loading ? (
          <div className="flex items-center justify-center py-20">
            <div className="text-center">
              <div className="w-16 h-16 border-4 border-purple-600 border-t-transparent rounded-full animate-spin mx-auto mb-4" />
              <p className="text-gray-600">Loading social data...</p>
            </div>
          </div>
        ) : (
          <>
            {/* Friends Tab */}
            {activeTab === 'friends' && (
              <div className="space-y-6">
                {friends.length === 0 ? (
                  <div className="bg-white rounded-xl p-12 text-center">
                    <Users className="w-16 h-16 text-gray-400 mx-auto mb-4" />
                    <p className="text-gray-500 mb-2">No friends yet</p>
                    <p className="text-sm text-gray-400 mb-6">
                      Connect with people who share your dining interests
                    </p>
                    <button className="btn-primary">
                      <UserPlus className="w-4 h-4 mr-2" />
                      Find Friends
                    </button>
                  </div>
                ) : (
                  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                    {friends.map((friend) => (
                      <div
                        key={friend.id}
                        className="card p-6 hover:shadow-lg transition-shadow"
                      >
                        <div className="flex items-start gap-4 mb-4">
                          <div className="w-16 h-16 rounded-full bg-gradient-to-br from-purple-500 to-orange-500 flex items-center justify-center text-white font-bold text-xl flex-shrink-0">
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
                            <h3 className="font-bold text-lg text-gray-900 truncate">
                              {friend.full_name || friend.username}
                            </h3>
                            <p className="text-sm text-gray-500">@{friend.username}</p>
                          </div>
                        </div>
                        <div className="flex items-center justify-between">
                          <div className="flex items-center gap-2">
                            <TrendingUp className="w-4 h-4 text-gray-400" />
                            <span className="text-sm text-gray-600">Compatibility</span>
                          </div>
                          <span
                            className={`badge ${getCompatibilityColor(friend.compatibility_score)}`}
                          >
                            {Math.round(friend.compatibility_score * 100)}%
                          </span>
                        </div>
                        <div className="mt-4 pt-4 border-t border-gray-100">
                          <button 
                            onClick={() => handleViewProfile(friend.id, friend.username)}
                            className="w-full btn-secondary text-sm"
                          >
                            View Profile
                          </button>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            )}

            {/* Matches Tab */}
            {activeTab === 'matches' && (
              <div className="space-y-6">
                <div className="bg-gradient-to-r from-purple-100 to-orange-100 rounded-xl p-6 mb-6">
                  <div className="flex items-center gap-3 mb-2">
                    <Sparkles className="w-6 h-6 text-purple-600" />
                    <h2 className="text-xl font-bold text-gray-900">
                      Discover Dining Partners
                    </h2>
                  </div>
                  <p className="text-gray-600 text-sm">
                    People with similar dining preferences who might be great dining companions
                  </p>
                </div>

                {socialMatches.length === 0 ? (
                  <div className="bg-white rounded-xl p-12 text-center">
                    <Sparkles className="w-16 h-16 text-gray-400 mx-auto mb-4" />
                    <p className="text-gray-500 mb-2">No matches found</p>
                    <p className="text-sm text-gray-400">
                      Check back later for compatible dining partners
                    </p>
                  </div>
                ) : (
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    {socialMatches.map((match) => (
                      <div
                        key={match.user.id}
                        className="card p-6 hover:shadow-lg transition-shadow"
                      >
                        <div className="flex items-start gap-4 mb-4">
                          <div className="w-16 h-16 rounded-full bg-gradient-to-br from-purple-500 to-orange-500 flex items-center justify-center text-white font-bold text-xl flex-shrink-0">
                            {match.user.avatar_url ? (
                              <img
                                src={match.user.avatar_url}
                                alt={match.user.username}
                                className="w-full h-full rounded-full object-cover"
                              />
                            ) : (
                              match.user.username.charAt(0).toUpperCase()
                            )}
                          </div>
                          <div className="flex-1 min-w-0">
                            <h3 className="font-bold text-lg text-gray-900 truncate">
                              {match.user.username}
                            </h3>
                            <p className="text-sm text-gray-500">
                              {match.user.persona || 'Food enthusiast'}
                            </p>
                          </div>
                          <span
                            className={`badge ${getCompatibilityColor(match.compatibility_score)}`}
                          >
                            {Math.round(match.compatibility_score * 100)}%
                          </span>
                        </div>

                        {match.shared_interests.length > 0 && (
                          <div className="mb-4">
                            <p className="text-xs text-gray-500 mb-2">Shared Interests</p>
                            <div className="flex flex-wrap gap-2">
                              {match.shared_interests.slice(0, 3).map((interest, idx) => (
                                <span
                                  key={idx}
                                  className="text-xs px-2 py-1 bg-purple-50 text-purple-700 rounded-full"
                                >
                                  {interest}
                                </span>
                              ))}
                              {match.shared_interests.length > 3 && (
                                <span className="text-xs px-2 py-1 text-gray-500">
                                  +{match.shared_interests.length - 3} more
                                </span>
                              )}
                            </div>
                          </div>
                        )}

                        {match.reasoning && (
                          <p className="text-sm text-gray-600 mb-4 italic">
                            "{match.reasoning}"
                          </p>
                        )}

                        <div className="flex gap-2">
                          <button 
                            onClick={() => handleConnect(match.user.id)}
                            disabled={connecting === match.user.id}
                            className="flex-1 btn-primary text-sm disabled:opacity-50 disabled:cursor-not-allowed"
                          >
                            <UserPlus className="w-4 h-4 mr-2" />
                            {connecting === match.user.id ? 'Connecting...' : 'Connect'}
                          </button>
                          <button 
                            onClick={() => handleViewProfile(match.user.id, match.user.username)}
                            className="btn-secondary text-sm"
                          >
                            View Profile
                          </button>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            )}

            {/* Activity Tab */}
            {activeTab === 'activity' && (
              <div className="space-y-6">
                <div className="bg-gradient-to-r from-blue-100 to-purple-100 rounded-xl p-6 mb-6">
                  <div className="flex items-center gap-3 mb-2">
                    <Activity className="w-6 h-6 text-blue-600" />
                    <h2 className="text-xl font-bold text-gray-900">Friend Activity Feed</h2>
                  </div>
                  <p className="text-gray-600 text-sm">
                    See what your friends are booking, reviewing, and exploring
                  </p>
                </div>

                {friendActivity.length === 0 ? (
                  <div className="bg-white rounded-xl p-12 text-center">
                    <Activity className="w-16 h-16 text-gray-400 mx-auto mb-4" />
                    <p className="text-gray-500 mb-2">No friend activity yet</p>
                    <p className="text-sm text-gray-400">
                      Activity from your friends will appear here
                    </p>
                  </div>
                ) : (
                  <div className="space-y-4">
                    {friendActivity.map((activity, idx) => (
                      <div
                        key={`${activity.user_id}-${activity.timestamp}-${idx}`}
                        className="card p-6 hover:shadow-md transition-shadow"
                      >
                        <div className="flex items-start gap-4">
                          <div className="w-12 h-12 rounded-full bg-gradient-to-br from-purple-500 to-orange-500 flex items-center justify-center text-white font-semibold flex-shrink-0">
                            {activity.user.avatar_url ? (
                              <img
                                src={activity.user.avatar_url}
                                alt={activity.user.username}
                                className="w-full h-full rounded-full object-cover"
                              />
                            ) : (
                              activity.user.username.charAt(0).toUpperCase()
                            )}
                          </div>
                          <div className="flex-1 min-w-0">
                            <div className="flex items-center gap-3 mb-2">
                              <span className="font-semibold text-gray-900">
                                {activity.user.username}
                              </span>
                              <span className="text-gray-600">
                                {getActivityText(activity)}
                              </span>
                              {getActivityIcon(activity.activity_type)}
                            </div>
                            {activity.venue && (
                              <div className="bg-gray-50 rounded-lg p-3 mb-2">
                                <p className="font-semibold text-gray-900">
                                  {activity.venue.name}
                                </p>
                                <p className="text-sm text-gray-600">
                                  {activity.venue.cuisine}
                                </p>
                              </div>
                            )}
                            <p className="text-xs text-gray-500">
                              {formatDate(activity.timestamp)} at {formatTime(activity.timestamp)}
                            </p>
                          </div>
                          {activity.venue && (
                            <button 
                              onClick={() => handleViewVenue(activity.venue!.id)}
                              className="btn-secondary text-sm whitespace-nowrap"
                            >
                              View Venue
                            </button>
                          )}
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            )}
          </>
        )}
      </div>
      <Navigation />
    </div>
  )
}
