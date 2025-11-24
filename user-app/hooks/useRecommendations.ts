import { useEffect, useState } from 'react'
import { api, Recommendation } from '@/lib/api-client'
import { useUserStore } from '@/stores/userStore'

export function useRecommendations(userId: number | null) {
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const { recommendations, setRecommendations } = useUserStore()

  useEffect(() => {
    if (!userId) return

    const fetchRecommendations = async () => {
      setLoading(true)
      setError(null)
      try {
        const data = await api.getRecommendations(userId)
        // Only update if we have valid data
        if (data && Array.isArray(data.venues)) {
          setRecommendations(data.venues)
        }
      } catch (err) {
        const errorMessage = err instanceof Error ? err.message : 'Failed to load recommendations'
        setError(errorMessage)
        console.error('Failed to fetch recommendations:', err)
        // Don't clear existing recommendations on error - keep what we have
      } finally {
        setLoading(false)
      }
    }

    fetchRecommendations()
    
    // Refresh every 30 seconds
    const interval = setInterval(fetchRecommendations, 30000)
    return () => clearInterval(interval)
  }, [userId, setRecommendations])

  return { recommendations, loading, error, refetch: () => {
    if (userId) {
      api.getRecommendations(userId)
        .then(data => {
          if (data && Array.isArray(data.venues)) {
            setRecommendations(data.venues)
          }
        })
        .catch(err => {
          console.error('Failed to refetch recommendations:', err)
          // Don't clear existing recommendations on error
        })
    }
  } }
}

