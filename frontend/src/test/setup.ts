import '@testing-library/jest-dom'
import { vi } from 'vitest'

// Mock WebSocket for tests
global.WebSocket = class MockWebSocket {
  constructor() {
    // Mock implementation
  }
  
  close() {}
  send() {}
  
  // Mock properties
  readyState = 1 // OPEN
  onopen = null
  onclose = null
  onmessage = null
  onerror = null
} as any

// Mock ResizeObserver
global.ResizeObserver = class ResizeObserver {
  observe() {}
  unobserve() {}
  disconnect() {}
}

// Mock IntersectionObserver
global.IntersectionObserver = class IntersectionObserver {
  constructor() {}
  observe() {}
  unobserve() {}
  disconnect() {}
} as any

// Mock matchMedia
Object.defineProperty(window, 'matchMedia', {
  writable: true,
  value: vi.fn().mockImplementation((query: string) => ({
    matches: false,
    media: query,
    onchange: null,
    addListener: vi.fn(), // deprecated
    removeListener: vi.fn(), // deprecated
    addEventListener: vi.fn(),
    removeEventListener: vi.fn(),
    dispatchEvent: vi.fn(),
  })),
})