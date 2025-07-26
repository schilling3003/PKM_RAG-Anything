import React, { useState, useCallback, useRef } from 'react'
import { enhancedToast } from './useToast'

interface RetryOptions {
  maxAttempts?: number
  delay?: number
  exponentialBackoff?: boolean
  retryCondition?: (error: any) => boolean
}

interface ErrorRecoveryState {
  isRetrying: boolean
  attemptCount: number
  lastError: Error | null
}

export function useErrorRecovery() {
  const [state, setState] = useState<ErrorRecoveryState>({
    isRetrying: false,
    attemptCount: 0,
    lastError: null,
  })

  const timeoutRef = useRef<NodeJS.Timeout>()

  const retry = useCallback(async <T>(
    operation: () => Promise<T>,
    options: RetryOptions = {}
  ): Promise<T> => {
    const {
      maxAttempts = 3,
      delay = 1000,
      exponentialBackoff = true,
      retryCondition = () => true,
    } = options

    setState(prev => ({ ...prev, isRetrying: true, attemptCount: 0 }))

    for (let attempt = 1; attempt <= maxAttempts; attempt++) {
      try {
        const result = await operation()
        setState(prev => ({ ...prev, isRetrying: false, lastError: null }))
        return result
      } catch (error) {
        const err = error as Error
        setState(prev => ({ 
          ...prev, 
          attemptCount: attempt, 
          lastError: err 
        }))

        // Check if we should retry
        if (attempt === maxAttempts || !retryCondition(err)) {
          setState(prev => ({ ...prev, isRetrying: false }))
          throw err
        }

        // Calculate delay with exponential backoff
        const currentDelay = exponentialBackoff 
          ? delay * Math.pow(2, attempt - 1)
          : delay

        // Show retry notification
        enhancedToast.info(
          `Attempt ${attempt} failed. Retrying in ${currentDelay / 1000}s...`,
          { duration: currentDelay }
        )

        // Wait before retrying
        await new Promise(resolve => {
          timeoutRef.current = setTimeout(resolve, currentDelay)
        })
      }
    }

    throw state.lastError
  }, [state.lastError])

  const reset = useCallback(() => {
    if (timeoutRef.current) {
      clearTimeout(timeoutRef.current)
    }
    setState({
      isRetrying: false,
      attemptCount: 0,
      lastError: null,
    })
  }, [])

  return {
    ...state,
    retry,
    reset,
  }
}

// Hook for handling API errors with automatic retry
export function useApiErrorHandler() {
  const { retry, ...recoveryState } = useErrorRecovery()

  const handleApiError = useCallback((error: any) => {
    // Parse API error response
    const errorData = error?.response?.data?.error || {}
    const message = errorData.user_message || errorData.message || 'An unexpected error occurred'
    const suggestions = errorData.recovery_suggestions || []
    const errorCode = errorData.error_code
    const severity = errorData.severity || 'medium'

    // Show appropriate toast based on severity
    if (severity === 'critical' || severity === 'high') {
      enhancedToast.error(message, {
        duration: 8000,
        // Note: action would need to be a proper ToastActionElement
        // For now, we'll include suggestions in the description
      })
    } else {
      enhancedToast.warning(message, {
        duration: 5000,
      })
    }

    return {
      message,
      suggestions,
      errorCode,
      severity,
      canRetry: isRetryableError(error),
    }
  }, [])

  const retryApiCall = useCallback(async <T>(
    apiCall: () => Promise<T>,
    options?: RetryOptions
  ): Promise<T> => {
    return retry(apiCall, {
      maxAttempts: 3,
      delay: 1000,
      exponentialBackoff: true,
      retryCondition: isRetryableError,
      ...options,
    })
  }, [retry])

  return {
    ...recoveryState,
    handleApiError,
    retryApiCall,
  }
}

// Determine if an error is retryable
function isRetryableError(error: any): boolean {
  const status = error?.response?.status
  const errorCode = error?.response?.data?.error?.error_code

  // Network errors are retryable
  if (!status) return true

  // Server errors (5xx) are retryable
  if (status >= 500) return true

  // Rate limiting is retryable
  if (status === 429) return true

  // Specific error codes that are retryable
  const retryableErrorCodes = [
    'DATABASE_500',
    'EXTERNAL_SERVICE_502',
    'FILE_SYSTEM_500',
    'PROCESSING_422', // Sometimes processing errors are temporary
  ]

  return retryableErrorCodes.some(code => errorCode?.includes(code))
}

// Hook for form validation with error recovery
export function useFormErrorHandler() {
  const [fieldErrors, setFieldErrors] = useState<Record<string, string>>({})
  const [generalError, setGeneralError] = useState<string | null>(null)

  const handleValidationError = useCallback((error: any) => {
    const errorData = error?.response?.data?.error || {}
    
    if (errorData.category === 'validation' && errorData.details?.field_errors) {
      setFieldErrors(errorData.details.field_errors)
      setGeneralError(null)
    } else {
      setGeneralError(errorData.user_message || 'Please check your input and try again')
      setFieldErrors({})
    }

    // Show toast for general validation errors
    if (errorData.user_message) {
      enhancedToast.warning(errorData.user_message, {
        duration: 4000,
      })
    }
  }, [])

  const clearErrors = useCallback(() => {
    setFieldErrors({})
    setGeneralError(null)
  }, [])

  const clearFieldError = useCallback((fieldName: string) => {
    setFieldErrors(prev => {
      const newErrors = { ...prev }
      delete newErrors[fieldName]
      return newErrors
    })
  }, [])

  return {
    fieldErrors,
    generalError,
    handleValidationError,
    clearErrors,
    clearFieldError,
    hasErrors: Object.keys(fieldErrors).length > 0 || generalError !== null,
  }
}

// Hook for handling offline/online state
export function useOfflineHandler() {
  const [isOnline, setIsOnline] = useState(navigator.onLine)
  const [wasOffline, setWasOffline] = useState(false)

  React.useEffect(() => {
    const handleOnline = () => {
      setIsOnline(true)
      if (wasOffline) {
        enhancedToast.success('Connection restored', {
          description: 'You are back online',
        })
        setWasOffline(false)
      }
    }

    const handleOffline = () => {
      setIsOnline(false)
      setWasOffline(true)
      enhancedToast.warning('Connection lost', {
        description: 'Some features may not work properly',
        duration: Infinity,
      })
    }

    window.addEventListener('online', handleOnline)
    window.addEventListener('offline', handleOffline)

    return () => {
      window.removeEventListener('online', handleOnline)
      window.removeEventListener('offline', handleOffline)
    }
  }, [])

  return { isOnline, wasOffline }
}