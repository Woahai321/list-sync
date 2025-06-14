"use client"

import { useEffect, useState } from "react"
import { createPortal } from "react-dom"

interface PortalProps {
  children: React.ReactNode
  container?: Element | null
}

export function Portal({ children, container }: PortalProps) {
  const [mounted, setMounted] = useState(false)
  const [portalContainer, setPortalContainer] = useState<Element | null>(null)

  useEffect(() => {
    setMounted(true)
    
    // Use provided container or create/find a default one
    if (container) {
      setPortalContainer(container)
    } else {
      let portalRoot = document.getElementById('portal-root')
      if (!portalRoot) {
        portalRoot = document.createElement('div')
        portalRoot.id = 'portal-root'
        portalRoot.style.position = 'relative'
        portalRoot.style.zIndex = '2147483647'
        document.body.appendChild(portalRoot)
      }
      setPortalContainer(portalRoot)
    }

    return () => {
      // Cleanup: remove portal root if it's empty and we created it
      if (!container) {
        const portalRoot = document.getElementById('portal-root')
        if (portalRoot && portalRoot.children.length === 0) {
          document.body.removeChild(portalRoot)
        }
      }
    }
  }, [container])

  if (!mounted || !portalContainer) {
    return null
  }

  return createPortal(children, portalContainer)
} 