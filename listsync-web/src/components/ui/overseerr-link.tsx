import { ExternalLink } from "lucide-react"
import { useOverseerrConfig, generateOverseerrUrl } from "@/hooks/useOverseerr"

interface OverseerrLinkProps {
  overseerrId?: number | null
  mediaType: string
  title: string
  className?: string
}

export function OverseerrLink({ overseerrId, mediaType, title, className = "" }: OverseerrLinkProps) {
  const { data: overseerrConfig } = useOverseerrConfig()
  
  if (!overseerrId || !overseerrConfig?.configured || !overseerrConfig?.base_url) {
    return (
      <span className="text-xs text-white/30">
        Overseerr ID: {overseerrId || 'N/A'}
      </span>
    )
  }

  const overseerrUrl = generateOverseerrUrl(overseerrConfig.base_url, mediaType, overseerrId)
  
  if (!overseerrUrl) {
    return (
      <span className="text-xs text-white/50">
        Overseerr ID: {overseerrId}
      </span>
    )
  }

  return (
    <a
      href={overseerrUrl}
      target="_blank"
      rel="noopener noreferrer"
      className={`text-xs text-purple-400 hover:text-purple-300 transition-colors flex items-center gap-1 ${className}`}
      title={`View "${title}" in Overseerr`}
    >
      <ExternalLink className="h-3 w-3" />
      <span>Overseerr</span>
    </a>
  )
} 