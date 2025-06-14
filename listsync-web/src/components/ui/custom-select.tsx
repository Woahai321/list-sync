"use client"

import { useState, useRef, useEffect } from "react"
import { ChevronDown, Check } from "lucide-react"
import { Portal } from "./portal"

interface SelectOption {
  value: string
  label: string
}

interface CustomSelectProps {
  value: string
  onChange: (value: string) => void
  options: SelectOption[]
  placeholder?: string
  className?: string
}

export function CustomSelect({ value, onChange, options, placeholder = "Select...", className = "" }: CustomSelectProps) {
  const [isOpen, setIsOpen] = useState(false)
  const [position, setPosition] = useState({ x: 0, y: 0, width: 0 })
  const selectRef = useRef<HTMLDivElement>(null)

  const updatePosition = () => {
    if (!selectRef.current) return

    const rect = selectRef.current.getBoundingClientRect()
    const scrollX = window.pageXOffset || document.documentElement.scrollLeft
    const scrollY = window.pageYOffset || document.documentElement.scrollTop

    setPosition({
      x: rect.left + scrollX,
      y: rect.bottom + scrollY + 8, // 8px gap
      width: rect.width
    })
  }

  // Close dropdown when clicking outside
  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (selectRef.current && !selectRef.current.contains(event.target as Node)) {
        setIsOpen(false)
      }
    }

    if (isOpen) {
      document.addEventListener("mousedown", handleClickOutside)
      return () => document.removeEventListener("mousedown", handleClickOutside)
    }
  }, [isOpen])

  // Close dropdown on escape key
  useEffect(() => {
    function handleEscape(event: KeyboardEvent) {
      if (event.key === "Escape") {
        setIsOpen(false)
      }
    }

    if (isOpen) {
      document.addEventListener("keydown", handleEscape)
      return () => document.removeEventListener("keydown", handleEscape)
    }
  }, [isOpen])

  // Update position when opened or on scroll/resize
  useEffect(() => {
    if (isOpen) {
      updatePosition()
      
      const handleScroll = () => updatePosition()
      const handleResize = () => updatePosition()
      
      window.addEventListener('scroll', handleScroll, true)
      window.addEventListener('resize', handleResize)
      
      return () => {
        window.removeEventListener('scroll', handleScroll, true)
        window.removeEventListener('resize', handleResize)
      }
    }
  }, [isOpen])

  const selectedOption = options.find(option => option.value === value)

  const handleToggle = () => {
    if (!isOpen) {
      updatePosition()
    }
    setIsOpen(!isOpen)
  }

  return (
    <>
      <div className={`relative ${className}`} ref={selectRef}>
        {/* Select Button */}
        <button
          type="button"
          onClick={handleToggle}
          className={`
            w-full px-4 py-2 text-left
            bg-white/10 border border-white/20 rounded-lg
            text-white placeholder-white/50
            hover:bg-white/15 hover:border-white/30
            focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent
            transition-all duration-200 ease-in-out
            flex items-center justify-between
            backdrop-blur-sm
            titillium-web-regular
            ${isOpen ? 'ring-2 ring-purple-500 border-transparent bg-white/15 shadow-lg shadow-purple-500/20' : ''}
          `}
        >
          <span className={selectedOption ? 'text-white' : 'text-white/50'}>
            {selectedOption ? selectedOption.label : placeholder}
          </span>
          <ChevronDown 
            className={`h-4 w-4 text-white/70 transition-all duration-300 ease-in-out ${
              isOpen ? 'transform rotate-180 text-purple-400' : ''
            }`} 
          />
        </button>
      </div>

      {/* Dropdown Menu - Rendered in Portal */}
      {isOpen && (
        <Portal>
          <div
            className="fixed z-[2147483647]"
            style={{
              left: position.x,
              top: position.y,
              width: position.width,
            }}
          >
            <div className="
              bg-gray-900/95 backdrop-blur-md border border-white/20 rounded-lg shadow-2xl
              max-h-60 overflow-y-auto
              animate-in fade-in-0 zoom-in-95 slide-in-from-top-2 duration-200
              ring-1 ring-purple-500/20
            ">
              {options.map((option, index) => (
                <button
                  key={option.value}
                  type="button"
                  onClick={() => {
                    onChange(option.value)
                    setIsOpen(false)
                  }}
                  className={`
                    w-full px-4 py-3 text-left
                    hover:bg-purple-500/20 hover:text-purple-200
                    transition-all duration-200 ease-in-out
                    flex items-center justify-between
                    titillium-web-regular
                    ${index === 0 ? 'rounded-t-lg' : ''}
                    ${index === options.length - 1 ? 'rounded-b-lg' : ''}
                    ${value === option.value 
                      ? 'bg-purple-500/30 text-purple-200 border-l-2 border-purple-400 shadow-inner' 
                      : 'text-white/90 hover:shadow-sm'
                    }
                  `}
                  style={{
                    animationDelay: `${index * 50}ms`
                  }}
                >
                  <span>{option.label}</span>
                  {value === option.value && (
                    <Check className="h-4 w-4 text-purple-400 animate-in zoom-in-50 duration-200" />
                  )}
                </button>
              ))}
            </div>
          </div>
        </Portal>
      )}
    </>
  )
} 