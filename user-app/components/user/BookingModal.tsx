'use client'

import { useState } from 'react'
import { X, Calendar, Users, Clock, MapPin, AlertCircle, CheckCircle } from 'lucide-react'
import { Venue, api } from '@/lib/api-client'
import { useUserStore } from '@/stores/userStore'

interface BookingModalProps {
  venue: Venue
  isOpen: boolean
  onClose: () => void
  userId: number
}

export function BookingModal({ venue, isOpen, onClose, userId }: BookingModalProps) {
  const { addBooking, currentUser } = useUserStore()
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [success, setSuccess] = useState(false)
  const [confirmationCode, setConfirmationCode] = useState<string | null>(null)
  
  const [formData, setFormData] = useState({
    party_size: 2,
    booking_time: '',
    special_requests: ''
  })

  if (!isOpen) return null

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true)
    setError(null)
    setSuccess(false)

    try {
      const result = await api.createBooking({
        user_id: userId,
        venue_id: venue.id,
        party_size: formData.party_size,
        booking_time: formData.booking_time || undefined,
        special_requests: formData.special_requests || undefined
      })

      if (result.success) {
        setSuccess(true)
        setConfirmationCode(result.confirmation_code || null)
        
        // Refresh bookings list
        try {
          const bookings = await api.getUserBookings(userId)
          useUserStore.getState().setBookings(bookings)
        } catch (err) {
          console.error('Failed to refresh bookings:', err)
        }
        
        // Close modal after 2 seconds
        setTimeout(() => {
          onClose()
          setSuccess(false)
          setFormData({ party_size: 2, booking_time: '', special_requests: '' })
        }, 2000)
      } else {
        setError(result.errors?.join(', ') || 'Booking failed')
      }
    } catch (err: any) {
      setError(err.message || 'Failed to create booking. Please try again.')
    } finally {
      setLoading(false)
    }
  }

  const handleClose = () => {
    if (!loading) {
      onClose()
      setError(null)
      setSuccess(false)
      setFormData({ party_size: 2, booking_time: '', special_requests: '' })
    }
  }

  // Calculate default booking time (next meal time)
  const getDefaultBookingTime = () => {
    const now = new Date()
    const hour = now.getHours()
    let defaultTime = new Date()
    
    if (hour < 11) {
      // Morning - schedule for lunch
      defaultTime.setHours(12, 0, 0, 0)
    } else if (hour < 17) {
      // Afternoon - schedule for dinner
      defaultTime.setHours(19, 0, 0, 0)
    } else {
      // Evening - schedule for next day lunch
      defaultTime.setDate(defaultTime.getDate() + 1)
      defaultTime.setHours(12, 0, 0, 0)
    }
    
    return defaultTime.toISOString().slice(0, 16) // Format for datetime-local input
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50 backdrop-blur-sm">
      <div className="bg-white rounded-2xl shadow-2xl max-w-md w-full max-h-[90vh] overflow-y-auto">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b">
          <h2 className="text-2xl font-bold text-gray-900">Book Table</h2>
          <button
            onClick={handleClose}
            disabled={loading}
            className="p-2 hover:bg-gray-100 rounded-lg transition-colors disabled:opacity-50"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Venue Info */}
        <div className="p-6 border-b bg-gradient-to-r from-purple-50 to-orange-50">
          <h3 className="text-xl font-bold text-gray-900 mb-2">{venue.name}</h3>
          <div className="flex flex-wrap gap-3 text-sm text-gray-600">
            <span className="flex items-center gap-1">
              <MapPin className="w-4 h-4" />
              {venue.cuisine}
            </span>
            {venue.distance && (
              <span>{venue.distance.toFixed(1)} km away</span>
            )}
            <span>{venue.price_level}</span>
          </div>
        </div>

        {/* Success Message */}
        {success && (
          <div className="p-6">
            <div className="bg-green-50 border border-green-200 rounded-lg p-4 flex items-start gap-3">
              <CheckCircle className="w-5 h-5 text-green-600 flex-shrink-0 mt-0.5" />
              <div className="flex-1">
                <h4 className="font-semibold text-green-900 mb-1">Booking Confirmed!</h4>
                <p className="text-sm text-green-700">
                  Your table has been reserved.
                  {confirmationCode && (
                    <span className="block mt-1 font-mono font-bold">{confirmationCode}</span>
                  )}
                </p>
              </div>
            </div>
          </div>
        )}

        {/* Error Message */}
        {error && (
          <div className="p-6 pt-0">
            <div className="bg-red-50 border border-red-200 rounded-lg p-4 flex items-start gap-3">
              <AlertCircle className="w-5 h-5 text-red-600 flex-shrink-0 mt-0.5" />
              <div className="flex-1">
                <p className="text-sm text-red-700">{error}</p>
              </div>
            </div>
          </div>
        )}

        {/* Form */}
        {!success && (
          <form onSubmit={handleSubmit} className="p-6 space-y-4">
            {/* Party Size */}
            <div>
              <label htmlFor="party_size" className="block text-sm font-medium text-gray-700 mb-2">
                <Users className="w-4 h-4 inline mr-1" />
                Party Size
              </label>
              <select
                id="party_size"
                value={formData.party_size}
                onChange={(e) => setFormData({ ...formData, party_size: parseInt(e.target.value) })}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                required
                disabled={loading}
              >
                {[1, 2, 3, 4, 5, 6, 7, 8].map(size => (
                  <option key={size} value={size}>
                    {size} {size === 1 ? 'person' : 'people'}
                  </option>
                ))}
              </select>
            </div>

            {/* Booking Time */}
            <div>
              <label htmlFor="booking_time" className="block text-sm font-medium text-gray-700 mb-2">
                <Clock className="w-4 h-4 inline mr-1" />
                Preferred Time
              </label>
              <input
                type="datetime-local"
                id="booking_time"
                value={formData.booking_time || getDefaultBookingTime()}
                onChange={(e) => setFormData({ ...formData, booking_time: e.target.value })}
                min={new Date().toISOString().slice(0, 16)}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                disabled={loading}
              />
              <p className="mt-1 text-xs text-gray-500">
                Leave empty to let us choose the best time for you
              </p>
            </div>

            {/* Special Requests */}
            <div>
              <label htmlFor="special_requests" className="block text-sm font-medium text-gray-700 mb-2">
                Special Requests (Optional)
              </label>
              <textarea
                id="special_requests"
                value={formData.special_requests}
                onChange={(e) => setFormData({ ...formData, special_requests: e.target.value })}
                rows={3}
                placeholder="Dietary restrictions, seating preferences, etc."
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent resize-none"
                disabled={loading}
              />
            </div>

            {/* Actions */}
            <div className="flex gap-3 pt-4">
              <button
                type="button"
                onClick={handleClose}
                disabled={loading}
                className="flex-1 px-4 py-2 border border-gray-300 rounded-lg text-gray-700 hover:bg-gray-50 transition-colors disabled:opacity-50"
              >
                Cancel
              </button>
              <button
                type="submit"
                disabled={loading}
                className="flex-1 px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition-colors disabled:opacity-50 flex items-center justify-center gap-2"
              >
                {loading ? (
                  <>
                    <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                    Booking...
                  </>
                ) : (
                  <>
                    <Calendar className="w-4 h-4" />
                    Confirm Booking
                  </>
                )}
              </button>
            </div>
          </form>
        )}
      </div>
    </div>
  )
}

