import axios from 'axios'

// Create axios instance with base configuration
export const api = axios.create({
  baseURL: '/api',
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Request interceptor for logging
api.interceptors.request.use(
  (config) => {
    console.log(`API Request: ${config.method?.toUpperCase()} ${config.url}`)
    return config
  },
  (error) => {
    console.error('API Request Error:', error)
    return Promise.reject(error)
  }
)

// Response interceptor for error handling
api.interceptors.response.use(
  (response) => {
    return response
  },
  (error) => {
    console.error('API Response Error:', error)
    
    // Handle common error cases
    if (error.response?.status === 404) {
      console.warn('Resource not found')
    } else if (error.response?.status >= 500) {
      console.error('Server error occurred')
    }
    
    return Promise.reject(error)
  }
)

export default api