"use client"

import { useState, useRef, useEffect } from "react"
import { Portal } from "./portal"

interface TooltipProps {
  children: React.ReactNode
  content: React.ReactNode
  side?: "top" | "bottom" | "left" | "right"
  align?: "start" | "center" | "end"
  delayDuration?: number
  className?: string
}

export function Tooltip({ 
  children, 
  content, 
  side = "top", 
  align = "center", 
  delayDuration = 200,
  className = ""
}: TooltipProps) {
  const [isVisible, setIsVisible] = useState(false)
  const [position, setPosition] = useState({ x: 0, y: 0 })
  const triggerRef = useRef<HTMLDivElement>(null)
  const timeoutRef = useRef<NodeJS.Timeout | null>(null)

  const updatePosition = () => {
    if (!triggerRef.current) return

    const rect = triggerRef.current.getBoundingClientRect()
    const scrollX = window.pageXOffset || document.documentElement.scrollLeft
    const scrollY = window.pageYOffset || document.documentElement.scrollTop

    let x = 0
    let y = 0

    // Calculate position based on side
    switch (side) {
      case "top":
        x = rect.left + scrollX + (align === "start" ? 0 : align === "end" ? rect.width : rect.width / 2)
        y = rect.top + scrollY - 8 // 8px offset for arrow
        break
      case "bottom":
        x = rect.left + scrollX + (align === "start" ? 0 : align === "end" ? rect.width : rect.width / 2)
        y = rect.bottom + scrollY + 8 // 8px offset for arrow
        break
      case "left":
        x = rect.left + scrollX - 8 // 8px offset for arrow
        y = rect.top + scrollY + (align === "start" ? 0 : align === "end" ? rect.height : rect.height / 2)
        break
      case "right":
        x = rect.right + scrollX + 8 // 8px offset for arrow
        y = rect.top + scrollY + (align === "start" ? 0 : align === "end" ? rect.height : rect.height / 2)
        break
    }

    setPosition({ x, y })
  }

  const handleMouseEnter = () => {
    if (timeoutRef.current) {
      clearTimeout(timeoutRef.current)
    }
    timeoutRef.current = setTimeout(() => {
      updatePosition()
      setIsVisible(true)
    }, delayDuration)
  }

  const handleMouseLeave = () => {
    if (timeoutRef.current) {
      clearTimeout(timeoutRef.current)
    }
    setIsVisible(false)
  }

  useEffect(() => {
    if (isVisible) {
      const handleScroll = () => updatePosition()
      const handleResize = () => updatePosition()
      
      window.addEventListener('scroll', handleScroll, true)
      window.addEventListener('resize', handleResize)
      
      return () => {
        window.removeEventListener('scroll', handleScroll, true)
        window.removeEventListener('resize', handleResize)
      }
    }
  }, [isVisible])

  useEffect(() => {
    return () => {
      if (timeoutRef.current) {
        clearTimeout(timeoutRef.current)
      }
    }
  }, [])

  const getTransformOrigin = () => {
    switch (side) {
      case "top":
        return align === "start" ? "bottom left" : align === "end" ? "bottom right" : "bottom center"
      case "bottom":
        return align === "start" ? "top left" : align === "end" ? "top right" : "top center"
      case "left":
        return align === "start" ? "top right" : align === "end" ? "bottom right" : "center right"
      case "right":
        return align === "start" ? "top left" : align === "end" ? "bottom left" : "center left"
    }
  }

  const getTransform = () => {
    let transform = ""
    
    switch (side) {
      case "top":
        transform += "translateY(-100%)"
        break
      case "bottom":
        transform += "translateY(0%)"
        break
      case "left":
        transform += "translateX(-100%)"
        break
      case "right":
        transform += "translateX(0%)"
        break
    }

    if (side === "top" || side === "bottom") {
      if (align === "center") transform += " translateX(-50%)"
      else if (align === "end") transform += " translateX(-100%)"
    } else {
      if (align === "center") transform += " translateY(-50%)"
      else if (align === "end") transform += " translateY(-100%)"
    }

    return transform
  }

  return (
    <>
      <div
        ref={triggerRef}
        onMouseEnter={handleMouseEnter}
        onMouseLeave={handleMouseLeave}
        className="inline-block"
      >
        {children}
      </div>
      
      {isVisible && (
        <Portal>
          <div
            className={`
              fixed pointer-events-none z-[2147483647]
              px-3 py-2 bg-black/95 text-white text-xs rounded-lg shadow-xl
              border border-white/20 whitespace-nowrap
              transition-all duration-200 ease-out
              ${className}
            `}
            style={{
              left: position.x,
              top: position.y,
              transform: getTransform(),
              transformOrigin: getTransformOrigin(),
            }}
          >
            {content}
            
            {/* Arrow */}
            <div
              className="absolute w-0 h-0"
              style={{
                ...(side === "top" && {
                  top: "100%",
                  left: align === "start" ? "12px" : align === "end" ? "calc(100% - 12px)" : "50%",
                  transform: align === "center" ? "translateX(-50%)" : undefined,
                  borderLeft: "4px solid transparent",
                  borderRight: "4px solid transparent",
                  borderTop: "4px solid rgba(0, 0, 0, 0.95)",
                }),
                ...(side === "bottom" && {
                  bottom: "100%",
                  left: align === "start" ? "12px" : align === "end" ? "calc(100% - 12px)" : "50%",
                  transform: align === "center" ? "translateX(-50%)" : undefined,
                  borderLeft: "4px solid transparent",
                  borderRight: "4px solid transparent",
                  borderBottom: "4px solid rgba(0, 0, 0, 0.95)",
                }),
                ...(side === "left" && {
                  left: "100%",
                  top: align === "start" ? "12px" : align === "end" ? "calc(100% - 12px)" : "50%",
                  transform: align === "center" ? "translateY(-50%)" : undefined,
                  borderTop: "4px solid transparent",
                  borderBottom: "4px solid transparent",
                  borderLeft: "4px solid rgba(0, 0, 0, 0.95)",
                }),
                ...(side === "right" && {
                  right: "100%",
                  top: align === "start" ? "12px" : align === "end" ? "calc(100% - 12px)" : "50%",
                  transform: align === "center" ? "translateY(-50%)" : undefined,
                  borderTop: "4px solid transparent",
                  borderBottom: "4px solid transparent",
                  borderRight: "4px solid rgba(0, 0, 0, 0.95)",
                }),
              }}
            />
          </div>
        </Portal>
      )}
    </>
  )
} 