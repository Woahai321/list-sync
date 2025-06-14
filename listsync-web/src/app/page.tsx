import { Logo } from "@/components/ui/logo"
import { ArrowRight, Zap, Link, Shield, Clock } from "lucide-react"

export default function HomePage() {
  return (
    <div className="min-h-screen flex items-center justify-center relative overflow-hidden floating-orbs" style={{ backgroundColor: '#000000' }}>
      {/* Background Effects */}
      <div className="absolute inset-0 bg-gradient-to-br from-purple-900/20 via-transparent to-purple-800/20"></div>
      
      <div className="max-w-xl w-full glass-card p-6 text-center relative mx-4">
        {/* Logo Section */}
        <div className="mb-6">
          <Logo size="lg" showText={true} className="justify-center mb-4" />
          <p className="text-lg text-white/80 titillium-web-light leading-relaxed">
            Web Interface for Media Synchronization
          </p>
          <p className="text-xs text-white/60 mt-2 titillium-web-regular">
            Connect your watchlists to your media server seamlessly
          </p>
        </div>
        
        {/* Main CTA */}
        <div className="mb-6">
          <a 
            href="/dashboard" 
            className="inline-flex items-center gap-2 glass-button-primary py-3 px-6 rounded-xl font-semibold transition-all duration-300 hover:scale-105 hover:shadow-2xl hover:shadow-purple-500/25 titillium-web-semibold text-base group"
          >
            Go to Dashboard
            <ArrowRight className="h-4 w-4 group-hover:translate-x-1 transition-transform" />
          </a>
        </div>
        
        {/* Feature Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-3 mb-6">
          <div className="glass-card p-4 text-left hover:bg-white/10 transition-all duration-300 group">
            <div className="flex items-start gap-3">
              <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-purple-500 to-purple-600 flex items-center justify-center group-hover:scale-110 transition-transform">
                <Link className="h-4 w-4 text-white" />
              </div>
              <div className="flex-1">
                <h3 className="text-sm font-semibold text-white mb-1 titillium-web-semibold">Multi-Platform</h3>
                <p className="text-xs text-white/70 titillium-web-regular">
                  Connect IMDb, Trakt, Letterboxd, and more platforms in one place
                </p>
              </div>
            </div>
          </div>
          
          <div className="glass-card p-4 text-left hover:bg-white/10 transition-all duration-300 group">
            <div className="flex items-start gap-3">
              <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-purple-500 to-purple-600 flex items-center justify-center group-hover:scale-110 transition-transform">
                <Zap className="h-4 w-4 text-white" />
              </div>
              <div className="flex-1">
                <h3 className="text-sm font-semibold text-white mb-1 titillium-web-semibold">Auto Sync</h3>
                <p className="text-xs text-white/70 titillium-web-regular">
                  Automated media requests and intelligent synchronization
                </p>
              </div>
            </div>
          </div>
          
          <div className="glass-card p-4 text-left hover:bg-white/10 transition-all duration-300 group">
            <div className="flex items-start gap-3">
              <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-purple-500 to-purple-600 flex items-center justify-center group-hover:scale-110 transition-transform">
                <Clock className="h-4 w-4 text-white" />
              </div>
              <div className="flex-1">
                <h3 className="text-sm font-semibold text-white mb-1 titillium-web-semibold">Real-time</h3>
                <p className="text-xs text-white/70 titillium-web-regular">
                  Live monitoring and instant updates across all services
                </p>
              </div>
            </div>
          </div>
          
          <div className="glass-card p-4 text-left hover:bg-white/10 transition-all duration-300 group">
            <div className="flex items-start gap-3">
              <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-purple-500 to-purple-600 flex items-center justify-center group-hover:scale-110 transition-transform">
                <Shield className="h-4 w-4 text-white" />
              </div>
              <div className="flex-1">
                <h3 className="text-sm font-semibold text-white mb-1 titillium-web-semibold">Secure</h3>
                <p className="text-xs text-white/70 titillium-web-regular">
                  Safe and secure integration with your media infrastructure
                </p>
              </div>
            </div>
          </div>
        </div>
        
        {/* Footer */}
        <div className="text-center">
          <p className="text-xs text-white/50 titillium-web-light">
            Streamline your media collection management
          </p>
        </div>
      </div>
    </div>
  )
}
