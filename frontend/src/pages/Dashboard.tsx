import { useState, useMemo, useEffect } from 'react'
import { usePrivacyScan } from '../hooks/usePrivacyScan'
import { Logo } from '../components/Logo'
import { PrivacyReportView } from '../components/PrivacyReport'
import { getConfigStatus } from '../services/api'

function detectType(query: string): { type: string; icon: string; label: string } | null {
  const q = query.trim()
  if (!q.length) return null
  if (/^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$/.test(q))
    return { type: 'email', icon: '@', label: 'Email' }
  if (/^\+?[\d\s\-().]{7,20}$/.test(q))
    return { type: 'phone', icon: '\u260E', label: 'Phone' }
  if (/^@?[\w.-]{3,30}$/.test(q) && !q.includes(' '))
    return { type: 'username', icon: '~', label: 'Username' }
  return { type: 'name', icon: 'A', label: 'Name' }
}

const examples = ['user@example.com', 'my_username', 'Full Name']

export function Dashboard() {
  const [query, setQuery] = useState('')
  const [focused, setFocused] = useState(false)
  const [license, setLicense] = useState<string | null>(null)
  const { loading, report, error, scan } = usePrivacyScan()

  useEffect(() => {
    getConfigStatus().then(s => {
      if (s.license.activated && s.license.valid) {
        setLicense(s.license.plan.toUpperCase())
      } else {
        setLicense(null)
      }
    }).catch(() => setLicense(null))
  }, [])

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    const sanitized = query.trim().slice(0, 200).replace(/[<>{}()\[\];&|`$]/g, '')
    if (!sanitized || sanitized.length < 2) return
    await scan(sanitized)
  }

  const detected = useMemo(() => detectType(query), [query])

  return (
    <div className="space-y-6 sm:space-y-10">
      <section className="relative pt-6 sm:pt-14 pb-6 sm:pb-10 text-center overflow-hidden animate-fade-in">
        <div className="absolute inset-0 bg-hero-glow pointer-events-none" />
        <div className="relative z-10">
          <div className="flex justify-center mb-4 sm:mb-6">
            <div className="relative">
              <Logo size={64} />
              <div className="absolute -inset-4 bg-primary-500/5 rounded-full blur-3xl animate-pulse hidden sm:block" />
            </div>
          </div>

          <h1 className="text-3xl sm:text-4xl md:text-5xl font-bold font-heading gradient-text mb-3 sm:mb-4 tracking-tight text-balance px-2">
            SPIA Privacy Audit
          </h1>
          <p className="text-gray-400 text-sm sm:text-lg max-w-lg mx-auto font-heading font-light leading-relaxed px-4 text-pretty">
            Discover where your personal information is exposed.
            Audit emails, usernames and names across the web, dark web and leaked databases.
          </p>

          <div className="flex items-center justify-center gap-2 sm:gap-3 mt-4 sm:mt-6 flex-wrap">
            {[
              { color: 'bg-success-400', shadow: 'shadow-[0_0_4px_#10b981]', label: 'Surface Web' },
              { color: 'bg-warning-400', shadow: 'shadow-[0_0_4px_#f59e0b]', label: 'Deep Web' },
              { color: 'bg-danger-400', shadow: 'shadow-[0_0_4px_#ef4444]', label: 'Dark Web' },
            ].map((w, i) => (
              <span key={i} className="text-[10px] sm:text-xs font-mono text-gray-600 flex items-center gap-1.5">
                <span className={`w-1.5 h-1.5 rounded-full ${w.color} ${w.shadow}`} />
                {w.label}
              </span>
            ))}
          </div>
        </div>
      </section>

      {license ? (
        <div className="max-w-2xl mx-auto px-4 animate-fade-in">
          <div className="flex items-center justify-center gap-2 text-[10px] font-mono text-success-400/70
                          bg-success-400/[0.03] border border-success-400/10 rounded-lg py-1.5 px-3">
            <span className="w-1.5 h-1.5 rounded-full bg-success-400" />
            {license} license active
          </div>
        </div>
      ) : (
        <div className="max-w-2xl mx-auto px-4 animate-fade-in">
          <div className="flex items-center justify-center gap-2 text-[10px] font-mono text-warning-400/70
                          bg-warning-400/[0.03] border border-warning-400/10 rounded-lg py-1.5 px-3">
            <span className="w-1.5 h-1.5 rounded-full bg-warning-400" />
            Trial mode — <button onClick={() => window.location.hash = 'pricing'} className="underline hover:text-warning-300">upgrade</button> for full features
          </div>
        </div>
      )}

      <section className="max-w-2xl mx-auto animate-slide-up px-4" style={{ marginTop: license !== null ? '12px' : '12px' }}>
        <form onSubmit={handleSubmit}>
          {/* ---- search bar ---- */}
          <div className={`
            relative group rounded-2xl p-[1px] transition-all duration-500
            ${focused
              ? 'bg-gradient-to-r from-primary-500/40 via-accent-400/30 to-primary-500/40 shadow-glow-md'
              : 'bg-white/[0.04] shadow-none'}
          `}>
            <div className="relative flex items-center bg-base-900 rounded-2xl overflow-hidden">
              {/* left icon */}
              <div className="pl-4 sm:pl-5 flex-shrink-0">
                <svg
                  width="18" height="18" viewBox="0 0 24 24" fill="none"
                  stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"
                  className="text-gray-500 transition-colors duration-300 group-hover:text-primary-400"
                >
                  <circle cx="11" cy="11" r="8" />
                  <line x1="21" y1="21" x2="16.65" y2="16.65" />
                </svg>
              </div>

              {/* input */}
              <input
                type="text"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                onFocus={() => setFocused(true)}
                onBlur={() => setFocused(false)}
                placeholder="Email, username, phone or full name..."
                className="flex-1 bg-transparent border-none outline-none text-sm sm:text-base font-mono
                           text-gray-200 placeholder-gray-600 py-4 sm:py-5 px-3 sm:px-4
                           min-w-0"
                disabled={loading}
                autoFocus
                autoComplete="off"
                spellCheck={false}
                aria-label="Privacy search query"
              />

              {/* right side: detection chip + button */}
              <div className="flex items-center gap-2 pr-2 sm:pr-3 flex-shrink-0">
                {detected && (
                  <span className="hidden sm:inline-flex items-center gap-1 px-2.5 py-1 rounded-full
                                   bg-white/[0.03] border border-white/[0.06] text-[11px] font-mono
                                   text-gray-400 animate-scale-in">
                    <span className="text-primary-400 font-bold">{detected.icon}</span>
                    {detected.label}
                  </span>
                )}

                <button
                  type="submit"
                  disabled={loading || query.trim().length < 2}
                  className="relative flex items-center justify-center gap-2 px-4 sm:px-5 py-2.5 sm:py-3
                             rounded-xl font-heading font-semibold text-xs sm:text-sm
                             transition-all duration-300 disabled:opacity-30 disabled:cursor-not-allowed
                             bg-white text-base-950
                             hover:bg-gray-100
                             active:scale-[0.97] overflow-hidden group/btn"
                >
                  {loading ? (
                    <span className="flex items-center gap-2 relative z-10">
                      <span className="w-3.5 h-3.5 border-2 border-base-950/20 border-t-base-950 rounded-full animate-spin" />
                      <span className="hidden sm:inline">Scanning</span>
                    </span>
                  ) : (
                    <span className="flex items-center gap-2 relative z-10">
                      <svg width="14" height="14" viewBox="0 0 24 24" fill="none"
                           stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                        <circle cx="11" cy="11" r="8" />
                        <line x1="21" y1="21" x2="16.65" y2="16.65" />
                      </svg>
                      <span>Scan</span>
                    </span>
                  )}
                </button>
              </div>
            </div>
          </div>

          {/* ---- detection chip mobile ---- */}
          <div className="flex justify-center mt-3 sm:hidden">
            {detected && (
              <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full
                               bg-white/[0.03] border border-white/[0.06] text-[11px] font-mono
                               text-gray-400 animate-scale-in">
                <span className="text-primary-400 font-bold">{detected.icon}</span>
                Detected: {detected.label}
              </span>
            )}
          </div>

          {/* ---- examples + hint ---- */}
          <div className="flex items-center justify-center gap-2 mt-3 sm:mt-4 flex-wrap">
            {examples.map((ex) => (
              <button
                key={ex}
                type="button"
                onClick={() => setQuery(ex)}
                className="px-3 py-1.5 rounded-lg text-[11px] sm:text-xs font-mono
                           bg-white/[0.02] border border-white/[0.04] text-gray-500
                           hover:text-gray-300 hover:border-white/[0.1] hover:bg-white/[0.04]
                           transition-all duration-200"
              >
                {ex}
              </button>
            ))}
            <span className="hidden sm:inline text-[10px] text-gray-700 font-mono mx-1">&middot;</span>
            <span className="hidden sm:inline text-[10px] text-gray-600 font-mono">
              60+ sources &middot; ~8s
            </span>
          </div>
        </form>
      </section>

      {error && (
        <section className="max-w-xl mx-auto animate-scale-in px-4" role="alert">
          <div className="glass-card border-danger-500/20 bg-danger-500/[0.03]">
            <div className="flex items-start gap-3">
              <span className="text-danger-400 text-lg mt-0.5 flex-shrink-0">&#x26A0;</span>
              <div className="min-w-0">
                <h3 className="text-sm font-heading font-semibold text-danger-400 mb-1">Scan error</h3>
                <p className="text-xs sm:text-sm text-danger-300/70 leading-relaxed break-words">{error}</p>
              </div>
            </div>
          </div>
        </section>
      )}

      {report && (
        <section className="max-w-5xl mx-auto animate-slide-up px-4">
          <PrivacyReportView report={report} />
        </section>
      )}

      {!report && !loading && (
        <>
          <section className="max-w-3xl mx-auto animate-slide-up px-4">
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 sm:gap-4 mt-6 sm:mt-8">
              {[
                { icon: '\uD83D\uDD0D', title: 'Deep Search', desc: 'Scans surface web, deep web and dark web across 60+ data sources.' },
                { icon: '\uD83D\uDEE1\uFE0F', title: 'Breaches & Leaks', desc: 'Checks Have I Been Pwned, Dehashed, paste sites and leak forums.' },
                { icon: '\uD83D\uDCCA', title: 'Score & Recommendations', desc: 'Privacy score 0-100 with a personalized action plan.' },
              ].map((f, i) => (
                <div key={i} className="glass-card group cursor-default animate-slide-up" style={{ animationDelay: `${i * 0.1}s` }}>
                  <div className="text-xl sm:text-2xl mb-2 sm:mb-3 group-hover:scale-110 transition-transform duration-300 inline-block">
                    {f.icon}
                  </div>
                  <h3 className="text-xs sm:text-sm font-heading font-semibold text-gray-200 mb-1 sm:mb-1.5">
                    {f.title}
                  </h3>
                  <p className="text-[11px] sm:text-xs text-gray-500 leading-relaxed">{f.desc}</p>
                </div>
              ))}
            </div>
          </section>

          <section className="max-w-xl mx-auto mt-8 sm:mt-10 text-center animate-slide-up px-4" style={{ animationDelay: '0.3s' }}>
            <div className="divider mb-4 sm:mb-6" />
            <p className="text-[11px] sm:text-xs text-gray-600 font-mono leading-relaxed max-w-md mx-auto">
              SPIA does not store your data. Searches are performed in real time
              against public APIs and search engines. Your queries are not saved
              or shared with third parties.
            </p>
          </section>
        </>
      )}
    </div>
  )
}
