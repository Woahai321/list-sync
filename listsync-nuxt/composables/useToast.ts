/**
 * Toast Notifications Composable
 * Provides a simple toast notification system
 */

import type { ToastNotification } from '~/types'

// Global toast state
const toasts = ref<ToastNotification[]>([])
let toastIdCounter = 0

/**
 * Toast composable
 */
export function useToast() {
  /**
   * Add a toast notification
   */
  const addToast = (
    type: 'success' | 'error' | 'info' | 'warning',
    title: string,
    message?: string,
    duration: number = 5000
  ) => {
    const id = `toast-${++toastIdCounter}`
    
    const toast: ToastNotification = {
      id,
      type,
      title,
      message,
      duration,
    }

    toasts.value.push(toast)

    // Auto-remove after duration
    if (duration > 0) {
      setTimeout(() => {
        removeToast(id)
      }, duration)
    }

    return id
  }

  /**
   * Remove a toast by ID
   */
  const removeToast = (id: string) => {
    const index = toasts.value.findIndex(t => t.id === id)
    if (index > -1) {
      toasts.value.splice(index, 1)
    }
  }

  /**
   * Show success toast
   */
  const showSuccess = (title: string, message?: string, duration?: number) => {
    return addToast('success', title, message, duration)
  }

  /**
   * Show error toast
   */
  const showError = (title: string, message?: string, duration?: number) => {
    return addToast('error', title, message, duration || 7000) // Errors stay longer
  }

  /**
   * Show info toast
   */
  const showInfo = (title: string, message?: string, duration?: number) => {
    return addToast('info', title, message, duration)
  }

  /**
   * Show warning toast
   */
  const showWarning = (title: string, message?: string, duration?: number) => {
    return addToast('warning', title, message, duration)
  }

  /**
   * Clear all toasts
   */
  const clearAll = () => {
    toasts.value = []
  }

  return {
    toasts: readonly(toasts),
    addToast,
    removeToast,
    showSuccess,
    showError,
    showInfo,
    showWarning,
    clearAll,
  }
}

/**
 * Global toast helper (can be used anywhere)
 */
export const toast = {
  success: (title: string, message?: string, duration?: number) => {
    const { showSuccess } = useToast()
    return showSuccess(title, message, duration)
  },
  
  error: (title: string, message?: string, duration?: number) => {
    const { showError } = useToast()
    return showError(title, message, duration)
  },
  
  info: (title: string, message?: string, duration?: number) => {
    const { showInfo } = useToast()
    return showInfo(title, message, duration)
  },
  
  warning: (title: string, message?: string, duration?: number) => {
    const { showWarning } = useToast()
    return showWarning(title, message, duration)
  },
}

