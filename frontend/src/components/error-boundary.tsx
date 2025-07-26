import React from 'react'
import { Button } from './ui/button'
import { Card, CardContent, CardHeader, CardTitle } from './ui/card'
import { Alert, AlertDescription } from './ui/alert'
import { Badge } from './ui/badge'
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from './ui/collapsible'
import { ChevronDown, RefreshCw, AlertTriangle, Bug, Home } from 'lucide-react'

interface ErrorBoundaryState {
  hasError: boolean
  error?: Error
  errorInfo?: React.ErrorInfo
  errorId?: string
  retryCount: number
}

interface ErrorBoundaryProps {
  children: React.ReactNode
  fallback?: React.ComponentType<{ error: Error; retry: () => void }>
  onError?: (error: Error, errorInfo: React.ErrorInfo) => void
  level?: 'page' | 'component' | 'critical'
  name?: string
}

interface ErrorDetails {
  timestamp: string
  userAgent: string
  url: string
  userId?: string
  sessionId?: string
  buildVersion?: string
}

export class ErrorBoundary extends React.Component<
  ErrorBoundaryProps,
  ErrorBoundaryState
> {
  private errorDetails: ErrorDetails

  constructor(props: ErrorBoundaryProps) {
    super(props)
    this.state = { 
      hasError: false, 
      retryCount: 0 
    }
    
    this.errorDetails = {
      timestamp: new Date().toISOString(),
      userAgent: navigator.userAgent,
      url: window.location.href,
      sessionId: this.generateSessionId(),
      buildVersion: (import.meta as any).env?.VITE_APP_VERSION || 'unknown'
    }
  }

  private generateSessionId(): string {
    return Math.random().toString(36).substring(2, 15) + 
           Math.random().toString(36).substring(2, 15)
  }

  private generateErrorId(): string {
    return `error_${Date.now()}_${Math.random().toString(36).substring(2, 9)}`
  }

  static getDerivedStateFromError(error: Error): Partial<ErrorBoundaryState> {
    return { 
      hasError: true, 
      error,
      errorId: `error_${Date.now()}_${Math.random().toString(36).substring(2, 9)}`
    }
  }

  componentDidCatch(error: Error, errorInfo: React.ErrorInfo) {
    const errorId = this.generateErrorId()
    
    this.setState({ 
      errorInfo,
      errorId
    })

    // Enhanced error logging
    const errorReport = {
      errorId,
      message: error.message,
      stack: error.stack,
      componentStack: errorInfo.componentStack,
      props: this.props,
      details: this.errorDetails,
      level: this.props.level || 'component',
      boundaryName: this.props.name || 'Unknown',
      retryCount: this.state.retryCount
    }

    console.group(`🚨 Error Boundary: ${this.props.name || 'Unknown'}`)
    console.error('Error:', error)
    console.error('Error Info:', errorInfo)
    console.error('Error Report:', errorReport)
    console.groupEnd()

    // Call custom error handler if provided
    if (this.props.onError) {
      this.props.onError(error, errorInfo)
    }

    // Send error to monitoring service (if available)
    this.reportError(errorReport)
  }

  private async reportError(errorReport: any) {
    try {
      // Send error report to backend monitoring endpoint
      await fetch('/api/v1/monitoring/errors/report', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(errorReport)
      })
    } catch (reportingError) {
      console.warn('Failed to report error to monitoring service:', reportingError)
    }
  }

  private handleRetry = () => {
    this.setState(prevState => ({
      hasError: false,
      error: undefined,
      errorInfo: undefined,
      errorId: undefined,
      retryCount: prevState.retryCount + 1
    }))
  }

  private handleReload = () => {
    window.location.reload()
  }

  private handleGoHome = () => {
    window.location.href = '/'
  }

  private getErrorSeverity(): 'low' | 'medium' | 'high' | 'critical' {
    const { error, retryCount } = this.state
    const { level } = this.props

    if (level === 'critical' || retryCount > 2) return 'critical'
    if (level === 'page' || error?.name === 'ChunkLoadError') return 'high'
    if (retryCount > 0) return 'medium'
    return 'low'
  }

  private getRecoveryActions() {
    const severity = this.getErrorSeverity()
    const { level } = this.props

    const actions = []

    if (severity !== 'critical' && level !== 'page') {
      actions.push({
        label: 'Try Again',
        action: this.handleRetry,
        icon: RefreshCw,
        variant: 'default' as const
      })
    }

    if (level === 'component') {
      actions.push({
        label: 'Reload Page',
        action: this.handleReload,
        icon: RefreshCw,
        variant: 'outline' as const
      })
    }

    if (level === 'page' || severity === 'critical') {
      actions.push({
        label: 'Go Home',
        action: this.handleGoHome,
        icon: Home,
        variant: 'outline' as const
      })
    }

    actions.push({
      label: 'Reload Application',
      action: this.handleReload,
      icon: RefreshCw,
      variant: 'destructive' as const
    })

    return actions
  }

  private getSeverityColor() {
    const severity = this.getErrorSeverity()
    switch (severity) {
      case 'critical': return 'destructive'
      case 'high': return 'destructive'
      case 'medium': return 'secondary'
      case 'low': return 'outline'
      default: return 'outline'
    }
  }

  private getUserFriendlyMessage(): string {
    const { error } = this.state
    const { level } = this.props

    if (error?.name === 'ChunkLoadError') {
      return 'The application has been updated. Please reload the page to get the latest version.'
    }

    if (level === 'critical') {
      return 'A critical error occurred that prevents the application from functioning properly.'
    }

    if (level === 'page') {
      return 'This page encountered an error and cannot be displayed properly.'
    }

    return 'A component on this page encountered an error. You can try again or reload the page.'
  }

  render() {
    if (this.state.hasError) {
      // Use custom fallback if provided
      if (this.props.fallback) {
        const FallbackComponent = this.props.fallback
        return <FallbackComponent error={this.state.error!} retry={this.handleRetry} />
      }

      const severity = this.getErrorSeverity()
      const actions = this.getRecoveryActions()
      const isFullScreen = this.props.level === 'page' || severity === 'critical'

      const errorContent = (
        <Card className={`w-full ${isFullScreen ? 'max-w-2xl' : 'max-w-md'}`}>
          <CardHeader>
            <div className="flex items-center gap-2">
              <AlertTriangle className="h-5 w-5 text-destructive" />
              <CardTitle className="text-destructive">
                {severity === 'critical' ? 'Critical Error' : 'Something went wrong'}
              </CardTitle>
              <Badge variant={this.getSeverityColor()}>
                {severity.toUpperCase()}
              </Badge>
            </div>
          </CardHeader>
          <CardContent className="space-y-4">
            <Alert>
              <AlertDescription>
                {this.getUserFriendlyMessage()}
              </AlertDescription>
            </Alert>

            {this.state.retryCount > 0 && (
              <Alert>
                <AlertDescription>
                  Retry attempt #{this.state.retryCount}. If the problem persists, try reloading the page.
                </AlertDescription>
              </Alert>
            )}

            <div className="flex flex-wrap gap-2">
              {actions.map((action, index) => (
                <Button
                  key={index}
                  onClick={action.action}
                  variant={action.variant}
                  size="sm"
                  className="flex items-center gap-2"
                >
                  <action.icon className="h-4 w-4" />
                  {action.label}
                </Button>
              ))}
            </div>

            {/* Error details for debugging */}
            <Collapsible>
              <CollapsibleTrigger asChild>
                <Button variant="ghost" size="sm" className="flex items-center gap-2">
                  <Bug className="h-4 w-4" />
                  Error Details
                  <ChevronDown className="h-4 w-4" />
                </Button>
              </CollapsibleTrigger>
              <CollapsibleContent className="mt-2">
                <div className="bg-muted p-3 rounded-md text-sm font-mono space-y-2">
                  <div><strong>Error ID:</strong> {this.state.errorId}</div>
                  <div><strong>Message:</strong> {this.state.error?.message}</div>
                  <div><strong>Component:</strong> {this.props.name || 'Unknown'}</div>
                  <div><strong>Timestamp:</strong> {this.errorDetails.timestamp}</div>
                  {(import.meta as any).env?.DEV && (
                    <details className="mt-2">
                      <summary className="cursor-pointer">Stack Trace</summary>
                      <pre className="mt-2 text-xs overflow-auto max-h-32">
                        {this.state.error?.stack}
                      </pre>
                    </details>
                  )}
                </div>
              </CollapsibleContent>
            </Collapsible>
          </CardContent>
        </Card>
      )

      if (isFullScreen) {
        return (
          <div className="flex items-center justify-center min-h-screen p-4 bg-background">
            {errorContent}
          </div>
        )
      }

      return (
        <div className="flex items-center justify-center p-4">
          {errorContent}
        </div>
      )
    }

    return this.props.children
  }
}

// Higher-order component for easier usage
export function withErrorBoundary<P extends object>(
  Component: React.ComponentType<P>,
  errorBoundaryProps?: Omit<ErrorBoundaryProps, 'children'>
) {
  const WrappedComponent = (props: P) => (
    <ErrorBoundary {...errorBoundaryProps}>
      <Component {...props} />
    </ErrorBoundary>
  )

  WrappedComponent.displayName = `withErrorBoundary(${Component.displayName || Component.name})`
  return WrappedComponent
}