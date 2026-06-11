import { useState, useEffect } from 'react'
import { Logo } from './components/Logo'
import { Dashboard } from './pages/Dashboard'
import { SettingsPage } from './pages/Settings'
import { PricingPage } from './pages/Pricing'
import { TermsPage, PrivacyPage } from './pages/Legal'

type Page = 'audit' | 'settings' | 'pricing' | 'terms' | 'privacy'

function App() {
  const [scrolled, setScrolled] = useState(false)
  const [page, setPage] = useState<Page>('audit')

  useEffect(() => {
    const onScroll = () => setScrolled(window.scrollY > 16)
    window.addEventListener('scroll', onScroll, { passive: true })
    return () => window.removeEventListener('scroll', onScroll)
  }, [])

  return (
    <div className="min-h-screen bg-[#06060e] dot-bg">
      <a
        href="#main-content"
        className="sr-only focus:not-sr-only focus:fixed focus:top-3 focus:left-3 focus:z-[100] focus:px-4 focus:py-2 focus:bg-primary-500 focus:text-white focus:rounded-lg focus:text-sm"
      >
        Skip to main content
      </a>

      <header
        className={`sticky top-0 z-50 transition-all duration-500 ${
          scrolled
            ? 'glass border-b border-white/5 shadow-lg shadow-primary-950/5'
            : 'bg-transparent'
        }`}
      >
        <div className="max-w-6xl mx-auto px-4 sm:px-6 py-3">
          <div className="flex items-center justify-between">
            <a href="/" className="flex items-center gap-2.5 sm:gap-3 group flex-shrink-0" aria-label="SPIA - Home page">
              <div className="relative">
                <Logo size={32} aria-hidden={true} />
                <div className="absolute -inset-1 bg-primary-500/10 rounded-full blur-md group-hover:bg-primary-500/20 transition-colors hidden sm:block" />
              </div>
              <div className="flex flex-col">
                <span className="text-base sm:text-lg font-bold font-heading gradient-text tracking-tight leading-none">
                  SPIA
                </span>
                <span className="text-[9px] sm:text-[10px] text-gray-500 font-mono tracking-[0.15em] uppercase leading-none mt-0.5">
                  Privacy Audit
                </span>
              </div>
            </a>
            <nav className="flex items-center gap-1 sm:gap-2" aria-label="Main navigation">
              {([
                ['audit', 'Audit'],
                ['pricing', 'Pricing'],
                ['settings', 'Settings'],
              ] as [Page, string][]).map(([p, label]) => (
                <button
                  key={p}
                  onClick={() => setPage(p)}
                  className={`text-[11px] sm:text-xs font-mono transition-colors px-2 sm:px-3 py-1.5 rounded-lg
                    ${page === p ? 'text-primary-300 bg-white/5' : 'text-gray-500 hover:text-gray-300 hover:bg-white/5'}`}
                >
                  {label}
                </button>
              ))}
              <span className="hidden sm:inline-flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg
                               bg-primary-500/5 border border-primary-500/10">
                <span className="w-1.5 h-1.5 rounded-full bg-success-400 shadow-[0_0_6px_#10b981]" />
                <span className="text-[10px] font-mono text-primary-400/80">v0.4</span>
              </span>
            </nav>
          </div>
        </div>
      </header>

      <main id="main-content" className="max-w-6xl mx-auto px-4 sm:px-6 py-6 sm:py-8">
        {page === 'audit' && <Dashboard />}
        {page === 'settings' && <SettingsPage />}
        {page === 'pricing' && <PricingPage />}
        {page === 'terms' && <TermsPage />}
        {page === 'privacy' && <PrivacyPage />}
      </main>

      <footer className="border-t border-white/5 mt-12 sm:mt-16" role="contentinfo">
        <div className="max-w-6xl mx-auto px-4 sm:px-6 py-5 sm:py-6">
          <div className="flex flex-col sm:flex-row items-center justify-between gap-3 text-[11px] sm:text-xs text-gray-600">
            <div className="flex items-center gap-2">
              <Logo size={14} animated={false} />
              <span className="font-mono">SPIA v0.4</span>
            </div>
            <span className="font-mono text-center">
              Public data audit &middot; 60+ sources &middot; HIBP &middot; Dark Web
            </span>
            <span className="font-mono flex items-center gap-4">
              <button onClick={() => setPage('terms')} className="hover:text-gray-400 transition-colors">Terms</button>
              <button onClick={() => setPage('privacy')} className="hover:text-gray-400 transition-colors">Privacy</button>
            </span>
          </div>
        </div>
      </footer>
    </div>
  )
}

export default App
