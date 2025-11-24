'use client'

import { useEffect, useState } from 'react'
import { Star, Filter, Users, Search, MapPin, Calendar } from 'lucide-react'
import { Review, Venue } from '@/lib/api-client'
import { api } from '@/lib/api-client'
import { useUserStore } from '@/stores/userStore'
import { formatDate, formatTime } from '@/lib/utils'
import { Navigation } from '@/components/shared/Navigation'
import { useRouter } from 'next/navigation'

const DEFAULT_USER_ID = 1

type FilterType = 'all' | 'friends' | 'venue'

export default function ReviewsPage() {
  const router = useRouter()
  const { currentUser, setSelectedVenue } = useUserStore()
  const [reviews, setReviews] = useState<Review[]>([])
  const [loading, setLoading] = useState(true)
  const [filter, setFilter] = useState<FilterType>('all')
  const [searchQuery, setSearchQuery] = useState('')
  const [selectedVenueId, setSelectedVenueId] = useState<number | null>(null)
  const [venues, setVenues] = useState<Venue[]>([])

  useEffect(() => {
    loadReviews()
    loadVenues()
  }, [filter, selectedVenueId])

  const loadVenues = async () => {
    try {
      const results = await api.searchVenues('')
      setVenues(results)
    } catch (error) {
      console.error('Failed to load venues:', error)
    }
  }

  const loadReviews = async () => {
    setLoading(true)
    try {
      const filters: any = {
        limit: 100
      }

      // Always pass userId to enable is_friend flag detection
      const userId = currentUser?.id || DEFAULT_USER_ID
      filters.userId = userId

      if (filter === 'friends') {
        filters.friendsOnly = true
      }

      if (selectedVenueId) {
        filters.venueId = selectedVenueId
      }

      const reviewsData = await api.getReviews(filters)
      setReviews(reviewsData)
    } catch (error) {
      console.error('Failed to load reviews:', error)
      setReviews([])
    } finally {
      setLoading(false)
    }
  }

  const handleVenueClick = (venueId: number) => {
    setSelectedVenue(venueId)
    router.push('/discover')
  }

  const filteredReviews = reviews.filter(review => {
    if (searchQuery) {
      const query = searchQuery.toLowerCase()
      return (
        review.venue_name.toLowerCase().includes(query) ||
        review.username.toLowerCase().includes(query) ||
        review.review_text?.toLowerCase().includes(query) ||
        review.venue_cuisine?.toLowerCase().includes(query)
      )
    }
    return true
  })

  const friendReviews = filteredReviews.filter(r => r.is_friend)
  const otherReviews = filteredReviews.filter(r => !r.is_friend)

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-purple-50 to-orange-50">
        <div className="w-16 h-16 border-4 border-purple-600 border-t-transparent rounded-full animate-spin" />
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-purple-50 to-orange-50">
      <div className="container mx-auto px-4 py-6 max-w-4xl">
        {/* Header */}
        <div className="mb-6">
          <h1 className="text-3xl font-bold text-gray-900 mb-2">Reviews</h1>
          <p className="text-gray-600">See what people are saying about venues</p>
        </div>

        {/* Filters */}
        <div className="mb-6 space-y-4">
          {/* Filter Tabs */}
          <div className="flex items-center gap-2 flex-wrap">
            <button
              onClick={() => {
                setFilter('all')
                setSelectedVenueId(null)
              }}
              className={`px-4 py-2 rounded-lg font-medium transition-colors ${
                filter === 'all'
                  ? 'bg-purple-600 text-white'
                  : 'bg-white text-gray-700 hover:bg-gray-50'
              }`}
            >
              All Reviews
            </button>
            <button
              onClick={() => {
                setFilter('friends')
                setSelectedVenueId(null)
              }}
              className={`px-4 py-2 rounded-lg font-medium transition-colors flex items-center gap-2 ${
                filter === 'friends'
                  ? 'bg-purple-600 text-white'
                  : 'bg-white text-gray-700 hover:bg-gray-50'
              }`}
            >
              <Users className="w-4 h-4" />
              Friends Only
            </button>
            <button
              onClick={() => setFilter('venue')}
              className={`px-4 py-2 rounded-lg font-medium transition-colors flex items-center gap-2 ${
                filter === 'venue'
                  ? 'bg-purple-600 text-white'
                  : 'bg-white text-gray-700 hover:bg-gray-50'
              }`}
            >
              <MapPin className="w-4 h-4" />
              By Venue
            </button>
          </div>

          {/* Venue Selector (when filter is 'venue') */}
          {filter === 'venue' && (
            <div>
              <select
                value={selectedVenueId || ''}
                onChange={(e) => setSelectedVenueId(e.target.value ? parseInt(e.target.value) : null)}
                className="w-full px-4 py-2 rounded-lg border-2 border-gray-200 focus:border-purple-500 focus:outline-none"
              >
                <option value="">Select a venue...</option>
                {venues.map((venue) => (
                  <option key={venue.id} value={venue.id}>
                    {venue.name} - {venue.cuisine}
                  </option>
                ))}
              </select>
            </div>
          )}

          {/* Search Bar */}
          <div className="relative">
            <Search className="absolute left-4 top-1/2 transform -translate-y-1/2 text-gray-400 w-5 h-5" />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search reviews by venue, user, or content..."
              className="w-full pl-12 pr-4 py-3 rounded-lg border-2 border-gray-200 focus:border-purple-500 focus:outline-none"
            />
          </div>
        </div>

        {/* Reviews List */}
        {filteredReviews.length === 0 ? (
          <div className="bg-white rounded-xl p-12 text-center">
            <Star className="w-16 h-16 text-gray-400 mx-auto mb-4" />
            <p className="text-gray-500 mb-2">
              {searchQuery || selectedVenueId
                ? 'No reviews match your filters'
                : 'No reviews yet'}
            </p>
            {searchQuery && (
              <button
                onClick={() => {
                  setSearchQuery('')
                  setSelectedVenueId(null)
                }}
                className="text-purple-600 hover:text-purple-700 font-medium mt-2"
              >
                Clear filters
              </button>
            )}
          </div>
        ) : (
          <div className="space-y-6">
            {/* Friend Reviews Section */}
            {friendReviews.length > 0 && filter !== 'friends' && (
              <section>
                <div className="flex items-center gap-2 mb-4">
                  <Users className="w-5 h-5 text-purple-600" />
                  <h2 className="text-xl font-semibold text-gray-900">Reviews from Friends</h2>
                  <span className="text-sm text-gray-500">({friendReviews.length})</span>
                </div>
                <div className="space-y-4">
                  {friendReviews.map((review) => (
                    <ReviewCard key={review.id} review={review} onVenueClick={handleVenueClick} />
                  ))}
                </div>
              </section>
            )}

            {/* Other Reviews Section */}
            {otherReviews.length > 0 && (
              <section>
                {friendReviews.length > 0 && filter !== 'friends' && (
                  <div className="flex items-center gap-2 mb-4">
                    <Star className="w-5 h-5 text-gray-600" />
                    <h2 className="text-xl font-semibold text-gray-900">All Reviews</h2>
                    <span className="text-sm text-gray-500">({otherReviews.length})</span>
                  </div>
                )}
                <div className="space-y-4">
                  {otherReviews.map((review) => (
                    <ReviewCard key={review.id} review={review} onVenueClick={handleVenueClick} />
                  ))}
                </div>
              </section>
            )}

            {/* Show all reviews if filter is 'friends' */}
            {filter === 'friends' && friendReviews.length > 0 && (
              <div className="space-y-4">
                {friendReviews.map((review) => (
                  <ReviewCard key={review.id} review={review} onVenueClick={handleVenueClick} />
                ))}
              </div>
            )}
          </div>
        )}
      </div>
      <Navigation />
    </div>
  )
}

