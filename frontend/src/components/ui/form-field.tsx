import React from 'react'
import { cn } from '@/lib/utils'
import { Label } from './label'
import { Input } from './input'
import { Textarea } from './textarea'
import { Alert, AlertDescription } from './alert'
import { AlertCircle, CheckCircle } from 'lucide-react'

interface FormFieldProps {
  label: string
  name: string
  type?: 'text' | 'email' | 'password' | 'textarea' | 'number'
  value: string
  onChange: (value: string) => void
  onBlur?: () => void
  error?: string
  success?: boolean
  required?: boolean
  disabled?: boolean
  placeholder?: string
  description?: string
  className?: string
  rows?: number
  maxLength?: number
  pattern?: string
  autoComplete?: string
}

export function FormField({
  label,
  name,
  type = 'text',
  value,
  onChange,
  onBlur,
  error,
  success,
  required,
  disabled,
  placeholder,
  description,
  className,
  rows = 3,
  maxLength,
  pattern,
  autoComplete,
}: FormFieldProps) {
  const hasError = Boolean(error)
  const hasSuccess = success && !hasError && value.length > 0

  const inputProps = {
    id: name,
    name,
    value,
    onChange: (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => 
      onChange(e.target.value),
    onBlur,
    disabled,
    placeholder,
    maxLength,
    pattern,
    autoComplete,
    className: cn(
      "transition-colors",
      hasError && "border-destructive focus:border-destructive focus:ring-destructive",
      hasSuccess && "border-green-500 focus:border-green-500 focus:ring-green-500",
      className
    ),
    'aria-invalid': hasError,
    'aria-describedby': [
      description && `${name}-description`,
      error && `${name}-error`,
    ].filter(Boolean).join(' ') || undefined,
  }

  return (
    <div className="space-y-2">
      <Label 
        htmlFor={name}
        className={cn(
          "flex items-center gap-2",
          hasError && "text-destructive",
          hasSuccess && "text-green-700 dark:text-green-400"
        )}
      >
        {label}
        {required && <span className="text-destructive">*</span>}
        {hasSuccess && <CheckCircle className="h-4 w-4" />}
      </Label>

      {description && (
        <p 
          id={`${name}-description`}
          className="text-sm text-muted-foreground"
        >
          {description}
        </p>
      )}

      {type === 'textarea' ? (
        <Textarea
          {...inputProps}
          rows={rows}
        />
      ) : (
        <Input
          {...inputProps}
          type={type}
        />
      )}

      {maxLength && (
        <div className="flex justify-end">
          <span className={cn(
            "text-xs text-muted-foreground",
            value.length > maxLength * 0.9 && "text-yellow-600",
            value.length >= maxLength && "text-destructive"
          )}>
            {value.length}/{maxLength}
          </span>
        </div>
      )}

      {error && (
        <Alert variant="destructive" id={`${name}-error`}>
          <AlertCircle className="h-4 w-4" />
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}
    </div>
  )
}

// Form validation utilities
export const validators = {
  required: (value: string, fieldName: string) => {
    if (!value.trim()) {
      return `${fieldName} is required`
    }
    return null
  },

  email: (value: string) => {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
    if (value && !emailRegex.test(value)) {
      return 'Please enter a valid email address'
    }
    return null
  },

  minLength: (value: string, min: number, fieldName: string) => {
    if (value && value.length < min) {
      return `${fieldName} must be at least ${min} characters long`
    }
    return null
  },

  maxLength: (value: string, max: number, fieldName: string) => {
    if (value && value.length > max) {
      return `${fieldName} must be no more than ${max} characters long`
    }
    return null
  },

  pattern: (value: string, pattern: RegExp, message: string) => {
    if (value && !pattern.test(value)) {
      return message
    }
    return null
  },

  custom: (value: string, validator: (value: string) => string | null) => {
    return validator(value)
  },
}

// Hook for form validation
export function useFormValidation<T extends Record<string, string>>(
  initialValues: T,
  validationRules: Record<keyof T, Array<(value: string) => string | null>>
) {
  const [values, setValues] = React.useState<T>(initialValues)
  const [errors, setErrors] = React.useState<Partial<Record<keyof T, string>>>({})
  const [touched, setTouched] = React.useState<Partial<Record<keyof T, boolean>>>({})

  const validateField = React.useCallback((name: keyof T, value: string) => {
    const rules = validationRules[name] || []
    
    for (const rule of rules) {
      const error = rule(value)
      if (error) {
        return error
      }
    }
    
    return null
  }, [validationRules])

  const validateAll = React.useCallback(() => {
    const newErrors: Partial<Record<keyof T, string>> = {}
    let isValid = true

    Object.keys(values).forEach((key) => {
      const fieldName = key as keyof T
      const error = validateField(fieldName, values[fieldName])
      if (error) {
        newErrors[fieldName] = error
        isValid = false
      }
    })

    setErrors(newErrors)
    return isValid
  }, [values, validateField])

  const setValue = React.useCallback((name: keyof T, value: string) => {
    setValues(prev => ({ ...prev, [name]: value }))
    
    // Clear error when user starts typing
    if (errors[name]) {
      setErrors(prev => ({ ...prev, [name]: undefined }))
    }
  }, [errors])

  const setFieldTouched = React.useCallback((name: keyof T) => {
    setTouched(prev => ({ ...prev, [name]: true }))
    
    // Validate field when it loses focus
    const error = validateField(name, values[name])
    setErrors(prev => ({ ...prev, [name]: error || undefined }))
  }, [validateField, values])

  const reset = React.useCallback(() => {
    setValues(initialValues)
    setErrors({})
    setTouched({})
  }, [initialValues])

  const hasErrors = Object.values(errors).some(error => error !== undefined)
  const isFormValid = !hasErrors && Object.keys(touched).length > 0

  return {
    values,
    errors,
    touched,
    setValue,
    setFieldTouched,
    validateAll,
    reset,
    hasErrors,
    isFormValid,
  }
}