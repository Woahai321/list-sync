import { Sidebar } from "@/components/layout/sidebar"

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <div className="flex h-screen relative overflow-hidden floating-orbs" style={{ backgroundColor: '#000000' }}>
      {/* Sidebar - hidden on mobile, normal flow on desktop */}
      <div className="hidden md:block">
        <Sidebar />
      </div>
      
      {/* Mobile hamburger menu - only shows on mobile */}
      <div className="md:hidden">
        <Sidebar />
      </div>
      
      <main className="flex-1 overflow-auto custom-scrollbar transition-all duration-300 min-w-0">
        <div className="p-6 relative max-w-full md:p-6 pt-16 md:pt-6">
          {children}
        </div>
      </main>
    </div>
  )
} 