function ReviewCard({ review, onVenueClick }: { review: Review; onVenueClick: (venueId: number) => void }) {
  return (
    <div className={`card p-6 ${review.is_friend ? 'border-2 border-purple-200 bg-purple-50/50' : ''}`}>
      <div className="flex items-start gap-4">
        {/* Avatar */}
        <div className="flex-shrink-0">
          {review.avatar_url ? (
            <img
              src={review.avatar_url}
              alt={review.username}
              className="w-12 h-12 rounded-full object-cover"
            />
          ) : (
            <div className="w-12 h-12 rounded-full bg-gradient-to-br from-purple-400 to-orange-400 flex items-center justify-center text-white font-bold text-lg">
              {review.username.charAt(0).toUpperCase()}
            </div>
          )}
        </div>

        {/* Review Content */}
        <div className="flex-1">
          <div className="flex items-center justify-between mb-2">
            <div className="flex items-center gap-2">
              <h3 className="font-semibold text-gray-900">{review.username}</h3>
              {review.is_friend && (
                <span className="text-xs px-2 py-1 bg-purple-100 text-purple-700 rounded-full font-medium">
                  Friend
                </span>
              )}
            </div>
            <span className="text-sm text-gray-500 flex items-center gap-1">
              <Calendar className="w-4 h-4" />
              {formatDate(review.created_at)}
            </span>
          </div>

          {/* Venue Info */}
          <button
            onClick={() => onVenueClick(review.venue_id)}
            className="text-left mb-3 group"
          >
            <h4 className="font-bold text-lg text-gray-900 group-hover:text-purple-600 transition-colors mb-1">
              {review.venue_name}
            </h4>
            <div className="flex items-center gap-2 text-sm text-gray-600">
              {review.venue_cuisine && (
                <>
                  <MapPin className="w-4 h-4" />
                  <span>{review.venue_cuisine}</span>
                </>
              )}
            </div>
          </button>

          {/* Rating */}
          {review.rating && (
            <div className="flex items-center gap-1 mb-3">
              {[1, 2, 3, 4, 5].map((star) => (
                <Star
                  key={star}
                  className={`w-5 h-5 ${
                    star <= Math.round(review.rating!)
                      ? 'fill-yellow-400 text-yellow-400'
                      : 'text-gray-300'
                  }`}
                />
              ))}
              <span className="ml-2 text-sm font-medium text-gray-700">
                {review.rating.toFixed(1)}/5.0
              </span>
            </div>
          )}

          {/* Review Text */}
          {review.review_text && (
            <p className="text-gray-700 leading-relaxed">{review.review_text}</p>
          )}

          {!review.review_text && !review.rating && (
            <p className="text-gray-500 italic">No review text available</p>
          )}
        </div>
      </div>
    </div>
  )
}

