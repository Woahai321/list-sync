"use client"

import Link from "next/link"
import { usePathname } from "next/navigation"
import { useState, useEffect } from "react"
import { 
  Home, 
  List, 
  RefreshCw, 
  BarChart3, 
  Activity, 
  Settings,
  Menu,
  X,
  BarChart
} from "lucide-react"
import { Logo } from "@/components/ui/logo"

const navigation = [
  { name: "Dashboard", href: "/dashboard", icon: Home },
  { name: "Statistics", href: "/dashboard/statistics", icon: BarChart },
  { name: "Lists", href: "/dashboard/lists", icon: List },
  { name: "Sync", href: "/dashboard/sync", icon: RefreshCw },
  { name: "Analytics", href: "/dashboard/analytics", icon: BarChart3 },
  { name: "Activity", href: "/dashboard/activity", icon: Activity },
  { name: "Settings", href: "/dashboard/settings", icon: Settings },
]

export function Sidebar() {
  const pathname = usePathname()
  const [isCollapsed, setIsCollapsed] = useState(false)
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false)
  const [isMobile, setIsMobile] = useState(false)

  // Check if screen is mobile size
  useEffect(() => {
    const checkScreenSize = () => {
      setIsMobile(window.innerWidth < 768) // md breakpoint
    }
    
    checkScreenSize()
    window.addEventListener('resize', checkScreenSize)
    
    return () => window.removeEventListener('resize', checkScreenSize)
  }, [])

  // Close mobile menu when route changes
  useEffect(() => {
    setIsMobileMenuOpen(false)
  }, [pathname])

  // Desktop sidebar component
  const DesktopSidebar = () => (
    <div className={`glass-sidebar min-h-screen p-6 relative overflow-hidden transition-all duration-300 flex-shrink-0 ${
      isCollapsed ? 'w-20' : 'w-64'
    }`}>
      {/* Header with Toggle Button */}
      <div className="mb-8 relative">
        {!isCollapsed ? (
          <>
            <div className="flex items-center justify-between mb-1">
              <Logo size="sm" showText={true} className="flex-1" />
              <button
                onClick={() => setIsCollapsed(!isCollapsed)}
                className="p-2 rounded-lg glass-button hover:scale-105 transition-all duration-200 flex-shrink-0 ml-2"
                aria-label="Collapse sidebar"
              >
                <X className="h-4 w-4" style={{ color: '#9d34da' }} />
              </button>
            </div>
            <div className="flex items-center gap-2 ml-1">
              <div className="w-1 h-1 rounded-full bg-purple-400/60"></div>
              <p className="text-xs text-white/60 titillium-web-light tracking-wide uppercase">Web Interface</p>
            </div>
          </>
        ) : (
          <div className="flex flex-col items-center">
            {/* Collapsed logo */}
            <Logo size="sm" showText={false} className="mb-4" />
            <button
              onClick={() => setIsCollapsed(!isCollapsed)}
              className="p-2 rounded-lg glass-button hover:scale-105 transition-all duration-200"
              aria-label="Expand sidebar"
            >
              <Menu className="h-4 w-4" style={{ color: '#9d34da' }} />
            </button>
          </div>
        )}
      </div>

      {/* Navigation */}
      <nav className="space-y-2">
        {navigation.map((item) => {
          const isActive = pathname === item.href
          return (
            <Link
              key={item.name}
              href={item.href}
              className={`flex items-center rounded-lg transition-all duration-300 group ${
                isActive
                  ? "border shadow-lg"
                  : "hover:bg-white/10 hover:border hover:border-white/20"
              } ${isCollapsed ? 'justify-center p-3' : 'gap-3 px-4 py-3'}`}
              style={{
                backgroundColor: isActive ? 'rgba(157, 52, 218, 0.3)' : 'transparent',
                color: isActive ? '#ffffff' : 'rgba(255, 255, 255, 0.8)',
                borderColor: isActive ? 'rgba(157, 52, 218, 0.5)' : 'transparent',
                boxShadow: isActive ? '0 4px 20px rgba(157, 52, 218, 0.3)' : 'none'
              }}
              title={isCollapsed ? item.name : undefined}
            >
              <item.icon 
                className={`h-5 w-5 transition-colors ${
                  isActive ? "" : "group-hover:opacity-100"
                } ${isCollapsed ? 'flex-shrink-0' : ''}`}
                style={{
                  color: isActive ? '#bd73e8' : 'rgba(157, 52, 218, 0.6)'
                }}
              />
              {!isCollapsed && (
                <span className="font-medium titillium-web-semibold">{item.name}</span>
              )}
            </Link>
          )
        })}
      </nav>

      {/* Decorative gradient */}
      <div 
        className="absolute bottom-0 left-0 right-0 h-32 pointer-events-none"
        style={{
          background: 'linear-gradient(to top, rgba(157, 52, 218, 0.2) 0%, transparent 100%)'
        }}
      />
    </div>
  )

  // Mobile sidebar component
  const MobileSidebar = () => (
    <div className="w-64 glass-sidebar min-h-screen p-6 relative overflow-hidden">
      {/* Header */}
      <div className="mb-8 relative">
        <div className="flex items-center justify-between mb-1">
          <Logo size="sm" showText={true} className="flex-1" />
          <button
            onClick={() => setIsMobileMenuOpen(false)}
            className="p-2 rounded-lg glass-button hover:scale-105 transition-all duration-200 flex-shrink-0 ml-2"
            aria-label="Close menu"
          >
            <X className="h-4 w-4" style={{ color: '#9d34da' }} />
          </button>
        </div>
        <div className="flex items-center gap-2 ml-1">
          <div className="w-1 h-1 rounded-full bg-purple-400/60"></div>
          <p className="text-xs text-white/60 titillium-web-light tracking-wide uppercase">Web Interface</p>
        </div>
      </div>

      {/* Navigation */}
      <nav className="space-y-2">
        {navigation.map((item) => {
          const isActive = pathname === item.href
          return (
            <Link
              key={item.name}
              href={item.href}
              className={`flex items-center gap-3 px-4 py-3 rounded-lg transition-all duration-300 group ${
                isActive
                  ? "border shadow-lg"
                  : "hover:bg-white/10 hover:border hover:border-white/20"
              }`}
              style={{
                backgroundColor: isActive ? 'rgba(157, 52, 218, 0.3)' : 'transparent',
                color: isActive ? '#ffffff' : 'rgba(255, 255, 255, 0.8)',
                borderColor: isActive ? 'rgba(157, 52, 218, 0.5)' : 'transparent',
                boxShadow: isActive ? '0 4px 20px rgba(157, 52, 218, 0.3)' : 'none'
              }}
            >
              <item.icon 
                className="h-5 w-5 transition-colors group-hover:opacity-100"
                style={{
                  color: isActive ? '#bd73e8' : 'rgba(157, 52, 218, 0.6)'
                }}
              />
              <span className="font-medium titillium-web-semibold">{item.name}</span>
            </Link>
          )
        })}
      </nav>

      {/* Decorative gradient */}
      <div 
        className="absolute bottom-0 left-0 right-0 h-32 pointer-events-none"
        style={{
          background: 'linear-gradient(to top, rgba(157, 52, 218, 0.2) 0%, transparent 100%)'
        }}
      />
    </div>
  )

  if (isMobile) {
    return (
      <>
        {/* Mobile hamburger button */}
        <button
          onClick={() => setIsMobileMenuOpen(true)}
          className="fixed top-4 left-4 z-50 p-3 rounded-lg glass-button hover:scale-105 transition-all duration-200 md:hidden"
          aria-label="Open menu"
        >
          <Menu className="h-5 w-5" style={{ color: '#9d34da' }} />
        </button>

        {/* Mobile overlay */}
        {isMobileMenuOpen && (
          <>
            {/* Backdrop */}
            <div 
              className="fixed inset-0 bg-black/50 z-40 md:hidden"
              onClick={() => setIsMobileMenuOpen(false)}
            />
            
            {/* Mobile sidebar */}
            <div className="fixed top-0 left-0 z-50 h-full transform transition-transform duration-300 md:hidden">
              <MobileSidebar />
            </div>
          </>
        )}
      </>
    )
  }

  // Desktop version
  return <DesktopSidebar />
} 
