'use client'

import { useState } from 'react'
import { Recommendation } from '@/lib/api-client'
import { useUserStore } from '@/stores/userStore'
import { Sparkles, MapPin, DollarSign, TrendingUp, Heart, Share2, Calendar } from 'lucide-react'
import { formatDistance } from '@/lib/utils'
import { motion } from 'framer-motion'
import { BookingModal } from './BookingModal'

interface ForYouFeedProps {
  recommendations: Recommendation[]
  loading?: boolean
  userId?: number
}

export function ForYouFeed({ recommendations, loading, userId = 1 }: ForYouFeedProps) {
  const { setSelectedVenue, currentUser } = useUserStore()
  const [bookingModalOpen, setBookingModalOpen] = useState(false)
  const [selectedVenueForBooking, setSelectedVenueForBooking] = useState<Recommendation | null>(null)
  
  const effectiveUserId = currentUser?.id || userId

  if (loading) {
    return (
      <section className="space-y-6">
        <h2 className="text-2xl font-bold text-gray-900">For You</h2>
        <div className="h-96 bg-gray-200 rounded-2xl animate-pulse" />
      </section>
    )
  }

  if (recommendations.length === 0) {
    return (
      <section className="space-y-6">
        <h2 className="text-2xl font-bold text-gray-900">For You</h2>
        <div className="bg-white rounded-2xl p-12 text-center">
          <p className="text-gray-500">No recommendations yet. Start exploring!</p>
        </div>
      </section>
    )
  }

  const heroRec = recommendations[0]
  const secondaryRecs = recommendations.slice(1, 4)

  return (
    <section className="space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-2xl font-bold text-gray-900">For You</h2>
        <span className="text-sm text-gray-500">Personalized just for you</span>
      </div>

      {/* Hero Recommendation */}
      {heroRec && heroRec.venue && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="relative rounded-2xl overflow-hidden shadow-xl cursor-pointer group"
          onClick={() => setSelectedVenue(heroRec.venue.id)}
        >
          <div className="relative h-64 bg-gradient-to-br from-purple-500 to-orange-500">
            <div className="w-full h-full flex items-center justify-center text-white text-4xl font-bold">
              {heroRec.venue.name.charAt(0)}
            </div>
            <div className="absolute inset-0 bg-gradient-to-t from-black/60 to-transparent" />

            {/* AI Explanation Badge */}
            {heroRec.reasoning && (
              <div className="absolute top-4 left-4 right-4">
                <div className="bg-gradient-to-r from-purple-600/90 to-indigo-600/90 backdrop-blur-sm rounded-lg p-3 text-white">
                  <div className="flex items-start gap-2">
                    <Sparkles className="w-5 h-5 flex-shrink-0 mt-0.5" />
                    <p className="text-sm font-medium italic">{heroRec.reasoning}</p>
                  </div>
                </div>
              </div>
            )}

            {/* Match Score */}
            <div className="absolute top-4 right-4">
              <div className="bg-white/90 backdrop-blur-sm rounded-full px-4 py-2">
                <div className="flex items-center gap-1">
                  <TrendingUp className="w-4 h-4 text-purple-600" />
                  <span className="text-lg font-bold text-purple-600">{heroRec.match_score}%</span>
                  <span className="text-xs text-gray-600">match</span>
                </div>
              </div>
            </div>

            {/* Venue Info */}
            <div className="absolute bottom-0 left-0 right-0 p-6 text-white">
              <h3 className="text-2xl font-bold mb-2">{heroRec.venue.name}</h3>
              <div className="flex items-center gap-4 text-sm">
                <div className="flex items-center gap-1">
                  <span className="font-semibold">{heroRec.venue.cuisine}</span>
                </div>
                {heroRec.venue.distance && (
                  <div className="flex items-center gap-1">
                    <MapPin className="w-4 h-4" />
                    <span>{formatDistance(heroRec.venue.distance)}</span>
                  </div>
                )}
                <div className="flex items-center gap-1">
                  <DollarSign className="w-4 h-4" />
                  <span>{heroRec.venue.price_level}</span>
                </div>
              </div>

              {/* Quick Actions */}
              <div className="flex items-center gap-3 mt-4" onClick={(e) => e.stopPropagation()}>
                <button
                  onClick={(e) => {
                    e.stopPropagation()
                    setSelectedVenueForBooking(heroRec)
                    setBookingModalOpen(true)
                  }}
                  className="btn-primary flex items-center gap-2 text-sm"
                >
                  <Calendar className="w-4 h-4" />
                  Book Now
                </button>
                <button
                  onClick={(e) => {
                    e.stopPropagation()
                    setSelectedVenue(heroRec.venue.id)
                  }}
                  className="bg-white/20 backdrop-blur-sm hover:bg-white/30 text-white px-4 py-2 rounded-lg transition-colors"
                >
                  <Heart className="w-4 h-4" />
                </button>
                <button
                  onClick={(e) => {
                    e.stopPropagation()
                    setSelectedVenue(heroRec.venue.id)
                  }}
                  className="bg-white/20 backdrop-blur-sm hover:bg-white/30 text-white px-4 py-2 rounded-lg transition-colors"
                >
                  <Share2 className="w-4 h-4" />
                </button>
              </div>
            </div>
          </div>
        </motion.div>
      )}

      {/* Secondary Recommendations */}
      {secondaryRecs.length > 0 && (
        <div>
          <h3 className="text-lg font-semibold text-gray-900 mb-4">More Recommendations</h3>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {secondaryRecs.map((rec) => (
              rec.venue ? (
                <motion.div
                  key={rec.venue.id}
                  initial={{ opacity: 0, scale: 0.95 }}
                  animate={{ opacity: 1, scale: 1 }}
                  className="card overflow-hidden cursor-pointer group"
                  onClick={() => setSelectedVenue(rec.venue.id)}
                >
                  <div className="relative h-32 bg-gradient-to-br from-purple-400 to-orange-400">
                    <div className="w-full h-full flex items-center justify-center text-white text-2xl font-bold">
                      {rec.venue.name.charAt(0)}
                    </div>
                    {rec.venue.trending && (
                      <div className="absolute top-2 right-2 badge-trending">
                        🔥 Trending
                      </div>
                    )}
                    <div className="absolute bottom-2 right-2 bg-white/90 backdrop-blur-sm rounded-full px-2 py-1">
                      <span className="text-xs font-bold text-purple-600">{rec.match_score}%</span>
                    </div>
                  </div>
                  <div className="p-4">
                    <h4 className="font-semibold text-gray-900 mb-1">{rec.venue.name}</h4>
                    <p className="text-sm text-gray-600 mb-2">{rec.venue.cuisine}</p>
                    <div className="flex items-center justify-between text-xs text-gray-500">
                      {rec.venue.distance && (
                        <span className="flex items-center gap-1">
                          <MapPin className="w-3 h-3" />
                          {formatDistance(rec.venue.distance)}
                        </span>
                      )}
                      <span>{rec.venue.price_level}</span>
                    </div>
                  </div>
                </motion.div>
              ) : null
            ))}
          </div>
        </div>
      )}

      {/* Booking Modal */}
      {selectedVenueForBooking?.venue && (
        <BookingModal
          venue={selectedVenueForBooking.venue}
          isOpen={bookingModalOpen}
          onClose={() => {
            setBookingModalOpen(false)
            setSelectedVenueForBooking(null)
          }}
          userId={effectiveUserId}
        />
      )}
    </section>
  )
}

