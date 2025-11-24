import { useEffect } from 'react'
import { useUserStore } from '@/stores/userStore'
import { Booking, api } from '@/lib/api-client'

const WS_URL = process.env.NEXT_PUBLIC_WS_URL || 'ws://localhost:8000'

export function useRealtimeUpdates(userId: number | null) {
  const { addBooking, updateBooking, setRecommendations } = useUserStore()

  useEffect(() => {
    if (!userId) return

    // Use Server-Sent Events for real-time updates
    const apiBase = process.env.NEXT_PUBLIC_API_URL?.replace('/api/v1', '') || 'http://localhost:8000'
    const eventSource = new EventSource(
      `${apiBase}/api/v1/admin/streams/subscribe/recommendations`
    )

    eventSource.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data)
        
        // Handle recommendation updates
        if (data.channel === 'recommendations' && data.user_id === userId) {
          // Refresh recommendations using API client to ensure proper transformation
          api.getRecommendations(userId)
            .then(result => {
              // Only update if we have valid venues data
              if (result && Array.isArray(result.venues) && result.venues.length > 0) {
                setRecommendations(result.venues)
              }
              // If venues is empty or missing, don't update (keep existing recommendations)
            })
            .catch(err => {
              console.error('Failed to refresh recommendations from realtime update:', err)
              // Don't clear recommendations on error - keep existing ones
            })
        }

        // Handle booking updates
        if (data.channel === 'bookings' && data.user_id === userId) {
          if (data.event_type === 'booking_created') {
            const booking = data.payload as Booking
            addBooking(booking)
          } else if (data.event_type === 'booking_confirmed') {
            updateBooking(data.booking_id, { status: 'confirmed' })
          }
        }
      } catch (err) {
        console.error('Error processing SSE event:', err)
      }
    }

    eventSource.onerror = (error) => {
      // SSE connection error - will auto-reconnect
      // Only log if it's a real error (not just connection refused which is expected if backend is down)
      if (eventSource.readyState === EventSource.CLOSED) {
        console.warn('SSE connection closed. Backend may be unavailable.')
      }
    }

    return () => {
      eventSource.close()
    }
  }, [userId, addBooking, updateBooking, setRecommendations])
}

