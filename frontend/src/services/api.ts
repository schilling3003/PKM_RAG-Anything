import axios, { AxiosError, AxiosResponse, InternalAxiosRequestConfig } from 'axios'
import { enhancedToast } from '@/hooks/useToast'

// Avoid any potential conflicts with global String
declare const String: StringConstructor

// Enhanced error interface
interface ApiError {
  error_code: string
  message: string
  user_message: string
  category: string
  severity: string
  status_code: number
  timestamp: string
  details: Record<string, any>
  recovery_suggestions: string[]
}

// Create axios instance with base configuration
export const api = axios.create({
  baseURL: '/api',
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Request interceptor for logging and request tracking
api.interceptors.request.use(
  (config: InternalAxiosRequestConfig) => {
    console.log(`🚀 API Request: ${config.method?.toUpperCase()} ${config.url}`)
    return config
  },
  (error) => {
    console.error('❌ API Request Setup Error:', error)
    return Promise.reject(error)
  }
)

// Response interceptor for enhanced error handling
api.interceptors.response.use(
  (response: AxiosResponse) => {
    console.log(`✅ API Response: ${response.status} ${response.statusText}`)
    return response
  },
  (error: AxiosError) => {
    console.error('❌ API Error:', error.response?.status, error.response?.data || error.message)
    return handleApiError(error)
  }
)

function handleApiError(error: AxiosError): Promise<never> {
  // Network error (no response)
  if (!error.response) {
    if (error.code === 'ECONNABORTED') {
      enhancedToast.error('Request timeout. Please try again.', {
        description: 'The server took too long to respond',
      })
    } else {
      enhancedToast.error('Network error. Please check your connection.', {
        description: 'Unable to reach the server',
      })
    }
    return Promise.reject(error)
  }

  const status = error.response.status
  const errorData = error.response.data as { error?: ApiError } | undefined
  const apiError = errorData?.error

  // Handle structured API errors
  if (apiError) {
    return handleStructuredError(apiError, error)
  }

  // Handle HTTP status codes
  switch (status) {
    case 400:
      enhancedToast.error('Invalid request', {
        description: 'Please check your input and try again',
      })
      break
    
    case 401:
      enhancedToast.error('Authentication required', {
        description: 'Please log in to continue',
      })
      break
    
    case 403:
      enhancedToast.error('Access denied', {
        description: 'You don\'t have permission to perform this action',
      })
      break
    
    case 404:
      enhancedToast.error('Not found', {
        description: 'The requested resource could not be found',
      })
      break
    
    case 409:
      enhancedToast.error('Conflict', {
        description: 'The operation conflicts with existing data',
      })
      break
    
    case 422:
      enhancedToast.error('Validation failed', {
        description: 'Please check your input and try again',
      })
      break
    
    case 429:
      enhancedToast.warning('Too many requests', {
        description: 'Please wait before trying again',
      })
      break
    
    case 500:
      enhancedToast.error('Server error', {
        description: 'An internal server error occurred',
      })
      break
    
    case 502:
      enhancedToast.error('Service unavailable', {
        description: 'The service is temporarily unavailable',
      })
      break
    
    case 503:
      enhancedToast.error('Service unavailable', {
        description: 'The service is under maintenance',
      })
      break
    
    default:
      enhancedToast.error('Unexpected error', {
        description: `HTTP ${status}: ${error.response.statusText}`,
      })
  }

  return Promise.reject(error)
}

function handleStructuredError(apiError: ApiError, originalError: AxiosError): Promise<never> {
  const { severity, user_message, recovery_suggestions } = apiError

  // Determine toast type based on severity
  const showToast = () => {
    const options = {
      description: recovery_suggestions.length > 0 
        ? `Try: ${recovery_suggestions[0]}` 
        : undefined,
      duration: severity === 'critical' || severity === 'high' ? 8000 : 5000,
    }

    switch (severity) {
      case 'critical':
      case 'high':
        return enhancedToast.error(user_message, options)
      case 'medium':
        return enhancedToast.warning(user_message, options)
      case 'low':
        return enhancedToast.info(user_message, options)
      default:
        return enhancedToast.error(user_message, options)
    }
  }

  showToast()
  return Promise.reject(originalError)
}

// Utility functions for common API patterns
export const apiUtils = {
  // Handle loading states with toast
  withLoadingToast: async <T>(
    promise: Promise<T>,
    loadingMessage: string,
    successMessage?: string
  ): Promise<T> => {
    const toastId = enhancedToast.loading(loadingMessage)
    
    try {
      const result = await promise
      
      if (successMessage) {
        toastId.update({
          id: toastId.id,
          variant: 'success',
          title: 'Success',
          description: successMessage,
          duration: 3000,
        })
      } else {
        toastId.dismiss()
      }
      
      return result
    } catch (error) {
      toastId.dismiss()
      throw error
    }
  },

  // Retry failed requests
  retry: async <T>(
    apiCall: () => Promise<T>,
    maxAttempts: number = 3,
    delay: number = 1000
  ): Promise<T> => {
    for (let attempt = 1; attempt <= maxAttempts; attempt++) {
      try {
        return await apiCall()
      } catch (error) {
        if (attempt === maxAttempts) {
          throw error
        }
        
        // Don't retry on client errors (4xx)
        const status = (error as AxiosError)?.response?.status
        if (status && status >= 400 && status < 500) {
          throw error
        }
        
        // Wait before retrying
        await new Promise(resolve => setTimeout(resolve, delay * attempt))
      }
    }
    
    throw new Error('Max retry attempts reached')
  },

  // Check if error is retryable
  isRetryable: (error: AxiosError): boolean => {
    const status = error.response?.status
    
    // Network errors are retryable
    if (!status) return true
    
    // Server errors are retryable
    if (status >= 500) return true
    
    // Rate limiting is retryable
    if (status === 429) return true
    
    return false
  },
}

export default api