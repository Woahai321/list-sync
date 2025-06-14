import { useQuery } from "@tanstack/react-query"

interface OverseerrConfig {
  configured: boolean
  base_url: string | null
  user_id: string
  error?: string
}

export function useOverseerrConfig() {
  return useQuery({
    queryKey: ["overseerr-config"],
    queryFn: async (): Promise<OverseerrConfig> => {
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL || "http://localhost:4222/api"}/overseerr/config`)
      if (!response.ok) {
        throw new Error("Failed to fetch Overseerr configuration")
      }
      return response.json()
    },
    staleTime: 5 * 60 * 1000, // 5 minutes
    refetchInterval: false, // Only refetch manually
  })
}

export function generateOverseerrUrl(
  baseUrl: string | null | undefined,
  mediaType: string,
  overseerrId: number | null | undefined
): string | null {
  if (!baseUrl || !overseerrId) {
    return null
  }
  
  // Determine the correct path based on media type
  const path = mediaType === 'tv' ? 'tv' : 'movie'
  
  return `${baseUrl}/${path}/${overseerrId}`
} 