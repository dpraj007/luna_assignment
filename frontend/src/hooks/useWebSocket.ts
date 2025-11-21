/**
 * WebSocket hook for bidirectional admin control.
 */
import { useState, useEffect, useCallback, useRef } from 'react'

interface WebSocketMessage {
  type: string
  payload?: Record<string, unknown>
  request_id?: string
}

interface WebSocketResponse {
  type: string
  success: boolean
  data?: Record<string, unknown>
  error?: string
  request_id?: string
}

interface UseWebSocketReturn {
  isConnected: boolean
  send: (message: WebSocketMessage) => Promise<WebSocketResponse>
  lastMessage: WebSocketResponse | null
  error: string | null
}

export function useWebSocket(url: string): UseWebSocketReturn {
  const [isConnected, setIsConnected] = useState(false)
  const [lastMessage, setLastMessage] = useState<WebSocketResponse | null>(null)
  const [error, setError] = useState<string | null>(null)

  const wsRef = useRef<WebSocket | null>(null)
  const pendingRequests = useRef<Map<string, (response: WebSocketResponse) => void>>(new Map())

  useEffect(() => {
    const connect = () => {
      try {
        const ws = new WebSocket(url)

        ws.onopen = () => {
          setIsConnected(true)
          setError(null)
          console.log('WebSocket connected')
        }

        ws.onmessage = (event) => {
          try {
            const data: WebSocketResponse = JSON.parse(event.data)
            setLastMessage(data)

            // Resolve pending request if request_id matches
            if (data.request_id && pendingRequests.current.has(data.request_id)) {
              const resolve = pendingRequests.current.get(data.request_id)
              if (resolve) {
                resolve(data)
                pendingRequests.current.delete(data.request_id)
              }
            }
          } catch (e) {
            console.error('Failed to parse WebSocket message:', e)
          }
        }

        ws.onclose = () => {
          setIsConnected(false)
          console.log('WebSocket disconnected')

          // Attempt to reconnect after 3 seconds
          setTimeout(connect, 3000)
        }

        ws.onerror = (e) => {
          setError('WebSocket connection error')
          console.error('WebSocket error:', e)
        }

        wsRef.current = ws
      } catch (e) {
        setError('Failed to create WebSocket connection')
        console.error('WebSocket creation error:', e)
      }
    }

    connect()

    return () => {
      if (wsRef.current) {
        wsRef.current.close()
      }
    }
  }, [url])

  const send = useCallback((message: WebSocketMessage): Promise<WebSocketResponse> => {
    return new Promise((resolve, reject) => {
      if (!wsRef.current || wsRef.current.readyState !== WebSocket.OPEN) {
        reject(new Error('WebSocket not connected'))
        return
      }

      // Generate request ID
      const requestId = `${Date.now()}-${Math.random().toString(36).substr(2, 9)}`
      const messageWithId = { ...message, request_id: requestId }

      // Store pending request
      pendingRequests.current.set(requestId, resolve)

      // Set timeout
      setTimeout(() => {
        if (pendingRequests.current.has(requestId)) {
          pendingRequests.current.delete(requestId)
          reject(new Error('Request timeout'))
        }
      }, 10000)

      // Send message
      wsRef.current.send(JSON.stringify(messageWithId))
    })
  }, [])

  return {
    isConnected,
    send,
    lastMessage,
    error,
  }
}

export default useWebSocket
