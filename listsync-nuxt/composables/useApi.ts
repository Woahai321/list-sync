/**
 * API Composables for ListSync
 * Provides reactive API calls with loading and error states
 */

import type { UseFetchOptions } from 'nuxt/app'

/**
 * Generic API call composable with automatic loading and error handling
 */
export function useApiCall<T>(
  endpoint: string,
  options?: UseFetchOptions<T>
) {
  const config = useRuntimeConfig()
  const baseURL = `${config.public.apiUrl}${config.public.apiBase}`

  return useFetch<T>(`${baseURL}${endpoint}`, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...options?.headers,
    },
  })
}

/**
 * GET request composable
 */
export function useApiGet<T>(
  endpoint: string,
  options?: UseFetchOptions<T>
) {
  return useApiCall<T>(endpoint, {
    ...options,
    method: 'GET',
  })
}

/**
 * POST request composable
 */
export function useApiPost<T>(
  endpoint: string,
  body?: any,
  options?: UseFetchOptions<T>
) {
  return useApiCall<T>(endpoint, {
    ...options,
    method: 'POST',
    body,
  })
}

/**
 * PUT request composable
 */
export function useApiPut<T>(
  endpoint: string,
  body?: any,
  options?: UseFetchOptions<T>
) {
  return useApiCall<T>(endpoint, {
    ...options,
    method: 'PUT',
    body,
  })
}

/**
 * DELETE request composable
 */
export function useApiDelete<T>(
  endpoint: string,
  options?: UseFetchOptions<T>
) {
  return useApiCall<T>(endpoint, {
    ...options,
    method: 'DELETE',
  })
}

/**
 * Manual fetch without automatic state management
 * Useful for imperatively triggering API calls
 */
export async function useApiFetch<T>(
  endpoint: string,
  options?: RequestInit & { method?: string; body?: any }
): Promise<T> {
  const config = useRuntimeConfig()
  const baseURL = `${config.public.apiUrl}${config.public.apiBase}`

  try {
    const response = await $fetch<T>(`${baseURL}${endpoint}`, {
      ...options,
      headers: {
        'Content-Type': 'application/json',
        ...options?.headers,
      },
    })
    return response
  } catch (error: any) {
    console.error(`API Fetch Error [${endpoint}]:`, error)
    throw error
  }
}

/**
 * Lazy API call - only executes when explicitly called
 */
export function useLazyApi<T>(
  endpoint: string,
  options?: UseFetchOptions<T>
) {
  const config = useRuntimeConfig()
  const baseURL = `${config.public.apiUrl}${config.public.apiBase}`

  return useLazyFetch<T>(`${baseURL}${endpoint}`, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...options?.headers,
    },
  })
}

