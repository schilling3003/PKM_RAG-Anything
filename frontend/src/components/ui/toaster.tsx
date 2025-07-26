import {
  Toast,
  ToastClose,
  ToastDescription,
  ToastProvider,
  ToastTitle,
  ToastViewport,
} from "@/components/ui/toast"
import { useToast } from "@/hooks/useToast"
import { CheckCircle, AlertCircle, AlertTriangle, Info, Loader2 } from "lucide-react"

const getToastIcon = (variant?: string) => {
  switch (variant) {
    case 'success':
      return <CheckCircle className="h-4 w-4" />
    case 'destructive':
      return <AlertCircle className="h-4 w-4" />
    case 'warning':
      return <AlertTriangle className="h-4 w-4" />
    case 'info':
      return <Info className="h-4 w-4" />
    default:
      return null
  }
}

export function Toaster() {
  const { toasts } = useToast()

  return (
    <ToastProvider>
      {toasts.map(function ({ id, title, description, action, variant, ...props }) {
        const icon = getToastIcon(variant)
        const isLoading = title === 'Loading...'

        return (
          <Toast key={id} variant={variant} {...props}>
            <div className="flex items-start gap-3">
              {isLoading ? (
                <Loader2 className="h-4 w-4 animate-spin mt-0.5" />
              ) : (
                icon && <div className="mt-0.5">{icon}</div>
              )}
              <div className="grid gap-1 flex-1">
                {title && <ToastTitle>{title}</ToastTitle>}
                {description && (
                  <ToastDescription>{description}</ToastDescription>
                )}
              </div>
            </div>
            {action}
            <ToastClose />
          </Toast>
        )
      })}
      <ToastViewport />
    </ToastProvider>
  )
}