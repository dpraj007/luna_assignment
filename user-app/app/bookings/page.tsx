'use client'

import { useEffect, useState } from 'react'
import { Calendar, Clock, MapPin, Users, CheckCircle, AlertCircle } from 'lucide-react'
import { Booking } from '@/lib/api-client'
import { api } from '@/lib/api-client'
import { useUserStore } from '@/stores/userStore'
import { formatDate, formatTime, getTimeUntil } from '@/lib/utils'
import { Navigation } from '@/components/shared/Navigation'

const DEFAULT_USER_ID = 1

export default function BookingsPage() {
  const { bookings, setBookings } = useUserStore()
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    loadBookings()
  }, [])

  const loadBookings = async () => {
    try {
      const userBookings = await api.getUserBookings(DEFAULT_USER_ID)
      setBookings(userBookings)
    } catch (error) {
      console.error('Failed to load bookings:', error)
    } finally {
      setLoading(false)
    }
  }

  // Expose loadBookings to BookingCard via props
  const handleBookingUpdate = () => {
    loadBookings()
  }

  const upcomingBookings = bookings.filter(
    b => (b.status === 'confirmed' || b.status === 'pending') && new Date(b.booking_time) > new Date()
  ).sort((a, b) => new Date(a.booking_time).getTime() - new Date(b.booking_time).getTime())

  const pastBookings = bookings.filter(
    b => b.status === 'completed' || new Date(b.booking_time) < new Date()
  ).sort((a, b) => new Date(b.booking_time).getTime() - new Date(a.booking_time).getTime())

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="w-16 h-16 border-4 border-purple-600 border-t-transparent rounded-full animate-spin" />
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-purple-50 to-orange-50">
      <div className="container mx-auto px-4 py-6 max-w-4xl">
        <h1 className="text-3xl font-bold text-gray-900 mb-6">My Bookings</h1>

        {/* Upcoming Bookings */}
        {upcomingBookings.length > 0 && (
          <section className="mb-8">
            <h2 className="text-xl font-semibold text-gray-900 mb-4">Upcoming</h2>
            <div className="space-y-4">
              {upcomingBookings.map((booking) => (
                <BookingCard key={booking.id} booking={booking} onBookingUpdate={handleBookingUpdate} />
              ))}
            </div>
          </section>
        )}

        {/* Past Bookings */}
        {pastBookings.length > 0 && (
          <section>
            <h2 className="text-xl font-semibold text-gray-900 mb-4">Past</h2>
            <div className="space-y-4">
              {pastBookings.map((booking) => (
                <BookingCard key={booking.id} booking={booking} past onBookingUpdate={handleBookingUpdate} />
              ))}
            </div>
          </section>
        )}

        {bookings.length === 0 && (
          <div className="bg-white rounded-xl p-12 text-center">
            <Calendar className="w-16 h-16 text-gray-400 mx-auto mb-4" />
            <p className="text-gray-500 mb-4">No bookings yet</p>
            <button className="btn-primary">Browse Venues</button>
          </div>
        )}
      </div>
      <Navigation />
    </div>
  )
}

function BookingCard({ booking, past = false, onBookingUpdate }: { booking: Booking; past?: boolean; onBookingUpdate?: () => void }) {
  const [cancelling, setCancelling] = useState(false)
  const [showConfirm, setShowConfirm] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const statusColors = {
    confirmed: 'bg-green-100 text-green-700',
    pending: 'bg-yellow-100 text-yellow-700',
    cancelled: 'bg-red-100 text-red-700',
    completed: 'bg-gray-100 text-gray-700',
  }

  const handleCancel = async () => {
    setCancelling(true)
    setError(null)
    try {
      await api.cancelBooking(booking.id)
      // Refresh bookings list
      if (onBookingUpdate) {
        onBookingUpdate()
      }
      setShowConfirm(false)
    } catch (err: any) {
      console.error('Failed to cancel booking:', err)
      setError(err.message || 'Failed to cancel booking. Please try again.')
    } finally {
      setCancelling(false)
    }
  }

  return (
    <div className="card p-6">
      <div className="flex items-start justify-between mb-4">
        <div className="flex-1">
          <h3 className="text-xl font-bold text-gray-900 mb-2">
            {booking.venue?.name || 'Venue'}
          </h3>
          <div className="flex items-center gap-4 text-sm text-gray-600">
            <div className="flex items-center gap-1">
              <Calendar className="w-4 h-4" />
              {formatDate(booking.booking_time)}
            </div>
            <div className="flex items-center gap-1">
              <Clock className="w-4 h-4" />
              {formatTime(booking.booking_time)}
            </div>
            <div className="flex items-center gap-1">
              <Users className="w-4 h-4" />
              {booking.party_size} {booking.party_size === 1 ? 'person' : 'people'}
            </div>
          </div>
        </div>
        <div className="flex flex-col items-end gap-2">
          <span className={`badge ${statusColors[booking.status] || statusColors.pending}`}>
            {booking.status}
          </span>
          {!past && booking.status === 'confirmed' && (
            <span className="text-xs text-gray-500">
              {getTimeUntil(booking.booking_time)}
            </span>
          )}
        </div>
      </div>

      {booking.confirmation_code && (
        <div className="bg-purple-50 rounded-lg p-3 mb-4">
          <div className="flex items-center justify-between">
            <span className="text-sm font-semibold text-purple-900">Confirmation Code</span>
            <span className="text-lg font-mono font-bold text-purple-600">
              {booking.confirmation_code}
            </span>
          </div>
        </div>
      )}

      {booking.venue && (
        <div className="flex items-center gap-2 text-sm text-gray-600 mb-4">
          <MapPin className="w-4 h-4" />
          <span>{booking.venue.cuisine}</span>
          <span>•</span>
          <span>{booking.venue.price_level}</span>
        </div>
      )}

      {error && (
        <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg">
          <div className="flex items-center gap-2 text-red-700 text-sm">
            <AlertCircle className="w-4 h-4" />
            <span>{error}</span>
          </div>
        </div>
      )}

      <div className="flex items-center gap-3">
        {booking.status === 'confirmed' && !past && (
          <>
            <button className="btn-secondary text-sm">View Details</button>
            {showConfirm ? (
              <div className="flex items-center gap-2">
                <span className="text-sm text-gray-600">Cancel this booking?</span>
                <button
                  onClick={handleCancel}
                  disabled={cancelling}
                  className="text-sm px-3 py-1 bg-red-600 text-white rounded-lg hover:bg-red-700 font-semibold disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                >
                  {cancelling ? 'Cancelling...' : 'Yes, Cancel'}
                </button>
                <button
                  onClick={() => {
                    setShowConfirm(false)
                    setError(null)
                  }}
                  disabled={cancelling}
                  className="text-sm px-3 py-1 text-gray-600 hover:text-gray-700 font-semibold disabled:opacity-50"
                >
                  No
                </button>
              </div>
            ) : (
              <button
                onClick={() => setShowConfirm(true)}
                disabled={cancelling}
                className="text-sm text-red-600 hover:text-red-700 font-semibold disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
              >
                Cancel
              </button>
            )}
          </>
        )}
        {past && booking.status === 'completed' && (
          <button className="btn-secondary text-sm">Leave Review</button>
        )}
      </div>
    </div>
  )
}

