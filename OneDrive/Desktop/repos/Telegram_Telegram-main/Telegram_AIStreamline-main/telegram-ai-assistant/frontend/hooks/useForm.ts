import { useState, useCallback, ChangeEvent, FormEvent } from 'react'
import { VALIDATION_RULES } from '../utils/constants'

interface ValidationRule {
  required?: boolean
  pattern?: RegExp
  minLength?: number
  maxLength?: number
  min?: number
  max?: number
  custom?: (value: any) => boolean
  message: string
}

interface FormConfig {
  initialValues: Record<string, any>
  validationRules?: Record<string, ValidationRule>
  onSubmit: (values: Record<string, any>) => void | Promise<void>
}

interface ValidationErrors {
  [key: string]: string
}

export function useForm({ initialValues, validationRules = {}, onSubmit }: FormConfig) {
  const [values, setValues] = useState(initialValues)
  const [errors, setErrors] = useState<ValidationErrors>({})
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [touched, setTouched] = useState<Record<string, boolean>>({})

  // Validate a single field
  const validateField = useCallback(
    (name: string, value: any): string => {
      const rules = validationRules[name]
      if (!rules) return ''

      if (rules.required && !value) {
        return rules.message || 'This field is required'
      }

      if (rules.pattern && !rules.pattern.test(value)) {
        return rules.message || 'Invalid format'
      }

      if (rules.minLength && value.length < rules.minLength) {
        return rules.message || `Minimum length is ${rules.minLength}`
      }

      if (rules.maxLength && value.length > rules.maxLength) {
        return rules.message || `Maximum length is ${rules.maxLength}`
      }

      if (rules.min && Number(value) < rules.min) {
        return rules.message || `Minimum value is ${rules.min}`
      }

      if (rules.max && Number(value) > rules.max) {
        return rules.message || `Maximum value is ${rules.max}`
      }

      if (rules.custom && !rules.custom(value)) {
        return rules.message || 'Invalid value'
      }

      return ''
    },
    [validationRules]
  )

  // Validate all fields
  const validateForm = useCallback(() => {
    const newErrors: ValidationErrors = {}
    let isValid = true

    Object.keys(values).forEach((key) => {
      const error = validateField(key, values[key])
      if (error) {
        newErrors[key] = error
        isValid = false
      }
    })

    setErrors(newErrors)
    return isValid
  }, [values, validateField])

  // Handle input change
  const handleChange = useCallback(
    (e: ChangeEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>) => {
      const { name, value, type } = e.target
      const finalValue = type === 'checkbox' 
        ? (e.target as HTMLInputElement).checked
        : value

      setValues((prev) => ({ ...prev, [name]: finalValue }))
      setTouched((prev) => ({ ...prev, [name]: true }))

      const error = validateField(name, finalValue)
      setErrors((prev) => ({ ...prev, [name]: error }))
    },
    [validateField]
  )

  // Handle form submission
  const handleSubmit = useCallback(
    async (e: FormEvent) => {
      e.preventDefault()
      setIsSubmitting(true)

      try {
        if (validateForm()) {
          await onSubmit(values)
        }
      } catch (error) {
        console.error('Form submission error:', error)
      } finally {
        setIsSubmitting(false)
      }
    },
    [values, validateForm, onSubmit]
  )

  // Reset form
  const resetForm = useCallback(() => {
    setValues(initialValues)
    setErrors({})
    setTouched({})
    setIsSubmitting(false)
  }, [initialValues])

  // Set field value programmatically
  const setFieldValue = useCallback((name: string, value: any) => {
    setValues((prev) => ({ ...prev, [name]: value }))
    const error = validateField(name, value)
    setErrors((prev) => ({ ...prev, [name]: error }))
  }, [validateField])

  // Set field error programmatically
  const setFieldError = useCallback((name: string, error: string) => {
    setErrors((prev) => ({ ...prev, [name]: error }))
  }, [])

  // Check if form is valid
  const isValid = useCallback(() => Object.keys(errors).length === 0, [errors])

  // Get field props
  const getFieldProps = useCallback(
    (name: string) => ({
      name,
      value: values[name],
      onChange: handleChange,
      onBlur: () => setTouched((prev) => ({ ...prev, [name]: true })),
      error: touched[name] ? errors[name] : undefined,
    }),
    [values, errors, touched, handleChange]
  )

  // Common validation rules
  const commonRules = {
    email: {
      pattern: VALIDATION_RULES.EMAIL.pattern,
      message: VALIDATION_RULES.EMAIL.message,
    },
    password: {
      minLength: VALIDATION_RULES.PASSWORD.minLength,
      message: VALIDATION_RULES.PASSWORD.message,
    },
    phone: {
      pattern: VALIDATION_RULES.PHONE.pattern,
      message: VALIDATION_RULES.PHONE.message,
    },
  }

  return {
    values,
    errors,
    touched,
    isSubmitting,
    isValid: isValid(),
    handleChange,
    handleSubmit,
    resetForm,
    setFieldValue,
    setFieldError,
    getFieldProps,
    validateField,
    validateForm,
    commonRules,
  }
}
