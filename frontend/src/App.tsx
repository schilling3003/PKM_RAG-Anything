import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { ReactQueryDevtools } from '@tanstack/react-query-devtools'
import { BrowserRouter } from 'react-router-dom'

import { AppRoutes } from './routes'
import { ErrorBoundary } from './components/error-boundary'
import { Toaster } from './components/ui/toaster'
import { useOfflineHandler } from './hooks/useErrorRecovery'

// Create a client with enhanced error handling
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 1000 * 60 * 5, // 5 minutes
      retry: (failureCount, error: any) => {
        // Don't retry on 4xx errors (client errors)
        if (error?.response?.status >= 400 && error?.response?.status < 500) {
          return false
        }
        // Retry up to 3 times for other errors
        return failureCount < 3
      },
      retryDelay: (attemptIndex) => Math.min(1000 * 2 ** attemptIndex, 30000),
    },
    mutations: {
      retry: (failureCount, error: any) => {
        // Don't retry mutations on client errors
        if (error?.response?.status >= 400 && error?.response?.status < 500) {
          return false
        }
        // Retry once for server errors
        return failureCount < 1
      },
    },
  },
})

function AppContent() {
  // Handle offline/online state
  useOfflineHandler()

  return (
    <div className="min-h-screen bg-background font-sans antialiased">
      <AppRoutes />
      <Toaster />
    </div>
  )
}

function App() {
  return (
    <ErrorBoundary level="critical" name="App">
      <QueryClientProvider client={queryClient}>
        <BrowserRouter>
          <ErrorBoundary level="page" name="Router">
            <AppContent />
          </ErrorBoundary>
        </BrowserRouter>
        <ReactQueryDevtools initialIsOpen={false} />
      </QueryClientProvider>
    </ErrorBoundary>
  )
}

export default App