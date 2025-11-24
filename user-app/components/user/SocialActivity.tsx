'use client'

import { useRouter } from 'next/navigation'
import { FriendActivity } from '@/lib/api-client'
import { Users, Calendar, Heart, MapPin } from 'lucide-react'
import { formatTime, formatDate } from '@/lib/utils'
import { useUserStore } from '@/stores/userStore'

interface SocialActivityProps {
  activities: FriendActivity[]
  loading?: boolean
}

export function SocialActivity({ activities, loading }: SocialActivityProps) {
  const router = useRouter()
  const { setSelectedVenue } = useUserStore()

  const handleViewVenue = (venueId: number) => {
    setSelectedVenue(venueId)
    router.push('/discover')
  }
  if (loading) {
    return (
      <section className="space-y-4">
        <h2 className="text-xl font-bold text-gray-900">Your Friends Are Dining</h2>
        <div className="space-y-3">
          {[1, 2, 3].map(i => (
            <div key={i} className="h-16 bg-gray-200 rounded-lg animate-pulse" />
          ))}
        </div>
      </section>
    )
  }

  if (activities.length === 0) {
    return (
      <section className="space-y-4">
        <h2 className="text-xl font-bold text-gray-900">Your Friends Are Dining</h2>
        <div className="bg-white rounded-xl p-8 text-center">
          <Users className="w-12 h-12 text-gray-400 mx-auto mb-3" />
          <p className="text-gray-500">No friend activity yet</p>
        </div>
      </section>
    )
  }

  const getActivityIcon = (type: string) => {
    switch (type) {
      case 'booking':
        return <Calendar className="w-4 h-4 text-blue-600" />
      case 'review':
        return <Heart className="w-4 h-4 text-red-600" />
      case 'interest':
        return <MapPin className="w-4 h-4 text-purple-600" />
      default:
        return <Users className="w-4 h-4 text-gray-600" />
    }
  }

  const getActivityText = (activity: FriendActivity) => {
    switch (activity.activity_type) {
      case 'booking':
        return `just booked ${activity.venue?.name || 'a venue'}`
      case 'review':
        return `loved ${activity.venue?.name || 'a venue'}`
      case 'interest':
        return `is interested in ${activity.venue?.name || 'a venue'}`
      default:
        return 'has new activity'
    }
  }

  return (
    <section className="space-y-4">
      <h2 className="text-xl font-bold text-gray-900">Your Friends Are Dining</h2>
      <div className="space-y-3">
        {activities.slice(0, 5).map((activity) => (
          <div
            key={`${activity.user_id}-${activity.timestamp}`}
            className="bg-white rounded-xl p-4 flex items-center gap-4 hover:shadow-md transition-shadow cursor-pointer"
          >
            <div className="w-10 h-10 rounded-full bg-gradient-to-br from-purple-500 to-orange-500 flex items-center justify-center text-white font-semibold flex-shrink-0">
              {activity.user.username.charAt(0).toUpperCase()}
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-sm text-gray-900">
                <span className="font-semibold">{activity.user.username}</span>{' '}
                {getActivityText(activity)}
              </p>
              <p className="text-xs text-gray-500 mt-1">
                {formatDate(activity.timestamp)} at {formatTime(activity.timestamp)}
              </p>
            </div>
            <div className="flex-shrink-0">
              {getActivityIcon(activity.activity_type)}
            </div>
            {activity.venue && (
              <button 
                onClick={() => handleViewVenue(activity.venue!.id)}
                className="text-sm text-purple-600 font-semibold hover:text-purple-700"
              >
                View
              </button>
            )}
          </div>
        ))}
      </div>
    </section>
  )
}

