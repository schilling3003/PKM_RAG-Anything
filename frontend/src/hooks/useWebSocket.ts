import { useEffect, useRef } from 'react'
import { websocketService, type WebSocketEventHandler } from '@/services/websocket'

export function useWebSocket() {
  const isConnectedRef = useRef(false)

  useEffect(() => {
    if (!isConnectedRef.current) {
      websocketService.connect().catch(error => {
        console.error('Failed to connect to WebSocket:', error)
      })
      isConnectedRef.current = true
    }

    return () => {
      if (isConnectedRef.current) {
        websocketService.disconnect()
        isConnectedRef.current = false
      }
    }
  }, [])

  return {
    isConnected: websocketService.isConnected,
    send: websocketService.send.bind(websocketService),
    on: websocketService.on.bind(websocketService),
    off: websocketService.off.bind(websocketService),
  }
}

export function useWebSocketEvent(eventType: string, handler: WebSocketEventHandler) {
  useEffect(() => {
    websocketService.on(eventType, handler)
    
    return () => {
      websocketService.off(eventType, handler)
    }
  }, [eventType, handler])
}